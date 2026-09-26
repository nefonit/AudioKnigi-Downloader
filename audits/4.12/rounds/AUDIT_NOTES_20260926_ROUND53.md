# Round 53 audit notes — 2026-09-26

Reviewed the supplied post-Round-52 audit against the actual source and Qt documentation.

## Confirmed fixes

- Follow-up to the Round 52 Windows CI failure: retain bounded nonempty UTF-8 log tails when their only newline is the final CRLF. Explicit LF/CRLF byte fixtures reproduce the Windows case on every platform.

- Missing-source diagnostics now retain chapter index zero.
- Exception audits resolve the allowlist relative to the requested project root. Broad exception tuples and empty ellipsis handlers are detected without relaxing existing allowlist requirements.
- Localization audits cover named text arguments, including mixed positional/keyword calls and dynamic setters. Missing required runtime sources produce an explicit audit failure instead of being silently skipped.
- Undefined-global analysis includes `audioknigi_qt.py`.
- Source packages retain configuration fixtures specifically beneath `tests/fixtures`, continue excluding private runtime-state basenames elsewhere, and exclude `.pyd`, `.so`, and `.dll` build artifacts.
- Disk-space estimates recognize scalar and collection `all`/`*` selectors as the entire book. Invalid/boolean indices raise a clear error instead of being dropped and underestimating disk requirements.
- Acceptance `--status` reads existing evidence without resetting or rewriting it. A rejected/missing candidate manifest is displayed alongside the report, forces INCOMPLETE and a nonzero result, and EXE hash mismatches remain visible. Mutating acceptance runs still require a valid candidate manifest.
- Round 49 precedes Round 48 in the changelog again.

## Intentionally unchanged

- `QWidget.close()` sends a close event even when the widget is hidden: https://doc.qt.io/qt-6/qwidget.html#close . The report's opposite claim does not justify changing shutdown behavior.
- An existing QApplication is reused with its already-selected platform; forcing another singleton or changing the environment afterwards would not safely switch its backend.
- Release-baseline dates record previously verified build provenance. They were not advanced without a new validated Windows release. The original version heading and individual Round 42 history entries remain intact.
- Backup queue schema validation remains strict; diagnostic support bundles intentionally accept broader shapes.

## Verification

- Full local pytest suite: 648 passed on Python 3.12, including 19 new Round 53 cases.
- The static-quality wrappers are included in that suite.
- Final focused rerun covers the mixed positional/keyword UI-text case.
- This Linux run does not validate the frozen Windows EXE, multimedia/tray behavior, or manual NVDA/JAWS acceptance.
