# Round 72 — search sorting, availability filtering and download layout

Implemented user feedback from 2026-10-02:

- search results can be sorted by Title, Author or Narrator from clickable table headers, an accessible Sort menu, or the result context menu;
- Title sorting is query-aware: an exact title match is first, then shorter titles, then alphabetical order (for example `Двойник` before two-word `Двойник ...` titles);
- explicitly `restricted` / `unavailable` catalogue rows are removed from search results automatically; unknown availability remains visible so a temporary metadata failure does not hide a potentially downloadable book;
- the redundant Status search column and optional “Only available” filter were removed;
- the result table keeps keyboard/screen-reader access to sorting through the Sort button and context menu;
- the Book-tab download activity and book-details cards now use fixed vertical size policies, the description box is slightly shorter, and the active speed graph expands to 56 px instead of 72 px to prevent visual crowding at the application minimum height.
