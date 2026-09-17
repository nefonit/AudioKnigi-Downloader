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

## All functions production polish

The advanced workspace now follows the same visual language as the default screen while keeping every existing power-user action and native accessible control.

- **Search** uses a clear query card, one primary Find action and a separate results surface.
- **Queue** groups adding books, queue contents, run/pause/cancel and per-book management into distinct sections; destructive actions use a danger style.
- **Library / History** separates book actions from backup/export actions and makes destructive history operations visually distinct.
- **Book** keeps the compact, regression-tested layout while emphasizing Analyze/Download as primary actions and Cancel as destructive.
- **Settings** has a calmer production header, keeps everyday settings first, and marks technical tuning as optional.
- **Help** is now a two-pane support center with topic navigation, concise plain-language answers, keyboard hints and a dedicated crash-report action.
- Missing Drag-and-Drop support no longer exposes an installation instruction to ordinary users; the interface simply points them to the link field instead.
- Full regression suite after the UI pass: **161 passed**.

## ttkbootstrap semantic design pass

This production variant uses ttkbootstrap as the semantic theme source rather than only as a theme switcher.

- `darkly` / `flatly` provide the active semantic palette when ttkbootstrap is installed: primary, secondary, success, info, warning, danger, background, input, selection and border colors.
- Existing native `ttk` widgets now accept a lightweight `bootstyle=` compatibility argument. The argument maps to screen-reader-safe named ttk styles; no Canvas-based replacement controls are introduced.
- Primary calls-to-action, outline secondary actions, success playback/actions, warning pause states, danger/destructive actions, info actions, badges, search fields, comboboxes and progress bars use consistent semantic variants.
- Legacy hard-coded Tk frame/text surfaces are repainted from the active runtime palette so the container layer follows the same theme as ttk controls.
- If ttkbootstrap is unavailable, the same semantic style names fall back to the built-in WCAG-aware palette instead of breaking startup.
