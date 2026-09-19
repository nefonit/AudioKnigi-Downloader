# Audit notes — Round 24 (2026-09-18)

Round 24 applies the 2026-09-18 runtime/UI review on top of Round 23, with emphasis on Easy-mode operation feedback, localization, audioknigi.com.ua metadata quality, and crash diagnostics.

## Confirmed and fixed

- Added one reusable application-modal Easy-mode progress dialog for search, book analysis, and direct downloads. It blocks interaction with the main window while work is active, keeps worker signals flowing through the normal Qt event loop, exposes progress/status text, and routes Cancel to the owning operation.
- Hardened missing-media decisions: the modal decision box resolves the worker prompt when finished/destroyed, and the worker has a bounded safety timeout instead of waiting forever if the GUI path fails unexpectedly.
- Added traceback logging to Search/Analysis/Audiobookshelf workers and installed a `threading.excepthook` crash-report bridge for uncaught Python-thread exceptions. Existing `sys.excepthook` crash reporting remains intact.
- Fixed audioknigi.com.ua playlist labels such as `king_Rat_1, king_Rat_1`: duplicate labels collapse, filename/slug-like labels are replaced by the human book title plus a stable part number, while genuine chapter titles are preserved.
- Expanded audioknigi.com.ua title canonicalization so `онлайн` is removed both before and after the `аудиокнига` label.
- Replaced the fixed 1.5-second Playwright post-DOM wait with cancellable 250 ms polling for up to 8 seconds, giving Cloudflare/player initialization time to expose the playlist.
- Made Knigavuhe `BookController.enter(...)` extraction ignore JavaScript line/block comments, including commented-out calls and misleading brackets inside comments.
- Percent-encode non-ASCII HTTP request targets in the local Cloudflare proxy before ISO-8859-1 header serialization, and tolerate socket invalidation around both `select.select` waits.
- Fixed float-string chapter boundaries (`"10.0"`, `"120.0"`) by converting through `float` before `int`.
- Improved support-bundle path privacy for Windows paths with spaces in directory components without consuming ordinary text after a path; `_tail()` now preserves a clean line boundary while still dropping a genuinely partial first line.
- Migrated and removed the obsolete persisted `normalize_audio` boolean after transferring its intent to `normalization_mode`.
- Added runtime translations for tray strings without the historical leading space and aligned placeholder translations so they do not add punctuation absent from the source placeholder.
- Localized queue-complete tray notification through the canonical `Очередь завершена.` string.
- Preserved single-click chapter playback while debouncing the immediate `itemClicked` + `itemActivated` duplicate event sequence.
- Stopped the player position-save timer before the final shutdown save, then stopped media playback.
- Avoided filesystem probing for ordinary dragged HTTP(S) URLs that happen to end in `.url`.
- Bounded unfinished-download traversal only when a filesystem root is selected accidentally; normal library folders retain arbitrarily deep user templates.

## Reviewed and intentionally retained

- Full-MP3 ID3 handling is already safe: a non-MP3 source is transcoded to MP3 before ID3 writing; direct stream copy is used only when the probed source codec is MP3.
- `quality_preset` and `audio_preset` are not duplicate runtime settings: the former is the UI/user quality abstraction and the latter is the concrete encoder profile.
- FFmpeg/ffprobe proxy arguments are already emitted before the input URL, so the reported `-http_proxy` ordering problem is not present.
- Chrome 153 is not treated as a future/nonexistent user agent for the current September 2026 release line.
- Range HTTP 416 continues to fall back to the safer non-segmented path rather than guessing a corrected byte range after the server rejected the request.
- The repeated cancellable-future helpers and parser `_clean_text` variants were not mechanically centralized in this bug-fix round; they have source-specific semantics and changing them would add refactor risk without fixing a reproduced runtime defect.
- `Track.local_status` remains a plain dataclass field; all current application mutation paths use the canonical status helpers.
- Settings-page regrouping was left unchanged because it is a layout redesign, not a correctness/accessibility defect from this runtime report.

## Verification

- Round 24 focused regressions: **12 passed**.
- Full pytest suite: **402 passed, 0 failed**.
- Qt localization audit: **OK** (`ru`, `uk`, `de`, `en`; static UI literals, help, onboarding, accessible names complete).
- Exception audit: **PASS** (`reviewed_broad_exception_passes=107`).
- Undefined-global audit: **OK** (78 modules).
- Unused-import audit: **OK** (32 implementation modules).
- Full parity: **PASS 61/61**.
- Historical regression: **PASS** (`passed=267`, `known_shape_incompatibilities=116`, `resolved=0`).
- `compileall`: **PASS**.

Windows frozen-EXE behavior still requires the normal Windows/release workflow; this source round was validated in the current Linux test environment and retains the existing Windows CI coverage.
