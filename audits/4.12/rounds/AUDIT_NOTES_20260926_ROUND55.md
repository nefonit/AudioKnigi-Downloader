# Round 55 — accessibility, guidance and source resilience — 2026-09-26

Round 55 follows a user workflow review focused on NVDA/JAWS usability, visual guidance, source availability, search speed, narration hand-off, player keyboard operation and Help Center readability.

## Accessibility and guidance

- Added one visible current-step guidance banner shared with native Qt accessibility announcements.
- Advanced tabs announce concise next actions; Easy mode keeps a shorter guided workflow.
- Player controls now carry explicit screen-reader descriptions. Enter/Return is guaranteed for player buttons while Space keeps native QPushButton activation.
- The accessibility self-test now checks every visible keyboard-focusable button for both a spoken name and description, in addition to the stable widget-ID contract.
- Global shortcuts are stored with explicit WindowShortcut context so they remain active while focus moves between tabs and child controls.

## Source availability and blocking guidance

- Startup probes the three built-in source hosts concurrently in a daemon thread after the main window is visible.
- If some sources fail, the user is told that search will continue on available sources.
- If all sources fail, NVDA/JAWS receives an assertive warning and sighted users receive an application-modal warning.
- The warning first asks the user to verify the Internet connection. It then explains that a VPN may be needed when sites are blocked by the provider/country and gives Proton VPN and Mullvad VPN as examples.
- Existing Cloudflare support remains DNS-over-HTTPS / Cloudflare DNS. The UI explains that Cloudflare WARP can help with some network/DNS filtering but does not provide country selection.

## Search

- Independent source adapters are now started concurrently with a bounded outer pool. Final result order remains provider-registry order.
- Cancellation is still propagated into every provider and pending outer futures are cancelled.
- This intentionally supersedes the Phase 16 historical source-shape assertion that prohibited an outer search executor. The new behavior is covered by a barrier-based regression proving that all three sources start concurrently and by the historical-audit allowlist entry documenting the deliberate change.

## Narration and download hand-off

- Easy-mode narration selection automatically chooses the selected narration and starts analysis.
- Advanced narration switching keeps its automatic re-analysis and now marks the operation for download-focus hand-off.
- After narration-triggered analysis succeeds, keyboard/screen-reader focus moves directly to the Download book button and the user is told to press Enter or Space.
- Analysis, download start, cancellation, failure and completion now publish next-step guidance.

## Help Center

- Replaced the two-column fixed layout with a non-collapsible horizontal splitter.
- Topic rows have explicit height, spacing and word wrapping, preventing high-DPI/scaling overlap.
- The Russian guide adds practical next-step instructions to all 16 existing topics without changing their stable topic keys.

## Localization and verification

- New guidance is translated for Ukrainian, German and English through the existing literal catalog.
- New focused Round 55 regressions cover parallel search, source-health semantics, VPN/WARP messaging, player activation guidance, global shortcut context, button accessibility checks, narration focus hand-off, Help Center layout and the visible guidance banner.
- Local gates before push: full parity 61/61; Qt import audit OK; Qt localization audit OK; exception audit PASS; unused-import audit OK; undefined-global audit OK; historical regression PASS; Round 55 + Help Center focused tests 14 passed.

Packaged Windows runtime and real NVDA/JAWS behavior remain release-acceptance checks beyond source-level CI.
