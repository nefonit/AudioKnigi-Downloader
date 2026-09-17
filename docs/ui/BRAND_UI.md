# AudioKnigi branded production UI

This pass adds a reusable, accessibility-safe brand layer on top of the native Tk/ttk + ttkbootstrap interface.

- Brand constants and typography live in `audioknigi/brand.py`.
- The main header uses the existing product icon, a clear `AudioKnigi Downloader` lockup, version badge, and tagline.
- Easy mode presents the primary workflow as three explicit steps: link, audio quality, destination.
- Advanced pages share a slim brand accent rail and centralized heading typography.
- Help and first-run onboarding reuse the same icon, product name, and tagline.
- No Canvas-backed interactive widgets were introduced; native ttk controls remain the accessibility surface.
- ttkbootstrap semantic styles remain the source of primary/success/info/warning/danger control states.
