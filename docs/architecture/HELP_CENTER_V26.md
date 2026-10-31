# V26 — Help Center content and UI ownership

The Help Center formerly placed four-language documentation and widget code in
one ~125 KB Python module. The long topic catalog and supplemental descriptions
now live in `audioknigi/qt/help_content.py`, which imports **no Qt toolkit**.

`audioknigi/qt/help_center.py` remains the public entry point and contains:
- `QtHelpCenter` and its accessible controls/dialog and keyboard focus behavior;
- the original HTML rich-text renderer `_format_help_body_html`;
- the existing copy-report callback and language/topic selection;
- backwards-compatible names `TOPICS`, `TOPICS_RU` and
  `ROUND55_TOPIC_DETAILS_*`, re-exported from the content module.

`help_content.py` owns both `TOPICS` and the `ROUND55_TOPIC_DETAILS`
dictionaries, without changing any topic string or key. It can be imported
without initializing or importing Qt.

## Regression boundaries

- The content coverage tests inspect the source data module rather than
  assuming that help text lives inside the widget implementation.
- Tests check the 16 stable topic keys and four languages, the additional
  details and the existing screen-reader instructions.
- Qt UI tests still inspect the dialog's `QSplitter`, row sizing,
  rich-text formatter, focus, accessibility identifiers, and callback.
- Older import paths are preserved. No download, search, networking or
  player behavior is touched.

The archived pre-refactor tests remain unchanged as historical evidence.
Any retired source-layout-only assertions must be explicitly reviewed by the
historical regression gate; unexpected runtime failures must not be waived.
