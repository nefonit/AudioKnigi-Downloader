# AudioKnigi Downloader — audit follow-up Round 12 (2026-09-16)

Base: `AudioKnigi_Downloader_v4_12_42_REPORT_FIXES_ROUND11_20260916`.

## Confirmed and fixed

- **Parallel FFmpeg failure shutdown:** both parallel split pools now call `_cancel_active_subprocesses()` after cancelling queued futures. This prevents `ThreadPoolExecutor.__exit__()` from waiting for a still-running long FFmpeg encode after another split has already failed.
- **Support-bundle path privacy:** forward-slash UNC/network paths such as `//server/private/...` and `//?/UNC/...` are now masked as `<configured-path>` just like backslash UNC paths.
- **Support-bundle UTF-8 tail cleanup:** removed the redundant whole-tail strict UTF-8 validation loop. The final `decode(..., errors="ignore")` already safely trims incomplete byte sequences at either byte-limited edge without repeatedly decoding up to 512 KiB.
- **Schema.org JSON-LD types:** structured-book detection now accepts short types and namespace-qualified types such as `https://schema.org/Book`, `http://schema.org/Audiobook`, and `schema:CreativeWork`.
- **Knigavuhe early cancellation:** `fetch_book()` checks an already-set cancellation event before normalizing the URL or opening an HTTP session.
- **Full-MP3 retained-source collision:** a custom final output template may legitimately resolve to `<Title> (исходник).mp3`. The retained original source now gets a distinct visible sibling name (`<Title> (исходник, оригинал).ext`) instead of leaving a hidden `.full-source` file or overwriting the processed result.
- **Remote-size probing:** `_remote_size()` explicitly sends `Accept-Encoding: identity` together with the one-byte Range request so `Content-Length` is not distorted by transport compression when a server falls back to HTTP 200.
- **Download-request typing:** `build_download_request()` now accepts `Mapping[str, Any] | None`, matching the `AppSettings`/normalization contract instead of requiring a concrete `dict` in static typing.
- **Dropped-URL queue continuation:** if analysis unexpectedly returns a non-`Book` payload, pending dropped URLs are scheduled to continue instead of remaining stranded indefinitely.
- **Windows `.url` shortcut validation:** decoded `URL=` values are adopted only when they are supported AudioKnigi site URLs; malformed/foreign shortcut payloads no longer replace the original dropped value.

## Reviewed but not changed

- **Mixin cross-dependencies:** `ProbeMixin`, `BookFlowMixin`, `SourceAnalysisMixin`, and `NetworkDownloadMixin` are composed implementation pieces of the downloader facade. Their cross-calls are intentional in the supported composed class; moving helpers solely to make each mixin independently instantiable would be an architectural refactor, not a demonstrated runtime crash.
- **`_download_source_with_fallback()` indexing:** the current one-based loop deliberately uses `urls[pos]` as the *next* URL and checks `pos >= len(urls)` before indexing. With the function's one-primary/one-fallback contract, empty/missing primary values do not produce an `IndexError`.
- **Hard-coded `max_workers=3` for independent source downloads:** this is a performance policy rather than a correctness defect. It was not tied to Range worker count because those are different concurrency layers.
- **Existing APIC preservation:** when no replacement cover exists, existing embedded art is retained intentionally; deleting it would be destructive metadata loss.
- **`{Track_Title}` fallback:** the existing fallback to the book title avoids filenames such as `01 -.mp3` when a user-authored template includes separators around an empty track-title token. This behavior was kept.
- **Proxy relay lifetime:** no arbitrary total relay-session timeout was introduced because legitimate large/slow FFmpeg or Chromium transfers can exceed such a ceiling; existing inactivity/half-close handling remains the safer boundary.
- **Dynamic `Озвучка N` filesystem labels:** filesystem identity is intentionally language-stable. UI narration labels already use localization helpers, so no runtime-regex rule was added for path-oriented fallback names.
- **Settings-sync `_set_combo_data`:** the method exists in `SettingsUiMixin` and is available to the composed window through MRO; the reported `AttributeError` is not present.
- **QMediaPlayer immediate seek/play and queue drag-end semantics:** these were described as backend/UX nuances without a reproduced regression, so no speculative behavior change was made.

## Verification

- Focused Round 12 regressions: **9 passed**.
- `pytest -q`: **297 passed**.
- Historical regression audit: **PASS**, 270 historical checks passed with 113 known shape incompatibilities tracked.
- Exception audit: **PASS** (`reviewed_broad_exception_passes=112`).
- Undefined-global audit: **OK (77 modules)**.
- Unused-import audit: **OK (32 implementation modules)**.
- Qt localization audit: **OK** for `ru`, `uk`, `de`, `en`; static UI literals, help, onboarding and accessible names complete.
- Full parity audit: **PASS 61/61**.
- Qt import audit: **OK (73 project modules reachable, no legacy frontend path)**.

The real frozen Windows/PySide6/PyInstaller gate still requires the Windows build environment; source/static Linux checks do not replace it.
