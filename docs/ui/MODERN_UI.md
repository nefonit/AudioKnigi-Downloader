# Modern Accessible UI — 4.8.2

AudioKnigi Downloader uses one interface for sighted, keyboard and screen-reader users.

## Runtime widget policy

- Interactive controls are standard Tk/ttk widgets.
- Visual containers are native Tk frames/labels; there is no CustomTkinter runtime dependency.
- `ttkbootstrap` is used as a theme engine for native ttk widgets (`darkly` / `flatly` when available).
- If ttkbootstrap cannot load, the project keeps the same native controls and falls back to a polished `clam` style.

## Visual system

Dark core palette: background `#1E1E1E`, panel `#2D2D2D`, accent `#0078D4`, primary text `#E6E6E6`, muted text `#B8B8B8`. Core text/background pairs meet WCAG AA 4.5:1. The app uses Segoe UI on Windows, roomier padding and flat borders.

Treeviews use 30 px normal rows (larger in Large mode), bold headings and alternating row backgrounds. Queue/library rows stay taller because they contain cover thumbnails. Selection, errors and completion are also described in text; color is never the only state signal.

## Accessibility rules

- No icon-only action buttons.
- Tab/Shift+Tab order follows the widget construction order.
- Programmatic tab switches focus the first logical control in the destination.
- Native Enter/Space/arrow behavior is not replaced.
- JAWS/NVDA integration remains automatic and has no user-facing accessibility toggle.


## Long settings pages

The Settings page uses a Canvas only as a non-interactive scrolling viewport because Tk has no native scrollable Frame. All controls inside it remain real Tk/ttk widgets. The viewport itself is not in the Tab order, mouse-wheel scrolling is supported, and keyboard focus automatically scrolls the focused setting into view.

Placeholder-like examples are shown as persistent helper text instead of being inserted into Entry values. This keeps validation/StringVar state correct and gives both sighted and screen-reader users the same hint.
