# Round 62 — Round 61 audit follow-up

Applied confirmed findings from the follow-up review:

- removed dead `_privacy_path` absolute-path bookkeeping;
- accepted `Track`-like objects in `_estimate_required_space`;
- preserved `start`/`duration` when loudnorm uses `filter_complex`;
- refreshed audio-info cache entries on access so eviction is LRU instead of FIFO;
- restored language-appropriate keyboard names in EN/RU/UK and completed the reported DE/UK terminology fixes;
- preferred detected response encoding before requests' default ISO-8859-1 to avoid Cyrillic mojibake;
- preserved case-sensitive player-position keys on POSIX while retaining Windows normalization;
- protected history deletion during backup rollback and history reads during duplicate checks with `HISTORY_LOCK`.

Reviewed but intentionally unchanged:

- the Audioknigi description helpers are used from `book_analysis_service.py`; they are not dead code;
- `services.__all__` remains a deliberately narrow facade;
- non-Windows `install_cloudflare_dns` behavior is intentional platform isolation;
- `main_window_pages.py` accessibility localization style is inconsistent but functionally correct through `configure_accessible`;
- PlayerJS parsing, template substitution, Qt timer lifetime, operation-dialog behavior, UI relay, worker deepcopy normalization, field-sync guards, deferred search rendering, graceful shutdown and `.url` drag-and-drop were positive findings and required no changes.
