# Release licensing checklist

This project bundles or depends on components under different licenses. Before a public binary release:

1. Choose and publish a top-level license for AudioKnigi Downloader itself.
2. Review Mutagen (GPL-2.0-or-later) obligations for the exact distribution model.
3. Preserve the Qt/PySide6 notices and satisfy the selected open-source/commercial Qt terms.
4. Include the license/source-offer material required by the exact FFmpeg/FFprobe binaries being bundled.
5. Preserve Playwright, Requests, Pillow and PyInstaller notices; PyInstaller's bootloader exception allows bundling applications, subject to dependency licenses.
6. Archive the exact dependency versions and the FFmpeg build configuration used for each release.

This checklist is operational guidance, not legal advice.
