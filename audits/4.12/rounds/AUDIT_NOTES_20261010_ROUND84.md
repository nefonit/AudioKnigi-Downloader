# Round 84 — user-log and accessibility follow-up

Confirmed and fixed from real support diagnostics and the keyboard-accessibility report:

- Qt startup once again writes a privacy-sanitized `SESSION START` line with current application version, Python, OS, language and UI mode.
- `session_state.json` is refreshed by the Qt lifecycle with current version/language/mode and `running=true` at startup, then `running=false` on normal exit. This prevents a legacy 4.12.31 state file from being mistaken for the current build.
- `last_crash_report.txt` is now treated as current evidence only when its first-line application version matches the running build. Stale reports from older versions are omitted from support bundles and from Help Center “copy error report” output instead of being presented as a current crash.
- F1 “Keyboard shortcuts” help no longer connects `QAction.triggered(bool)` to a zero-argument lambda. It now uses a dedicated bool-compatible slot, while Shift+F1 remains contextual help.

Reviewed and intentionally unchanged:

- The September 4.12.31 Tkinter `RecursionError` in the supplied crash report is historical and does not identify a current Qt crash.
- A 2026-10-09 audioknigi.com.ua SSL/read timeout is a provider/network failure; subsequent searches and downloads completed successfully. No runtime-code change was justified from that timeout alone.
- A misspelled author query (`гарри гарисон` versus `Гаррисон Гарри`) returning no results is a fuzzy-search enhancement opportunity, not a stability defect.

Regression coverage remains in the consolidated domain modules; no `test_round84_*.py` file was created.
