# AudioKnigi Downloader 4.7.5 — audit disposition

## Fixed

- Untitled books now use `audiobook` for full MP3/M4B filenames and metadata text.
- Empty tuple cover payloads are handled explicitly.
- Search results are assembled in the worker and committed to shared/UI state on the Tk thread.
- Windows toast PowerShell explicitly activates WinRT notification/XML types; notification text remains Base64 data, not executable PowerShell.
- Natural player completion uses the last valid position when pygame returns `-1`, while unexpected early stops keep a resume point.
- Template folder fallback is explicitly non-empty.

## Verified / not a crash in 4.7.4

- `LibraryVisualMixin._photo_from_payload(())` already returned `None` because empty tuples are falsey, and `_payload_key` already caught indexing errors. 4.7.5 makes this explicit.
- `SearchMixin.log()` and `set_status()` were already UI-safe because both route widget work through the event bus. 4.7.5 additionally removes incremental worker mutation of `self.search_results`.
