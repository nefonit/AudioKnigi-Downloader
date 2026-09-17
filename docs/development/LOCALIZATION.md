# Localization

Stable message IDs are stored in `audioknigi/locales/messages.json` and translated with `i18n.tr()` / `i18n.message()`.

Legacy Russian literals are isolated in `legacy_literals.json` and translated through `ui_text()` for compatibility.
New features should prefer stable IDs so wording can change without changing lookup keys.
