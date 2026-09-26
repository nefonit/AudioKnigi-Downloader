# Round 40 — Windows visual refinement (2026-09-20)

Round 40 is based on direct review of the Windows production screenshots from Round 39. It changes presentation only; search/download behavior is intentionally untouched.

## Applied

- Raised dark-theme secondary/empty-state text contrast to a silver-gray `#9ba3af` family instead of relying on the dimmer generic muted token.
- Refined accessibility focus outlines to a warm amber `#e5a93c`, 2 px, with radii synchronized to the focused control. This keeps the keyboard focus obvious while reducing the heavy container look seen around tables/settings navigation.
- Rebuilt Simple/Advanced as a true segmented control with one shared holder, zero gap, transparent inactive segments and one blue selected segment.
- Centered the Advanced workspace and capped it at 1500 px so tables no longer span an entire ultrawide monitor.
- Rebalanced Advanced Search columns: Title, Author and Narrator are flexible; Source stays compact. The book-parts table stretches the chapter title rather than the source URL.
- Added a modest minimum height to the Easy card so the centered layout feels less like a compressed island on large displays.
- Upgraded Help Center rendering from plain text to rich text without changing topic content: larger blue heading, paragraph/list spacing and `<kbd>`-style keyboard badges.
- Increased menu-bar top/bottom padding slightly for Windows 11 breathing room.
- Search progress dialog was deliberately left unchanged because the supplied screenshot showed it as one of the strongest visual components.

## Accessibility

- Focus remains color + shape, not color alone.
- No accessible identifiers, names/descriptions, Tab order or screen-reader announcements were removed.
- The focus ring is thinner but still a full 2 px high-contrast outline.

## Verification

- `compileall`: PASS.
- Round 40 static UI contracts: PASS.
- PySide6/Windows visual acceptance must be performed on the user Windows build; this container does not include PySide6.
