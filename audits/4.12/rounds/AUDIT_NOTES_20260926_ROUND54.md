# Round 54 hardening notes — 2026-09-26

Follow-up review of Round 53 focused on edge cases that were not covered by its 19 regressions.

## Fixed

- Support-bundle log tails no longer preserve an arbitrary partial first line when the bounded byte window starts in the middle of that line. Such a fragment can lose the Windows drive/UNC prefix that the privacy sanitizer relies on and expose part of a private path. A marker is archived instead when no complete line is available.
- Disk-space selection parsing now accepts scalar integer indices but rejects booleans, fractional floats, NaN, infinity, negative values and non-iterable invalid collections with controlled ValueError errors instead of silently truncating or leaking a TypeError.
- Qt localization auditing now understands icon+text positional overloads for QAction, QPushButton, addAction and addItem, and dynamic raw f-strings are checked in constructors as well as setters.
- Acceptance parsing treats malformed schema types as invalid evidence instead of crashing while converting them with int(...). Both candidate-manifest validation and persisted acceptance-report checks fail closed.

## Regression coverage

- Truncated support-log privacy with Windows path fragments.
- Complete-line preservation after a truncated prefix.
- Fractional/non-finite/boolean and scalar track selections.
- Qt icon+text overloads and constructor f-strings.
- Malformed acceptance report/candidate schema values.

Windows packaged runtime and manual NVDA/JAWS acceptance remain separate release gates.
