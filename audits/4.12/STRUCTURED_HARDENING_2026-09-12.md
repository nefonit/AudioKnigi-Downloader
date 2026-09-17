# Structured refactor hardening — 2026-09-12

This review hardens the post-refactor 4.12.32 tree after the large structural split. It distinguishes confirmed runtime/build defects from audit claims that were based on an outdated calendar or package index.

## Confirmed and fixed

- **Release Python/dependency contract:** source/runtime support remains Python 3.11+, while the reproducible Windows toolchain is pinned to CPython 3.14.7. The old release pin `PySide6==6.8.3` was incompatible with Python 3.14, so the release baseline now uses PySide6 6.11.2, Playwright 1.62.0, Pillow 12.3.0 and PyInstaller 6.22.2. Normal CI exercises both Python 3.11 and 3.14.7.
- **Requirements cleanup:** `requirements.txt` is the runtime source; `requirements-qt.txt` is only a compatibility `-r requirements.txt` alias. Phase-13 dependency comments were removed.
- **CHANGELOG structure:** one root `# Changelog`, one H2 per release line, with old 4.12.31 development phases as H3 subsections.
- **urllib3 compatibility:** `Retry(other=...)` was removed so `build_http_session()` does not require the urllib3 2.x-only keyword.
- **Knigavuhe metadata:** multiple author/reader chunks are joined with spaces; narration variants are cloned before enrichment so cached objects are not mutated; the retired `_query_matches_metadata` helper was removed.
- **Duplicate preflight:** a stored duration no longer rejects a duplicate solely because the current online track duration is still unknown.
- **Diagnostics privacy/reliability:** home paths are redacted for both slash styles, log tails are kept valid UTF-8, and queue entries use opaque hashes rather than a nonexistent ID or private book title/URL.
- **Domain model:** `Track.local_status` now uses stable language-neutral codes (`missing`, `present`, `ready`, `damaged`) while old Russian snapshots are normalized on load.
- **PoleKnig text parsing:** nested book-link text is whitespace-normalized without merging words.
- **Localization:** the `Файл загружен: {name}` literal is present in EN/DE/UK, runtime regexes are compiled with DOTALL for multiline status messages, and unsupported-link UI text is explicitly localized.
- **Sidecars:** `book_info.txt` uses `track_number_width(book)` so 100+ chapter books use consistent numbering.
- **Services:** the missing `fetch_knigavuhe_book` binding is restored; search filtering accepts both provider keys (`knigavuhe`, `poleknig`, `audioknigi`) and display domains; services no longer import the provider registry, removing the service/provider import ring.
- **Qt/accessibility:** `QtPlayerController` is an explicit import, the mixin accessibility self-test imports the audit from the correct parent package, and `download_options` is covered by both required and focusable accessibility contracts.
- **Post-split hygiene:** copied monolith imports were pruned from `download/*` and `qt/mixins/*`; `tools/unused_import_audit.py` is an active pytest/CI gate.
- **Self-test teardown:** the accessibility self-test closes the window first so normal `closeEvent()` persistence/shutdown behavior runs before idempotent controller cleanup.

## Audit claims intentionally not applied

- **“Python 3.14.7 does not exist / 2026-09-12 is a future date.”** This review runs on 2026-09-12; CPython 3.14.7 was released on 2026-08-05. The real defect was the incompatible old PySide6 release pin, not the Python version itself.
- **“Chrome 151–153 are future User-Agents.”** Chrome 153 entered Stable on 2026-09-08, so downgrading the UA strings to 2025-era Chrome 132–134 would make them less accurate.
- **“Pillow 12.3.0 / Playwright 1.57 do not exist.”** Those versions exist. The release baseline was refreshed for compatibility/currentness, not because the cited packages were fictional.
- **Proxy empty-request 502 behavior:** malformed or already-closed local proxy connections are handled as controlled request failures; sending a best-effort 502 is not itself a crash defect.
- **Copy-mode `delete_source=False`:** when source and final MP3 are byte-identical, promoting the source to the final target intentionally produces one file rather than a redundant duplicate.

## Verification contracts added

The active test suite now covers release/version documentation, the release dependency baseline, urllib3 Retry compatibility, Knigavuhe cloning, neutral status codes, Windows-slash diagnostic redaction, UTF-8 log tails, opaque queue diagnostics, provider-key source filtering, service/provider direction, fallback imports, Qt static accessibility/import contracts, translation completeness, multiline runtime regexes, dynamic chapter-number width and the unused-import gate.

Historical tests remain under `archive/tests/`; `tools/historical_regression_audit.py` continues to fail on any new regression among historically passing behavior while allowing explicitly documented source-shape incompatibilities from the retired monolith.
