# Round 68 — creator identity and release metadata

Added product-author identity requested by the project creator:

- About dialog now shows `Едуард Саратовцев` as `Автор и разработчик`;
- contact email: `serioussem39@gmail.com`;
- GitHub profile: `https://github.com/nefonit`;
- project source: `https://github.com/nefonit/AudioKnigi-Downloader`;
- copyright: `© 2026 Едуард Саратовцев`;
- About includes the accessibility statement that the program was created by a blind developer with special attention to keyboard and NVDA/JAWS accessibility;
- About is a keyboard-focusable Qt dialog with read-only text plus explicit email/GitHub/repository actions;
- Windows EXE version resources are generated from the same version/brand constants at build time and supplied to PyInstaller with `--version-file`, avoiding manual version drift.

Localization strings for the About UI were added for Russian, English, German and Ukrainian.
