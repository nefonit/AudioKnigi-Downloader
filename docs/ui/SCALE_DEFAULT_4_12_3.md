# AudioKnigi Downloader 4.12.3 — default scale 100%

A clean user profile now starts the interface at **100%**.

The previous code used 125% as the fallback in several places, so a user who launched the EXE for the first time automatically received 125% even when Windows itself was not requesting it.

The default is now centralized as `DEFAULT_UI_SCALE = 100` and is used consistently by startup, settings restore, scale application and settings persistence.

Existing saved preferences are preserved. If `settings.json` already contains `"scale": 125` (or another supported value), the program keeps that value rather than overwriting the user's choice.

On Windows the settings file remains in `%APPDATA%\AudioKnigiDownloader\settings.json`. A user who already ran an older build with the former 125% default can select 100% once in Settings; that choice will then be saved.
