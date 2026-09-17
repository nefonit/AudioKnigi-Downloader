# AudioKnigi Downloader 4.12.31 — Help Center & visual keyboard focus

## Help Center
- Activating a topic with Enter/click immediately moves focus to the read-only topic document.
- The first paragraph is announced automatically through the active NVDA/JAWS Prism bridge.
- Up/Down read adjacent paragraphs; PageUp/PageDown move five paragraphs; Home/End jump to first/last paragraph.
- Shift+Tab returns to the currently selected topic button.
- Contextual F1 opens the corresponding topic button rather than always focusing the first help topic.

## Focus containment
Tab/Shift+Tab now traverse only controls in the active Toplevel. Help Center and dialogs can no longer send focus behind themselves into the main application window.

## Visual focus
- Every focusable native ttk control receives a separate 3px high-contrast yellow focus ring.
- Read-only Text controls use a 3px native highlight border.
- The indicator is managed by the accessibility layer and works whether or not a screen reader is running.

## Diagnostics/tests
Regression tests cover Help document speech, paragraph navigation, active-window focus containment, visual focus geometry and native Text highlight.
