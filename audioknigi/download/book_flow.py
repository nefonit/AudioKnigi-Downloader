from __future__ import annotations

import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from ..models import normalize_track_status, TRACK_STATUS_MISSING, TRACK_STATUS_PRESENT, TRACK_STATUS_READY, TRACK_STATUS_DAMAGED
from ..logging_utils import app_logger
from ..i18n import tr as i18n_tr
from ..sources import source_key
from ..core import Cancelled, fmt_size, fmt_time, resolve_executable, effective_track_duration, safe_normalization_mode
from .errors import MissingMediaSourceError, MissingSelectedTracksError, SharedSourceTimelineError
from .common import unlink_with_retry

class BookFlowMixin:
    """Book Flow subsystem for the downloader facade."""

    @staticmethod
    def _is_expired_media_error(exc):
        """Return True when a download failed because the media URL disappeared.

        Player/CDN links can be short-lived even while the public book page still
        exists.  Walk the exception chain because requests.HTTPError is often
        wrapped by the resumable/Range download helpers.
        """
        current = exc
        seen = set()
        while current is not None and id(current) not in seen:
            seen.add(id(current))
            response = getattr(current, "response", None)
            if getattr(response, "status_code", None) in (404, 410):
                return True
            text = str(current or "").casefold()
            if (
                "404 client error" in text
                or "410 client error" in text
                or "http 404" in text
                or "http 410" in text
            ):
                return True
            current = getattr(current, "__cause__", None) or getattr(current, "__context__", None)
        return False

    def _source_target_assignments(self, book, source_urls, folder):
        """Return stable temporary source paths for a subset of book URLs.

        Slots are derived from the complete book playlist, so a retry of parts
        2/3/5 keeps using _source_02/_source_03/_source_05 instead of renumbering
        the subset to _source_01/_source_02/_source_03.
        """
        all_unique_files = []
        seen = set()
        for track in list(getattr(book, "tracks", []) or []):
            url = str(getattr(track, "file", "") or "")
            if url and url not in seen:
                seen.add(url)
                all_unique_files.append(url)

        slot_by_url = {url: pos for pos, url in enumerate(all_unique_files, 1)}
        total_slots = len(all_unique_files)
        assignments = []
        for subset_index, raw_url in enumerate(list(source_urls or []), 1):
            url = str(raw_url or "")
            slot = slot_by_url.get(url, subset_index)
            name = "_source.mp3" if total_slots <= 1 else f"_source_{slot:02d}.mp3"
            assignments.append((slot, url, Path(folder) / name))
        return assignments

    def _clear_stale_source_downloads(self, book) -> int:
        folder = self._book_folder(book, create=False)
        if not folder.exists():
            return 0

        # Only remove engine-owned source/repair artifacts.  The previous
        # ``_source*.mp3*`` glob could also match a legitimate user file such
        # as ``_source of wisdom.mp3``.
        owned = re.compile(
            r"^(?:_source(?:_\d+)?|_repair_source(?:_\d+)?)\.mp3"
            r"(?:$|\.part(?:$|\.assembling$|\.segments\.json$|\.seg\d+$))"
        )
        removed = 0
        try:
            candidates = list(folder.iterdir())
        except OSError:
            candidates = []
        for candidate in candidates:
            if not candidate.is_file() or not owned.fullmatch(candidate.name):
                continue
            try:
                candidate.unlink(missing_ok=True)
                removed += 1
            except OSError:
                pass
        if removed:
            self.log(f"Удалены временные файлы устаревшего источника: {removed}.")
        return removed

    def _refresh_book_media_playlist(self, book, selected_indices):
        """Re-analyze the public book page and replace expiring media URLs in-place."""
        self._check_cancel()
        self.set_status("Аудиоссылка устарела — обновляю плейлист…")
        self.set_stage(2, i18n_tr(getattr(self, "runtime_language", "ru"), "stage_playlist_refresh"))
        self.log("Аудиоссылка вернула HTTP 404/410. Обновляю страницу и плейлист…")

        fresh = self._analyze_book(book.url)
        if getattr(fresh, "restricted", False):
            raise RuntimeError("После обновления плейлиста эта озвучка стала недоступна.")

        fresh_by_index = {int(tr.index): tr for tr in fresh.tracks}
        wanted = {int(x) for x in (selected_indices or [])}
        missing = sorted(wanted.difference(fresh_by_index))

        old_by_index = {int(tr.index): tr for tr in book.tracks}
        changed_urls = 0
        for tr in fresh.tracks:
            previous = old_by_index.get(int(tr.index))
            if previous is None:
                continue
            if str(previous.file or "") != str(tr.file or ""):
                changed_urls += 1
            # Preserve local/UI state while taking fresh network/timing metadata.
            tr.selected = bool(previous.selected)
            tr.local_status = normalize_track_status(previous.local_status)
            tr.actual_duration = previous.actual_duration
            tr.local_path = str(previous.local_path or "")

        for attr in (
            "title", "author", "narrator", "description", "genre", "year",
            "cover_url", "playlist_url", "narration_variants", "restricted",
            "remote_size", "cover_cache",
        ):
            try:
                setattr(book, attr, getattr(fresh, attr))
            except Exception:
                pass
        book.tracks = list(fresh.tracks)

        self._clear_stale_source_downloads(book)
        if missing:
            self.log(
                "Плейлист обновлён, но в нём отсутствуют выбранные части: "
                + ", ".join(str(x) for x in missing)
                + ". Ожидаю решения пользователя."
            )
            raise MissingSelectedTracksError(missing)
        self.log(
            "Плейлист обновлён: "
            f"частей {len(book.tracks)}, изменённых аудиоссылок {changed_urls}. "
            "Повторяю загрузку один раз."
        )
        return changed_urls

    def _ask_missing_media_action(self, track_indices, *, detail="", allow_skip=True):
        """GUI-neutral fallback for an unavailable media decision.

        Interactive frontends override this hook.  Non-interactive callers stop
        safely instead of guessing that missing chapters may be skipped.
        """
        indices = sorted({int(x) for x in (track_indices or [])})
        if indices:
            self.log(
                "Недоступны части: "
                + ", ".join(str(x) for x in indices)
                + ". Интерактивное решение не предоставлено; загрузка остановлена."
            )
        return "stop"

    @staticmethod
    def _expired_media_track_indices(exc, book, active_selected) -> list[int]:
        explicit = []
        for value in list(getattr(exc, "track_indices", []) or []):
            try:
                explicit.append(int(value))
            except (TypeError, ValueError):
                continue
        if explicit:
            return sorted(set(explicit))

        urls: set[str] = set()
        current = exc
        seen: set[int] = set()
        while current is not None and id(current) not in seen:
            seen.add(id(current))
            for candidate in (
                getattr(current, "source_url", ""),
                getattr(getattr(current, "response", None), "url", ""),
                getattr(getattr(current, "request", None), "url", ""),
            ):
                value = str(candidate or "").strip()
                if value:
                    urls.add(value)
            current = getattr(current, "__cause__", None) or getattr(current, "__context__", None)

        active = {int(value) for value in (active_selected or [])}
        inferred: list[int] = []
        for track in list(getattr(book, "tracks", []) or []):
            try:
                index = int(track.index)
            except (TypeError, ValueError):
                continue
            if active and index not in active:
                continue
            candidates = {
                str(getattr(track, "file", "") or "").strip(),
                str(getattr(track, "fallback_file", "") or "").strip(),
            }
            if urls.intersection(value for value in candidates if value):
                inferred.append(index)
        if inferred:
            return sorted(set(inferred))
        if len(active) == 1:
            return sorted(active)
        return []

    def _record_skipped_media_parts(self, indices):
        skipped = sorted({int(x) for x in (indices or [])})
        existing = set(getattr(self, "_last_process_skipped_indices", []) or [])
        existing.update(skipped)
        self._last_process_skipped_indices = sorted(existing)
        if skipped:
            self.log(
                "Пользователь пропустил недоступные части: "
                + ", ".join(str(x) for x in skipped)
                + ". Остальные выбранные части продолжаю скачивать."
            )

    def _process_book(self, book, selected_indices=None, status_callback=None):
        """Process a book, refreshing short-lived media URLs once after HTTP 404/410."""
        values = list(getattr(book, "tracks", []) or []) if selected_indices is None else list(selected_indices)
        active_selected = set()
        for value in values:
            raw_index = getattr(value, "index", value)
            if isinstance(raw_index, bool):
                continue
            try:
                track_index = int(raw_index)
            except (TypeError, ValueError, OverflowError):
                continue
            if track_index >= 0:
                active_selected.add(track_index)
        self._last_process_skipped_indices = []
        refreshed_after_not_found = False
        fallback_attempted = False
        while True:
            try:
                return self._process_book_once(book, active_selected, status_callback)
            except Cancelled:
                raise
            except SharedSourceTimelineError as exc:
                issue = dict(getattr(exc, "issue", {}) or {})
                if source_key(getattr(book, "url", "")) != "audioknigi":
                    raise
                if fallback_attempted:
                    raise RuntimeError(
                        "Резервный источник уже использовался один раз, но ошибка общей "
                        "аудиодорожки повторилась. Повторное автоматическое переключение "
                        "источника остановлено, чтобы избежать цикла."
                    ) from exc
                self._log_book_flow(
                    "shared_source_local_validation_failed", book, level="warning",
                    expected_end=f"{float(issue.get('expected_end') or 0.0):.3f}",
                    actual_duration=f"{float(issue.get('actual_duration') or 0.0):.3f}",
                    reason=issue.get("reason", "unknown"),
                )
                self.log(
                    "Общий файл audioknigi.com.ua не содержит аудио возле последнего "
                    "таймкода. Ищу исправную копию этой же озвучки на knigavuhe.org."
                )
                # Never let a truncated shared source survive into a fallback run.
                # The fallback can legitimately resolve to the same output folder.
                self._clear_stale_source_downloads(book)
                fallback = self._knigavuhe_fallback_candidate(book)
                if fallback is None:
                    raise RuntimeError(
                        "Общий аудиофайл audioknigi.com.ua оказался неполным, а "
                        "автоматический резервный источник knigavuhe.org сейчас недоступен. "
                        "Повторите попытку позже или выберите эту книгу на другом источнике."
                    ) from exc
                original_indices = {int(tr.index) for tr in list(getattr(book, "tracks", []) or [])}
                selected_all_original = bool(original_indices) and active_selected == original_indices
                if not selected_all_original:
                    raise RuntimeError(
                        "Резервный источник найден, но выбранные части нельзя безопасно "
                        "сопоставить между audioknigi.com.ua и knigavuhe.org: разметка глав "
                        "на этих сайтах различается. Проанализируйте резервную версию книги "
                        "и выберите нужные части заново."
                    ) from exc
                fallback_attempted = True
                # The old audioknigi folder is no longer resumable after a
                # timeline-validation fallback to a different source layout.
                # Remove its manifest before switching request.book so recovery
                # does not later offer an orphaned stale task.
                self._remove_resume_manifest(book)
                self._populate_missing_track_durations(fallback)
                self.log(
                    "Найден исправный резервный источник knigavuhe.org. "
                    f"Переключаю загрузку автоматически: {fallback.title}."
                )
                self._log_book_flow(
                    "source_fallback_selected_after_local_validation", fallback,
                    original_source="audioknigi", fallback_source="knigavuhe",
                )
                book = fallback
                fallback_indices = {int(tr.index) for tr in list(getattr(book, "tracks", []) or [])}
                active_selected = fallback_indices
                req = getattr(self, "request", None)
                if req is not None:
                    req.book = book
                    req.selected_indices = sorted(active_selected)
                callback = getattr(getattr(self, "callbacks", None), "request_changed", None)
                if callback is not None and req is not None:
                    try:
                        callback(req)
                    except Exception:
                        app_logger.debug("Request-change callback failed", exc_info=True)
                refreshed_after_not_found = False
                continue
            except Exception as exc:
                if not self._is_expired_media_error(exc):
                    raise
                self._log_book_flow(
                    "media_url_expired", book, missing=self._expired_media_track_indices(exc, book, active_selected),
                    already_refreshed=refreshed_after_not_found,
                )
                if refreshed_after_not_found:
                    missing_indices = self._expired_media_track_indices(exc, book, active_selected)
                    if missing_indices:
                        available_after_skip = active_selected.difference(missing_indices)
                        action = self._ask_missing_media_action(
                            missing_indices,
                            detail="Свежая ссылка на этот аудиофайл также вернула HTTP 404/410.",
                            allow_skip=bool(available_after_skip),
                        )
                        if action == "skip" and available_after_skip:
                            active_selected = available_after_skip
                            self._record_skipped_media_parts(missing_indices)
                            # Keep already completed fresh source downloads. A broad
                            # _source*.mp3 cleanup here would force unaffected parts
                            # to download again after the user skips one missing part.
                            # The full cleanup belongs to playlist refresh, above.
                            # The page/playlist refresh budget is per book run,
                            # not per missing track.  Once a refresh has already
                            # happened, later 404/410 parts may be skipped but do
                            # not trigger another full page refresh.
                            continue
                    raise RuntimeError(
                        "Аудиофайл недоступен (HTTP 404/410) даже после обновления плейлиста. "
                        "Возможно, файл временно удалён на сервере или эта часть книги недоступна."
                    ) from exc
                try:
                    self._log_book_flow("playlist_refresh_start", book, selected=sorted(active_selected))
                    self._refresh_book_media_playlist(book, active_selected)
                    self._log_book_flow("playlist_refresh_complete", book, selected=sorted(active_selected))
                except Cancelled:
                    raise
                except MissingSelectedTracksError as refresh_exc:
                    missing_indices = refresh_exc.track_indices
                    available_after_skip = active_selected.difference(missing_indices)
                    action = self._ask_missing_media_action(
                        missing_indices,
                        detail="После обновления страницы этих частей больше нет в плейлисте.",
                        allow_skip=bool(available_after_skip),
                    )
                    if action == "skip" and available_after_skip:
                        active_selected = available_after_skip
                        self._record_skipped_media_parts(missing_indices)
                        refreshed_after_not_found = True
                        continue
                    raise RuntimeError(
                        "Загрузка остановлена: выбранная часть отсутствует в обновлённом плейлисте."
                    ) from refresh_exc
                except Exception as refresh_exc:
                    raise RuntimeError(
                        "Аудиоссылка устарела (HTTP 404/410), а получить свежий плейлист не удалось: "
                        f"{refresh_exc}"
                    ) from refresh_exc
                refreshed_after_not_found = True

    def _process_book_once(self, book, selected_indices=None, status_callback=None):
        self._check_cancel()
        if resolve_executable("ffmpeg") is None:
            raise RuntimeError("FFmpeg не найден.")

        tracks = book.tracks
        if selected_indices is None:
            selected_indices = [tr.index for tr in tracks]
        selected_indices = set(int(x) for x in selected_indices)
        chosen = []
        for tr in tracks:
            try:
                track_index = int(getattr(tr, "index", -1))
            except (TypeError, ValueError):
                continue
            if track_index in selected_indices:
                chosen.append(tr)
        if not chosen:
            raise RuntimeError("Не выбрано ни одной части.")

        output_mode = "mp3"
        want_mp3 = True

        self._scan_book_files(book, create_folder=False)
        if not self._check_disk_space(book, selected_indices, show_warning=False):
            required, free = self._disk_space_info(book, selected_indices)
            if free is None:
                raise RuntimeError(
                    "Не удалось определить свободное место на диске. "
                    "Проверьте папку сохранения и доступ к диску."
                )
            raise RuntimeError(
                "Недостаточно свободного места.\n"
                f"Нужно примерно: {fmt_size(required)}\nСвободно: {fmt_size(free)}"
            )

        self._write_resume_manifest(book, sorted(selected_indices))
        folder = self._book_folder(book)
        flow_started = time.monotonic()
        self._log_book_flow(
            "download_start", book,
            selected=sorted(selected_indices), output_mode=output_mode, folder=folder,
            audio_preset=str(getattr(self, "runtime_audio_preset", "copy") or "copy"),
            normalization=str(getattr(self, "runtime_normalization_mode", "off") or "off"),
            embed_tags=bool(getattr(self, "runtime_embed_tags", False)),
            sidecars=bool(getattr(self, "runtime_save_sidecars", True)),
            delete_source=bool(getattr(self, "runtime_delete_source", True)),
        )

        def report(status):
            if status_callback:
                try:
                    status_callback(status)
                except Exception:
                    pass

        mp3_needs_creation = []
        if want_mp3:
            mp3_needs_creation = [
                tr for tr in chosen if normalize_track_status(tr.local_status) not in (TRACK_STATUS_READY, TRACK_STATUS_PRESENT)
            ]
            for tr in mp3_needs_creation:
                if normalize_track_status(tr.local_status) == TRACK_STATUS_DAMAGED:
                    try:
                        bad = self._track_path(book, tr)
                        bad.unlink(missing_ok=True)
                        self.log(f"{bad.name}: повреждён, создаю заново.")
                    except Exception:
                        pass

        source_tracks = list(mp3_needs_creation)
        missing_source_indices = [
            int(getattr(tr, "index", 0) or 0)
            for tr in source_tracks
            if not str(getattr(tr, "file", "") or "").strip()
        ]
        if missing_source_indices:
            joined = ", ".join(str(index) for index in missing_source_indices if index > 0) or "?"
            raise RuntimeError(
                "В плейлисте отсутствует адрес аудиофайла для частей: "
                f"{joined}. Повторите анализ книги."
            )
        unique_files = []
        seen_files = set()
        fallback_by_file = {}
        for tr in source_tracks:
            source_url = str(getattr(tr, "file", "") or "").strip()
            if getattr(tr, "file", None) != source_url:
                tr.file = source_url
            if source_url not in seen_files:
                seen_files.add(source_url)
                unique_files.append(source_url)
            fallback = str(getattr(tr, "fallback_file", "") or "")
            if fallback and source_url not in fallback_by_file:
                fallback_by_file[source_url] = fallback

        self._log_book_flow(
            "download_plan", book, selected=len(chosen), existing_mp3=len(chosen) - len(mp3_needs_creation) if want_mp3 else 0,
            mp3_to_create=len(mp3_needs_creation), unique_sources=len(unique_files),
            want_mp3=True,
        )

        # Source filenames must be stable for the whole book, not relative to
        # the current subset being repaired/retried.
        local_map = {}
        download_jobs = []
        for file_index, url, target in self._source_target_assignments(book, unique_files, folder):
            local_map[url] = target
            affected_tracks = [int(tr.index) for tr in source_tracks if str(tr.file or "") == url]
            self._log_book_flow(
                "source_mapping", book, level="debug", source_index=file_index,
                file=target.name, tracks=affected_tracks,
            )
            if not target.exists() or target.stat().st_size == 0:
                download_jobs.append((file_index, url, fallback_by_file.get(url, ""), target))

        # Keep every disposable source path even if local_map is later replaced
        # by a freshly downloaded repair source.  Otherwise an old/broken
        # _source*.mp3 can fall out of local_map.values() and survive cleanup.
        cleanup_sources = set(local_map.values())
        original_source_paths = dict(local_map)
        repaired_sources: dict[str, Path] = {}

        if download_jobs:
            self._log_book_flow(
                "source_download_start", book, jobs=len(download_jobs), reused=len(unique_files) - len(download_jobs),
            )
            self.set_stage(2, i18n_tr(getattr(self, "runtime_language", "ru"), "stage_source_download"))
            report("Скачивается")
            if len(download_jobs) == 1:
                file_index, url, fallback_url, target = download_jobs[0]
                try:
                    self._download_source_with_fallback(url, fallback_url, target, book.url)
                except Cancelled:
                    raise
                except Exception as exc:
                    if self._is_expired_media_error(exc):
                        affected = [int(tr.index) for tr in source_tracks if tr.file == url]
                        raise MissingMediaSourceError(
                            str(exc), source_url=url, track_indices=affected
                        ) from exc
                    raise
                self._log_book_flow(
                    "source_download_complete", book, level="debug", source_index=file_index,
                    file=target.name, bytes=target.stat().st_size if target.exists() else 0,
                )
            else:
                max_workers = min(3, len(download_jobs))
                # Individual network workers report percentages for their own
                # source file.  Letting all of them write to one global progress
                # bar makes it jump backwards and forwards.  During parallel
                # source downloads, expose stable book-level progress by completed
                # source count instead.
                self._suppress_source_transfer_ui = True
                try:
                    with ThreadPoolExecutor(max_workers=max_workers) as pool:
                        futures = {
                            pool.submit(self._download_source_with_fallback, url, fallback_url, target, book.url): (file_index, url, target)
                            for file_index, url, fallback_url, target in download_jobs
                        }
                        for pos, future in enumerate(as_completed(futures), 1):
                            self._check_cancel()
                            file_index, url, target = futures[future]
                            try:
                                future.result()
                            except Cancelled:
                                for pending in futures:
                                    if pending is not future:
                                        pending.cancel()
                                self._cancel_active_network_io()
                                raise
                            except Exception as exc:
                                for pending in futures:
                                    if pending is not future:
                                        pending.cancel()
                                self._cancel_active_network_io()
                                if self._is_expired_media_error(exc):
                                    affected = [int(tr.index) for tr in source_tracks if tr.file == url]
                                    raise MissingMediaSourceError(
                                        str(exc), source_url=url, track_indices=affected
                                    ) from exc
                                raise
                            self._log_book_flow(
                                "source_download_complete", book, level="debug", source_index=file_index,
                                file=target.name, bytes=target.stat().st_size if target.exists() else 0,
                                progress=f"{pos}/{len(download_jobs)}",
                            )
                            self.set_progress(pos * 100 / max(1, len(download_jobs)))
                            report(f"Скачивается {pos}/{len(download_jobs)}")
                finally:
                    self._suppress_source_transfer_ui = False
            self._log_book_flow("source_downloads_complete", book, jobs=len(download_jobs))
        elif unique_files:
            self._log_book_flow("source_reused", book, sources=len(unique_files))

        # Once direct chapter sources are on disk, duration becomes reliable
        # even if remote ffprobe was blocked by the host.  Keep it in
        # actual_duration (display/runtime fallback) instead of inventing
        # source start/end trimming coordinates.
        source_counts = {}
        for tr in source_tracks:
            source_counts[tr.file] = source_counts.get(tr.file, 0) + 1
        measured_source_timing = False
        for tr in source_tracks:
            if effective_track_duration(tr) is not None or source_counts.get(tr.file, 0) != 1:
                continue
            source_path = local_map.get(tr.file)
            if source_path is None:
                continue
            actual = self._probe_duration(source_path)
            if actual is not None and actual > 0:
                tr.actual_duration = float(actual)
                measured_source_timing = True
        if measured_source_timing and hasattr(self, "ui") and hasattr(self, "_refresh_book_timing_ui"):
            self.ui(lambda b=book: self._refresh_book_timing_ui(b))

        if want_mp3 and mp3_needs_creation:
            local_timeline_issue = self._shared_source_timeline_issue(book, local_map=local_map)
            if local_timeline_issue:
                self._log_book_flow(
                    "local_shared_source_timeline_mismatch", book, level="error",
                    expected_end=f"{local_timeline_issue['expected_end']:.3f}",
                    actual_duration=f"{local_timeline_issue['actual_duration']:.3f}",
                )
                raise SharedSourceTimelineError(local_timeline_issue)

            self._log_book_flow("ffmpeg_split_start", book, parts=len(mp3_needs_creation))
            split_text = i18n_tr(getattr(self, "runtime_language", "ru"), "status_splitting_progress", current=0, total=len(mp3_needs_creation))
            self.set_stage(3, split_text)
            report(split_text)
            groups = {}
            for tr in mp3_needs_creation:
                groups.setdefault(tr.file, []).append(tr)
            completed = 0
            progress_lock = threading.Lock()

            def local_source_for(source_url):
                src = local_map.get(source_url)
                if src is None:
                    raise RuntimeError(
                        "Локальный исходник для нарезки не найден. "
                        "Повторите анализ или загрузку книги."
                    )
                return src

            def split_group(source_url, group_tracks):
                nonlocal completed
                src = local_source_for(source_url)
                for tr in group_tracks:
                    self._check_cancel()
                    self.set_status(f"Создаю {self._track_filename(book, tr)}")
                    self._log_book_flow("ffmpeg_track_start", book, level="debug", track=tr.index, file=self._track_filename(book, tr))
                    self._split_track(book, tr, src)
                    self._log_book_flow("ffmpeg_track_complete", book, level="debug", track=tr.index, file=self._track_filename(book, tr))
                    with progress_lock:
                        completed += 1
                        current = completed
                        split_text = i18n_tr(
                            getattr(self, "runtime_language", "ru"),
                            "status_splitting_progress",
                            current=current,
                            total=len(mp3_needs_creation),
                        )
                        self.set_stage(3, split_text)
                        self.set_progress(current * 100 / max(1, len(mp3_needs_creation)))
                        report(split_text)

            parallel_single_source = (
                len(groups) == 1
                and bool(getattr(self, "runtime_parallel_single_source", False))
                and safe_normalization_mode(getattr(self, "runtime_normalization_mode", "off"), "off") != "two_pass"
                and len(mp3_needs_creation) >= 4
            )
            if parallel_single_source:
                # Optional SSD-oriented mode: two FFmpeg readers against one source.
                # Two-pass loudnorm is deliberately serialized: each split first
                # performs a measurement pass, so parallelizing those reads can
                # saturate the same source and makes cancellation unnecessarily noisy.
                source_url, group_tracks = next(iter(groups.items()))
                src = local_source_for(source_url)
                self.log("Параллельная нарезка одного исходника: 2 FFmpeg-процесса (режим SSD).")
                def split_one(tr):
                    nonlocal completed
                    self._check_cancel()
                    self._log_book_flow("ffmpeg_track_start", book, level="debug", track=tr.index, file=self._track_filename(book, tr))
                    self._split_track(book, tr, src)
                    self._log_book_flow("ffmpeg_track_complete", book, level="debug", track=tr.index, file=self._track_filename(book, tr))
                    with progress_lock:
                        completed += 1
                        current = completed
                        split_text = i18n_tr(
                            getattr(self, "runtime_language", "ru"),
                            "status_splitting_progress",
                            current=current,
                            total=len(mp3_needs_creation),
                        )
                        self.set_stage(3, split_text)
                        self.set_progress(current * 100 / max(1, len(mp3_needs_creation)))
                        report(split_text)
                with ThreadPoolExecutor(max_workers=2) as pool:
                    futures = [pool.submit(split_one, tr) for tr in group_tracks]
                    try:
                        for future in as_completed(futures):
                            self._check_cancel()
                            future.result()
                    except Exception:
                        for pending in futures:
                            if not pending.done():
                                pending.cancel()
                        # ``ThreadPoolExecutor.__exit__`` waits for already-running
                        # workers. Stop their FFmpeg children first so one failed
                        # split cannot leave shutdown waiting for a long encode.
                        self._cancel_active_subprocesses()
                        raise
            elif len(groups) <= 1:
                for source_url, group_tracks in groups.items():
                    split_group(source_url, group_tracks)
            else:
                with ThreadPoolExecutor(max_workers=min(3, len(groups))) as pool:
                    futures = [pool.submit(split_group, url, group) for url, group in groups.items()]
                    try:
                        for future in as_completed(futures):
                            self._check_cancel()
                            future.result()
                    except Exception:
                        for pending in futures:
                            if not pending.done():
                                pending.cancel()
                        self._cancel_active_subprocesses()
                        raise

        if want_mp3 and mp3_needs_creation:
            self._log_book_flow("ffmpeg_split_complete", book, parts=len(mp3_needs_creation))

        if want_mp3:
            self._log_book_flow("verify_start", book, parts=len(chosen), embed_tags=bool(getattr(self, "runtime_embed_tags", False)))
            self.set_stage(4, i18n_tr(getattr(self, "runtime_language", "ru"), "status_checking_progress", current=0, total=len(chosen)))
            cover = self._cover_bytes(book)
            self._log_book_flow(
                "cover_state", book, available=bool(cover),
                bytes=len(cover[0]) if cover and isinstance(cover, tuple) and cover else 0,
            )
            tag_jobs = []
            for pos, tr in enumerate(chosen, 1):
                self._check_cancel()
                status, actual, out = self._verify_track_file(book, tr)
                if normalize_track_status(status) == TRACK_STATUS_DAMAGED:
                    # A damaged output can be caused by a damaged cached source.
                    # Do not trust/reuse the existing _source*.mp3 for repair:
                    # fetch a fresh disposable copy and remember BOTH paths for
                    # final cleanup when delete_source is enabled.
                    source_key_value = str(tr.file or "")
                    src = repaired_sources.get(source_key_value)
                    if src is None:
                        original_source = original_source_paths.get(source_key_value)
                        if original_source is not None:
                            source_stem = Path(original_source).stem.lstrip("_") or "source"
                            src = folder / f"_repair_{source_stem}.mp3"
                        else:
                            src = folder / f"_repair_source_{len(repaired_sources) + 1:02d}.mp3"
                        try:
                            src.unlink(missing_ok=True)
                        except Exception:
                            pass
                        try:
                            self._download_source_with_fallback(
                                tr.file, getattr(tr, "fallback_file", ""), src, book.url
                            )
                        except Cancelled:
                            raise
                        except Exception as exc:
                            if self._is_expired_media_error(exc):
                                raise MissingMediaSourceError(
                                    str(exc),
                                    source_url=tr.file,
                                    track_indices=[int(tr.index)],
                                ) from exc
                            raise
                        repaired_sources[source_key_value] = src
                        cleanup_sources.add(src)
                    local_map[source_key_value] = src
                    self._split_track(book, tr, src)
                    status, actual, out = self._verify_track_file(book, tr)
                if normalize_track_status(status) in (TRACK_STATUS_MISSING, TRACK_STATUS_DAMAGED):
                    raise RuntimeError(
                        f"Не удалось корректно создать {out.name}: "
                        f"ожидалось {fmt_time(effective_track_duration(tr))}, получено {fmt_time(actual)}."
                    )
                tr.local_status = normalize_track_status(status)
                tr.actual_duration = actual
                tr.local_path = str(out)
                if hasattr(self, "ui") and hasattr(self, "_refresh_book_timing_ui"):
                    self.ui(lambda b=book: self._refresh_book_timing_ui(b))
                tag_jobs.append((tr, out))
                self.set_stage(4, i18n_tr(getattr(self, "runtime_language", "ru"), "status_checking_progress", current=pos, total=len(chosen)))
                self._log_book_flow(
                    "track_verified", book, level="debug", track=tr.index, status=tr.local_status,
                    duration=f"{float(actual or 0):.3f}", file=out.name,
                )

            self._log_book_flow("verify_complete", book, parts=len(chosen))
            if bool(getattr(self, "runtime_embed_tags", False)) and tag_jobs:
                self._log_book_flow("id3_start", book, files=len(tag_jobs))
                with ThreadPoolExecutor(max_workers=min(4, len(tag_jobs))) as pool:
                    futures = [
                        pool.submit(self._write_id3, out, book, tr.index, len(tracks), cover, tr)
                        for tr, out in tag_jobs
                    ]
                    for future in as_completed(futures):
                        self._check_cancel()
                        future.result()
                self._log_book_flow("id3_complete", book, files=len(tag_jobs))
            elif tag_jobs:
                self._log_book_flow("id3_skipped", book, files=len(tag_jobs), reason="disabled")

        self._save_book_sidecars(book, folder, list(getattr(book, "tracks", None) or []))
        self._scan_audiobookshelf_after_book()

        if bool(getattr(self, "runtime_delete_source", True)):
            removed_sources = 0
            for path in cleanup_sources:
                try:
                    unlink_with_retry(path, missing_ok=False)
                    removed_sources += 1
                except FileNotFoundError:
                    # The source may already have been moved/removed by an earlier
                    # stage.  Treat that as an already-clean state rather than a
                    # cleanup failure, and do not inflate ``removed_sources``.
                    pass
                except Exception:
                    app_logger.debug("Source cleanup failed | path=%s", path, exc_info=True)
            self._log_book_flow("source_cleanup", book, removed=removed_sources, planned=len(cleanup_sources))

        self._remove_resume_manifest(book)
        self._scan_book_files(book)
        self._add_history(book, folder, len(chosen))
        self._log_book_flow(
            "download_complete", book, folder=folder, parts=len(chosen),
            skipped=list(getattr(self, "_last_process_skipped_indices", []) or []),
            elapsed=f"{time.monotonic() - flow_started:.3f}s",
        )
        done_text = i18n_tr(getattr(self, "runtime_language", "ru"), "status_done")
        self.set_stage(5, done_text)
        report(done_text)
        return folder

__all__ = ["BookFlowMixin"]
