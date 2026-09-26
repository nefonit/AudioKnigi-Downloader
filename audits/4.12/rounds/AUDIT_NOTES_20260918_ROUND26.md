# Audit notes — Round 26 (2026-09-18)

A Windows verification log from Round 25 isolated the Easy-mode search freeze to GUI completion itself. The worker returned 41 results and emitted `finished`, then the main thread entered `_search_finished` and stopped before the `modal_finished` marker.

## Root cause isolation

- Search networking and provider orchestration completed. One Knigavuhe timeout was handled as a partial-source error; PoleKnig continued and the worker returned results.
- The freeze occurred before result-table rendering. Round 25 diagnostics showed the last main-thread marker at `_search_finished` entry, making native dialog finalization/final progress updates the remaining boundary.

## Fix

- Removed native `ApplicationModal` / `setModal(True)` usage from the Easy-mode operation progress dialog.
- The main window now blocks its central UI and menu explicitly while the modeless progress window remains responsive for Cancel.
- Operation completion uses `hide()` plus `deleteLater()` instead of synchronous `accept()` / native modal unwind.
- The main UI is re-enabled immediately after the progress window is hidden.
- Search completion tears down the operation window before touching the final 100% widgets.
- Added detailed `OPERATION UI` and before/after finish diagnostics so any remaining Windows-specific stall can be pinned to a single call.

## Verification

Round 26 adds focused regression coverage for non-native modality, hide-only teardown, UI re-enable, and search completion ordering.

## Verification

- Full pytest suite: **409 passed, 0 failed**.
- Qt localization audit: **OK** (`ru`, `uk`, `de`, `en`).
- Exception audit: **PASS** (`reviewed_broad_exception_passes=107`).
- Undefined-global audit: **OK** (78 modules).
- Unused-import audit: **OK** (32 implementation modules).
- Full parity: **PASS 61/61**.
- Historical regression: **PASS** (`passed=267`, `known_shape_incompatibilities=116`, `resolved=0`).
- `compileall`: **PASS**.
