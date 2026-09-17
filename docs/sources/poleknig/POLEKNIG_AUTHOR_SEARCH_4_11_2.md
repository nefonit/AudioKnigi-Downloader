# PoleKnig author-search pagination — 4.11.2

PoleKnig has two different result surfaces:

1. the generic site search (`/?q=...`);
2. the dedicated author catalogue (`/authors/<id>?p=...`).

The generic search is not guaranteed to enumerate every audiobook belonging to an author. Version 4.11.2 detects author links whose visible author name matches the user's query, opens the dedicated author catalogue, follows its `p=` pagination, and adds those books to the PoleKnig results before narration grouping.

For example, the live PoleKnig catalogue for Leonid Filatov currently reports 20 audiobooks and has a second catalogue page. A surname search such as `Филатов` therefore must not rely on the first generic-search page alone.

Safety and limits remain unchanged: the application returns at most 100 PoleKnig results, does not bypass rights-holder restrictions, and still groups separate recording pages of one logical work into narration variants.
