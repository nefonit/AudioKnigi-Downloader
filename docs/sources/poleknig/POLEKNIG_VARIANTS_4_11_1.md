# PoleKnig narration variants — 4.11.1

Version 4.11.1 fixes manual analysis of PoleKnig pages whose current recording was removed by a rights holder.

## What changed

- The app extracts the book author link from the PoleKnig detail page.
- It scans the author's public catalogue (including pagination, up to a conservative limit).
- Candidate pages are matched by the same author and a normalized logical title.
- Presentation prefixes such as `Сказ про` and `Пьеса: Сказ про` are treated as the same work as `Про ...` when the remaining title matches.
- Every candidate detail page is checked before it is shown. Alternatives that are themselves marked `Удалено правообладателем` are excluded.
- The current restricted page stays visible in the narration selector so the user can see which recording was originally requested.

## Example

For `https://poleknig.com/books/147736` the current Leonid Filatov recording is rights-restricted. The app can discover another page for the same work under the title `Сказ про Федота-стрельца, удалого молодца` and expose that reader in the `Озвучка` selector when the alternative page is not rights-restricted.

## Validation

- `compileall`: OK
- CI self-test: 4.11.1 OK
- Full regression suite: 241 passed
