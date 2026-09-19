# AudioKnigi Downloader — audit follow-up Round 14 (2026-09-16)

Base: `AudioKnigi_Downloader_v4_12_42_REPORT_FIXES_ROUND13_20260916`.

## Confirmed and fixed

- **Legacy normalization migration:** profiles that still contain `normalize_audio=true` but no canonical `normalization_mode` now migrate to `single` instead of silently resetting normalization to `off`.
- **Support-bundle embedded Windows paths:** absolute drive/UNC paths are redacted even when embedded inside an error/status sentence, while ordinary `https://...` URLs are left intact.
- **Literal Range segment discovery:** `.segNNN` siblings are enumerated literally instead of feeding `glob.escape()` syntax into `Path.glob()`. Filenames/folders containing square brackets are safe, and `.segments.json` is explicitly not mistaken for an audio segment.
- **Audio-info single-flight retry:** waiters no longer recurse back into `_cached_probe_audio_info()` when the owner fails to publish a result. They re-enter an iterative ownership loop, preserving one ffprobe per same file while allowing different files to probe concurrently.
- **Duplicate sidecar preflight:** legacy/mapping-style track rows are read through the mapping-safe field helper instead of direct `.index/.title/.start/.end` attributes.
- **PoleKnig PlayerJS fallback:** browser extraction uses circular-safe JSON serialization so a self-referencing PlayerJS playlist cannot discard the whole candidate payload.
- **PoleKnig relevance:** server-ranked search rows are no longer discarded merely because every free-form query token is absent from title/author/narrator metadata (for example publisher/series/`аудиокнига` terms).
- **Narration-switch selections:** switching narration preserves the chapter indices the user explicitly selected instead of resetting the fresh Track list to all chapters selected.
- **Player chapter focus:** activating a chapter in the chapter list loads/autoplays it without forcibly moving keyboard/screen-reader focus to the Play button.
- **Event-sound recovery:** a `QMediaPlayer` that reports `InvalidMedia` is retired from the cache before the system-sound fallback, allowing the next occurrence to build a fresh player.
- **Windows media-key HWND teardown:** unregistering global hotkeys now uses pointer-width-safe `ctypes.c_void_p` conversion just like registration.
- **Output-directory refresh:** choosing a folder no longer triggers both an immediate unfinished-download disk scan and the already-wired debounced scan; slow NAS/external paths are scanned once.
- **Screen-reader duplicate speech:** Queue and History no longer explicitly announce the same row summary that is already exposed through `AccessibleDescriptionRole`, preventing duplicate NVDA/JAWS speech.

## Reviewed but not changed

- **PoleKnig genre `match` variable reuse:** local-variable shadowing is a readability issue, not the reported `AttributeError`; genre extraction safely handles an empty cleaned label.
- **SearchResult/NarrationVariant availability types:** the string status on search rows and `bool | None` on individual narration variants are intentional model-layer distinctions, with explicit conversion at provider boundaries.
- **Cloudflare relay `select()` semantics / proxy lifetime:** disconnects are already handled through empty `recv()` and socket errors. A global relay-session lifetime was not added because it could terminate legitimate long FFmpeg/Chromium transfers.
- **Thread-local requests sessions:** no reproducible descriptor/port leak was demonstrated in the current lifecycle; broad session-pool redesign was not introduced.
- **Adaptive Range controller race:** `observe()` already serializes target/slow-sample/last-change state under its own lock, so concurrent reporters cannot perform the claimed double reduction inside the same interval.
- **Zero-duration `-t 0` split:** current duration selection only accepts positive inferred/measured durations or `end > start`; the reported command is not emitted by the current code.
- **Stale source-slot reuse after playlist refresh:** stale source downloads are cleared on media-playlist refresh and resumable segments are additionally bound to URL/size/range signatures from Round 9.
- **Malformed `.url` host/port:** supported-URL normalization already catches parser/port errors; malformed shortcut data does not escape as a `ValueError` from that layer.
- **Easy-mode result stale state:** selecting a search result already replaces the universal field with the result URL before automatic analysis, so a successfully analyzed result can enable Easy download.
- **Normalize preset size inflation:** `_effective_mp3_profile()` caps target bitrate/channels to the source profile, so a 64 kbps mono input is not blindly upmixed to 128 kbps stereo.
- **Priority persistence / quality-preset policy / broad mixin refactors:** these are workflow or architecture choices rather than reproduced runtime defects in this round.
- **Missing-media modal deadlock:** the current dialog owns a cancellation timer plus active prompt/box cancellation, which is specifically intended to break the worker wait during application shutdown.

## Verification

- Focused Round 14 regressions: **13 passed**.
- `pytest -q`: **322 passed**.
- Historical regression audit: **PASS**, 270 historical checks passed with 113 known shape incompatibilities tracked.
- Exception audit: **PASS** (`reviewed_broad_exception_passes=112`).
- Undefined-global audit: **OK (77 modules)**.
- Unused-import audit: **OK (32 implementation modules)**.
- Qt localization audit: **OK** for `ru`, `uk`, `de`, `en`; static UI literals, help, onboarding and accessible names complete.
- Full parity audit: **PASS 61/61**.
- Qt import audit: **OK (73 project modules reachable, no legacy frontend path)**.

The real frozen Windows/PySide6/PyInstaller gate still requires the Windows build environment; source/static Linux checks do not replace it.
