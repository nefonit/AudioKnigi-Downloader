# Audit notes — Round 6 (2026-09-15)

## Confirmed defects fixed

1. **PoleKnig fallback title parsing** — when `<h1>` is absent and `<title>` has the common form `«Book» Author: слушать аудиокнигу...`, the parser now extracts the quoted book title before stripping punctuation. The previous order could leave `Book» Author` in the title.
2. **Knigavuhe narration hydration side effects** — `_hydrate_narration_variant_readers()` now clones incoming `NarrationVariant` objects before enrichment. Worker threads still only return metadata, while the coordinator applies results on one thread; callers no longer observe in-place mutation of their original variant objects.
3. **PoleKnig candidate metadata defensiveness** — candidate comparison now uses `.get()`/normalized local variables for title, author and narrator rather than mixing mapping indexing with `.get()`. The current metadata producer supplies these keys, so this is defensive hardening rather than a reproduced `KeyError`.
4. **Qt accessibility self-test platform selection** — the self-test now creates its QApplication with `-platform offscreen` explicitly, while retaining the `QT_QPA_PLATFORM=offscreen` environment override. This makes the intended headless platform unambiguous on Windows build hosts.

## Reviewed but intentionally not changed

- **Claimed CONNECT truncation/RST in `network_dns.py`**: not reproduced. `_relay_bidirectional(..., return_when_right_closes=True)` only receives `b""` after previously queued upstream bytes have been read; a socket-pair regression proves payload bytes are delivered before relay return. The existing bounded upstream-EOF behavior is also an archived compatibility contract, so it remains unchanged.
- **Claim that `_extract_meta_content()` can consume the next `<meta>` tag**: false for the current regex. Every attribute span is `[^>]+`, so matching cannot cross the closing `>` of the current tag. A regression test locks this boundary.
- **`self.request._track_index(track)` allegedly missing**: false. `DownloadRequest._track_index()` exists and is used deliberately for validation/normalization. Renaming it is an API-style refactor, not a runtime fix.
- **Retained source gets `.audio` when both URL extension and detected codec are unknown**: this is a genuinely unknown-media case. Assigning `.mp3` or another player extension without evidence would mislabel the bytes. Existing ffprobe normally identifies the codec; the neutral fallback is retained.
- **Double extension for template `{Track_Title} .mp3`**: not reproduced. `_strip_literal_template_extension()` removes the literal trailing `.mp3` even when preceded by whitespace, `safe_name()` trims the remaining space, and the known media extension from the title is normalized before the final suffix is added. Regression result: `Part 01.mp3`, not `.mp3.mp3`.
- **Cloudflare DNS policy bypass by remote ffprobe/FFmpeg**: the remote ffprobe paths in both `download/probe.py` and `services/book_analysis_service.py` already inject `cloudflare_ffmpeg_input_args()`. `run_full_mp3()` invokes FFmpeg only on the already-downloaded local `source_target`, so no remote DNS lookup occurs there.

## Verification

- Round 6 focused regressions: **8 passed**.
- Full current pytest suite: **246 passed, 0 failed**.
- Exception audit: **PASS** (`reviewed_broad_exception_passes=113`).
- Historical regression audit: **PASS** (`passed=271`, `known_shape_incompatibilities=112`).
- Undefined-global audit: **OK** (77 modules).
- Unused-import audit: **OK** (32 implementation modules).
- Qt localization audit: **OK** for `ru`, `uk`, `de`, `en`.
- Full parity audit: **PASS 61/61**.
- Static Qt import-boundary audit: **OK** (73 project modules reachable, no legacy frontend path).

The Windows/PyInstaller accessibility executable self-test cannot be run in this Linux environment because PySide6 is not installed here. The source-level self-test contract and all portable tests/gates pass; the actual Windows build should still be rerun on the user's build machine.
