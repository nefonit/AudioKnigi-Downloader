# Follow-up audit fixes — 2026-09-10

Base: `AudioKnigi_Downloader_v4_12_31_PHASE39_AUDIT_FIXED_20260910`.

## Fixed

- `downloader.py`: `_run_ffmpeg()` and `_run_ffmpeg_capture()` no longer dereference a missing/None `cancel_event` inside `TimeoutExpired` handling.
- `downloader.py`: HTTP 416 with a stale/oversized `.part` now discards the invalid partial and restarts once from byte zero. A complete partial reported through `Content-Range: bytes */N` is still promoted without re-downloading.
- `downloader.py`: repair downloads are cached by source URL. Multiple damaged chapters cut from one shared source reuse one fresh repair source instead of re-downloading the whole source for every chapter.
- `downloader.py`: `DownloaderMixin` now exposes safe default host hooks for cancellation, logging, progress, stages and transfer metrics. `_DownloadEngine` continues to override them.
- `download_engine.py`: `delete_existing_outputs()` deletes only tracks present in `request.selected_indices`.
- `download_engine.py`: Full MP3 mode distinguishes zero source files from multiple source files and now reports stage 3 (processing) between download and ID3 work.
- `logging_utils.py`: default `log_exception()` resolves `sys.exc_info()` before testing for `RecursionError`, avoiding traceback formatting at the recursion limit.
- `knigavuhe.py`: authorless same-title results are no longer all collapsed under an empty author key. Authorless variants can join only when there is exactly one known author for that title.
- `network_dns.py`: peer reset/broken pipe/OSError during tunnel `recv()` is treated as normal tunnel termination instead of a proxy 502 path.
- `poleknig.py`: detail-page metadata preserves all author links; pagination query comparison ignores harmless leading/trailing whitespace.
- `player_controller.py`: periodic position persistence explicitly stops at EndOfMedia in addition to the existing store-level end-of-track protection.
- `player_mixin.py`: `_selected_track()` tolerates a temporarily missing selection model.
- `onboarding.py`: start/cancel button accessible descriptions no longer duplicate their accessible names.
- temporary table context menus use `WA_DeleteOnClose` through `qt/menu_utils.py`.
- Full-MP3 stage/error strings added to runtime localization; `_download_stage()` localizes the stage body as well as the `Этап` prefix.

## Main window decomposition

`audioknigi/qt/main_window.py` was reduced from 4598 lines / about 249 KB to 3991 lines / about 206 KB.

Extracted responsibilities:

- `qt/main_window_pages.py`: large Book and Settings page builders.
- `qt/settings_sync.py`: persisted-settings-to-widget synchronization.
- `qt/menu_utils.py`: lifecycle-safe one-shot context menus.

The main window remains the state/signal owner; the extracted classes are behavior-preserving mixins/helpers.

## Reviewed but intentionally not changed

- The i18n `нет` file-status collision was already fixed in the supplied base: track status uses the separate `нет (файл)` key.
- `MappingDataclass._plain_value()` intentionally preserves bytes; queue persistence already serializes cover bytes explicitly as validated Base64. Changing the generic model contract would be a compatibility break.
- `SpeedGraphWidget` already calls `ui_text(..., peak=...)`, so its `{peak:.2f}` template is translated and formatted before display; the reported runtime-template failure does not apply to the current code.
- PoleKnig's fallback JS object parser already handles PlayerJS objects that are not valid JSON/Python literals (including unquoted keys). Blind regex replacement of `true/false/null` could also alter quoted URL/title content, so it was not added.
- `QtEventSoundManager.configure(language=...)` keeps the existing stop-on-language-change behavior. Clearing references without stopping active players can orphan currently playing media and retain wrong-language cues.
- `run_qt()` does not forcibly delete externally supplied `QT_QPA_PLATFORM=offscreen`: that variable can be intentional in CI/headless use, and normal Python `KeyboardInterrupt` still executes the self-test `finally` restoration.
- URL stale comparison remains based on canonical `normalize_supported_url()`. HTTP paths are not generally case-insensitive, and the supported-source normalizer already canonicalizes the meaningful trailing-slash/book-ID forms.
- `ThreadPoolExecutor` cancellation remains unchanged because remote-duration workers already check cancellation before work and every 250 ms; forced non-wait shutdown is not required for correctness here.

## Verification

- `python -m pytest -q`: 293 passed.
- `PYTHONPATH=. python tools/full_parity_audit.py --root . --require-legacy-retired`: 61/61 PASS.
- `PYTHONPATH=. python tools/qt_localization_audit.py`: OK.
- `PYTHONPATH=. python tools/qt_import_audit.py`: OK (46 project modules reachable; no legacy frontend path).
- Source compilation: `python -m compileall -q audioknigi tests`: PASS.
- Runtime/accessibility executable self-tests were not runnable in the audit container because PySide6 is not installed there; the source test suite and import/static audits still pass.
