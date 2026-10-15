# Product / QA Risk Register

| ID | Risk | Likelihood (estimate) | Impact | Mitigation | Residual |
|---|---|---|---|---|---|
| RSK-01 | Corrupted or incomplete downloaded file | Medium | Critical | HTTP/range/EOF tests, checksums, resume test | Pending Windows E2E |
| RSK-02 | Queue/history data loss on upgrade | Medium | Critical | migration fixtures, backup/restore and corrupted JSON tests | Pending release profile |
| RSK-03 | Secrets or local paths in diagnostics | Medium | Critical | sanitization tests, manual ZIP review | Pending Windows privacy review |
| RSK-04 | NVDA/JAWS unusable workflow | High (no final evidence) | Critical | manual keyboard scripts in Test Cases, accessibility audit | Blocked until UAT |
| RSK-05 | DNS/provider instability | High (external dependency) | Major | mocks, retries, DNS fallback, timeout tests | External variability |
| RSK-06 | FFmpeg mismatched profile/loudnorm | Medium | Major | real MP3 metadata/duration inspections | Pending representative codecs |
| RSK-07 | Frozen EXE missing locales/assets | Medium | Critical | clean Windows EXE smoke/install | Pending exact EXE |

Likelihood here is a **planning estimate**, not measured incident frequency. Update after field telemetry/defect triage.