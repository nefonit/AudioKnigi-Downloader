# Production UI pass

This build keeps the 4.8.22 download engine and native accessible Tk/ttk architecture, while polishing the ordinary-user experience.

## Main changes

- The default screen now follows one clear workflow: link → audio quality → save destination → download → progress/result.
- Added a visible **Paste** action that does not unexpectedly start analysis.
- Removed decorative/demo status chips from the real product screen.
- The save destination is visible before download and links directly to Settings.
- User-facing status text no longer duplicates a colored status dot with emoji.
- Header navigation is calmer: **Main** and **All functions**.
- The sidebar is a compact quick-access area instead of a promotional/decorative panel.
- Completion actions use concise everyday labels.
- First-run onboarding has a clearer welcome and purpose statement while keeping the same three-step flow.
- Native controls, keyboard navigation, screen-reader semantics, high-DPI scaling and the existing advanced workspace are preserved.
