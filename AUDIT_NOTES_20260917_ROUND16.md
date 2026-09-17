# AudioKnigi Downloader 4.12.42 — Round 16 Help Center expansion

Date: 2026-09-17
Base: Round 15

## Request

The user specifically requested that the in-app Help section be expanded fully rather than leaving topics as one or two short sentences. This round intentionally focuses on the real Qt `Help Center` opened by F1/Shift+F1 rather than adding another external document.

## What changed

### Complete Qt Help Center

`audioknigi/qt/help_center.py` now contains 16 substantial topics in every supported UI language (`ru`, `uk`, `de`, `en`):

1. Getting started
2. Simple vs Advanced mode
3. Book, narration and parts
4. Search
5. Download/resume/full MP3
6. Quality, encoding and normalization
7. Queue
8. History/library
9. Player
10. Settings
11. Files/folders/templates
12. Backup/transfer
13. NVDA/JAWS and keyboard-only operation
14. Keyboard shortcuts
15. Diagnostics/support report
16. Troubleshooting/recovery

The Russian bodies are all substantially longer than the previous one/two-sentence entries, and the other three languages have matching topic coverage and order.

### User-facing behavior documented

The expanded help includes concrete behavior that previously required reading source code or audit notes:

- supported sites and universal search/link field;
- narration variants and selected chapters;
- selected-parts versus full-MP3 downloads;
- resume, `.part`, `.segNNN`, `.segments.json`, Range downloading and playlist refresh;
- browser fallback through Microsoft Edge;
- Standard / Phone / Normalize presets plus advanced encoding/normalization;
- safe fallback when two-pass loudnorm measurement is incomplete;
- persistent queue actions, retry, pause, priority and one-MP3 semantics;
- history actions and JSON/CSV export;
- Qt Multimedia playback, saved positions and media keys;
- case-sensitive filename-template tokens such as `{Track_Number}`;
- backup versus diagnostic bundle semantics;
- privacy behavior of diagnostic ZIPs;
- NVDA/JAWS keyboard workflows and accessibility self-test;
- recovery steps for interrupted downloads and queue failures.

### Help Center header

`help_short_intro` in `audioknigi/locales/messages.json` was changed in all four languages so the UI no longer calls the Help Center a "short instruction" after the expansion.

### Shortcut compatibility

The existing F1 contract remains unchanged: the menu shortcut still opens the accessibility/keyboard help topic. Shift+F1 remains contextual Help Center. A dedicated `shortcuts` topic is now available in the topic list without breaking archived behavior.

## Deliberately not changed

This round does not alter downloader/network/provider behavior merely because the same user message contained technical observations. Several of those observations were informational (for example the conservative shared fallback URL strategy and correct one-based fallback indexing). The requested product change was the completeness of the Help section, so runtime changes were kept out of this round.

## Regression coverage

Added `tests/integration/test_help_center_round16_20260917.py` with 4 focused checks:

- all four languages expose the same 16-topic help structure;
- every topic has a substantial multi-paragraph body;
- Russian help covers the complete workflow and key advanced behaviors;
- the Help Center intro no longer describes itself as short, while the historical F1/Shift+F1 contract remains intact.

## Verification

- Targeted Round 16 tests: **4 passed**
- Full pytest suite: **336 passed, 0 failed**
- Historical regression audit: **PASS — 270 passed, 113 known shape incompatibilities**
- Exception audit: **PASS — 111 reviewed broad exception passes**
- Undefined global audit: **OK — 77 modules**
- Unused import audit: **OK — 32 implementation modules**
- Qt localization audit: **OK** (`ru`, `uk`, `de`, `en`; help topics complete)
- Full parity audit: **PASS — 61/61**
- Qt import audit: **OK — 73 project modules**
- Python compileall: **PASS**

## Platform note

No Windows/PySide6/PyInstaller frozen executable was built in this Linux environment. The existing Windows build/runtime self-tests still need to be run on Windows before claiming frozen-build success.
