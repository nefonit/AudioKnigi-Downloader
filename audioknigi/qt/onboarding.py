from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..core import DEFAULT_OUTPUT
from ..i18n import LANGUAGES, tr, ui_text
from .accessibility import configure_accessible, ensure_accessibility_tree
from .localized_context_menu import install_localized_text_context_menu


QUALITY_PRESETS = (
    ("standard", "Стандартное — оригинальное качество"),
    ("phone", "Для телефона — меньше размер"),
    ("normalize", "Выравнять громкость"),
)

_MODE_LABELS = (
    ("easy", "Простой"),
    ("advanced", "Расширенный"),
)

_ONBOARDING_TEXT = {
    "ru": {
        "title": "Добро пожаловать в AudioKnigi Downloader",
        "subtitle": "Выберите основные параметры. Всё остальное можно изменить позже в Настройках.",
        "language": "Язык интерфейса:",
        "folder": "Папка для аудиокниг:",
        "quality": "Качество по умолчанию:",
        "mode": "Режим интерфейса:",
        "browse": "Выбрать…",
        "start": "Сохранить и начать",
        "cancel": "Отмена",
        "quality_standard": "Стандартное — оригинальное качество",
        "quality_phone": "Для телефона — меньше размер",
        "quality_normalize": "Выравнять громкость",
        "mode_easy": "Простой",
        "mode_advanced": "Расширенный",
    },
    "uk": {
        "title": "Ласкаво просимо до AudioKnigi Downloader",
        "subtitle": "Оберіть основні параметри. Усе інше можна змінити пізніше в Налаштуваннях.",
        "language": "Мова інтерфейсу:",
        "folder": "Папка для аудіокниг:",
        "quality": "Якість за замовчуванням:",
        "mode": "Режим інтерфейсу:",
        "browse": "Обрати…",
        "start": "Зберегти й почати",
        "cancel": "Скасувати",
        "quality_standard": "Стандартна — оригінальна якість",
        "quality_phone": "Для телефона — менший розмір",
        "quality_normalize": "Вирівняти гучність",
        "mode_easy": "Простий",
        "mode_advanced": "Розширений",
    },
    "de": {
        "title": "Willkommen bei AudioKnigi Downloader",
        "subtitle": "Wähle die wichtigsten Einstellungen. Alles Weitere kannst du später in den Einstellungen ändern.",
        "language": "Oberflächensprache:",
        "folder": "Hörbuchordner:",
        "quality": "Standardqualität:",
        "mode": "Oberflächenmodus:",
        "browse": "Auswählen…",
        "start": "Speichern und starten",
        "cancel": "Abbrechen",
        "quality_standard": "Standard — Originalqualität",
        "quality_phone": "Fürs Smartphone — kleinere Dateien",
        "quality_normalize": "Lautstärke angleichen",
        "mode_easy": "Einfach",
        "mode_advanced": "Erweitert",
    },
    "en": {
        "title": "Welcome to AudioKnigi Downloader",
        "subtitle": "Choose the essential options. You can change everything else later in Settings.",
        "language": "Interface language:",
        "folder": "Audiobook folder:",
        "quality": "Default quality:",
        "mode": "Interface mode:",
        "browse": "Choose…",
        "start": "Save and start",
        "cancel": "Cancel",
        "quality_standard": "Standard — original quality",
        "quality_phone": "For phone — smaller files",
        "quality_normalize": "Normalize volume",
        "mode_easy": "Simple",
        "mode_advanced": "Advanced",
    },
}

_ONBOARDING_HINTS = {
    "ru": {"language": "Alt+стрелка вниз открывает список языков; стрелки меняют выбор.", "folder": "Введите папку, куда сохранять загруженные аудиокниги.", "browse": "Открыть выбор папки.", "quality": "Выберите качество звука по умолчанию.", "mode": "Выберите Простой режим для основного сценария или Расширенный для всех разделов."},
    "uk": {"language": "Alt+стрілка вниз відкриває список мов; стрілки змінюють вибір.", "folder": "Введіть папку, куди зберігати завантажені аудіокниги.", "browse": "Відкрити вибір папки.", "quality": "Оберіть якість звуку за замовчуванням.", "mode": "Оберіть Простий режим для основного сценарію або Розширений для всіх розділів."},
    "de": {"language": "Alt+Pfeil nach unten öffnet die Sprachliste; Pfeiltasten ändern die Auswahl.", "folder": "Ordner eingeben, in dem heruntergeladene Hörbücher gespeichert werden.", "browse": "Ordnerauswahl öffnen.", "quality": "Standard-Audioqualität auswählen.", "mode": "Einfach für den Hauptablauf oder Erweitert für alle Bereiche auswählen."},
    "en": {"language": "Alt+Down opens the language list; arrow keys change the selection.", "folder": "Enter the folder where downloaded audiobooks should be saved.", "browse": "Open a folder picker.", "quality": "Choose the default audio quality.", "mode": "Choose Simple for the main flow or Advanced for all sections."},
}


class QtFirstRunWizard(QDialog):
    """Single-screen, accessible first-run setup.

    The class name is intentionally preserved for compatibility with the release
    parity contract, but the old multi-page first-run assistant has been replaced by one
    compact decision screen.  It avoids the disabled Next/Finish controls and
    white empty pages seen in the Windows build while preserving the same saved
    settings keys.
    """

    def __init__(self, parent=None, *, settings: dict | None = None):
        super().__init__(parent)
        self.settings = dict(settings or {})
        self._language = str(self.settings.get("language", "ru") or "ru")
        if self._language not in LANGUAGES:
            self._language = "ru"
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setModal(True)
        self.setMinimumWidth(620)
        self.setMaximumWidth(760)
        configure_accessible(
            self,
            name=_ONBOARDING_TEXT[self._language]["title"],
            description=_ONBOARDING_TEXT[self._language]["subtitle"],
            identifier="first_run_wizard",
        )
        self._build()
        self._retranslate()
        ensure_accessibility_tree(self)

    def _build(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(26, 24, 26, 22)
        outer.setSpacing(14)

        self.title_label = QLabel()
        self.title_label.setObjectName("pageTitle")
        self.title_label.setWordWrap(True)
        outer.addWidget(self.title_label)

        self.subtitle_label = QLabel()
        self.subtitle_label.setObjectName("onboardingSubtitle")
        self.subtitle_label.setWordWrap(True)
        outer.addWidget(self.subtitle_label)

        form = QFormLayout()
        form.setHorizontalSpacing(16)
        form.setVerticalSpacing(12)
        outer.addLayout(form)

        self.language_combo = QComboBox()
        for code, label in LANGUAGES.items():
            self.language_combo.addItem(label, code)
        idx = self.language_combo.findData(self._language)
        self.language_combo.setCurrentIndex(max(0, idx))
        configure_accessible(
            self.language_combo,
            name=tr(self._language, "language"),
            description=_ONBOARDING_HINTS[self._language]["language"],
            identifier="wizard_language",
        )
        self.language_combo.currentIndexChanged.connect(self._language_changed)
        self.language_label = QLabel()
        self.language_label.setBuddy(self.language_combo)
        form.addRow(self.language_label, self.language_combo)

        folder_holder = QWidget(self)
        folder_row = QHBoxLayout(folder_holder)
        folder_row.setContentsMargins(0, 0, 0, 0)
        folder_row.setSpacing(8)
        self.folder_edit = QLineEdit(str(self.settings.get("output_dir", DEFAULT_OUTPUT) or DEFAULT_OUTPUT))
        install_localized_text_context_menu(self.folder_edit, lambda: self._language)
        configure_accessible(
            self.folder_edit,
            name=ui_text(self._language, "Папка для аудиокниг"),
            description=_ONBOARDING_HINTS[self._language]["folder"],
            identifier="wizard_output_dir",
        )
        self.browse_button = QPushButton()
        configure_accessible(
            self.browse_button,
            name=ui_text(self._language, "Выбрать папку для аудиокниг"),
            description=_ONBOARDING_HINTS[self._language]["browse"],
            identifier="wizard_choose_folder",
        )
        self.browse_button.clicked.connect(self._choose_folder)
        folder_row.addWidget(self.folder_edit, 1)
        folder_row.addWidget(self.browse_button)
        self.folder_label = QLabel()
        self.folder_label.setBuddy(self.folder_edit)
        form.addRow(self.folder_label, folder_holder)

        self.quality_combo = QComboBox()
        for value, _label in QUALITY_PRESETS:
            self.quality_combo.addItem("", value)
        quality = str(self.settings.get("quality_preset", "standard") or "standard")
        self.quality_combo.setCurrentIndex(max(0, self.quality_combo.findData(quality)))
        configure_accessible(
            self.quality_combo,
            name=ui_text(self._language, "Качество"),
            description=_ONBOARDING_HINTS[self._language]["quality"],
            identifier="wizard_quality",
        )
        self.quality_label = QLabel()
        self.quality_label.setBuddy(self.quality_combo)
        form.addRow(self.quality_label, self.quality_combo)

        self.mode_combo = QComboBox()
        for value, _label in _MODE_LABELS:
            self.mode_combo.addItem("", value)
        saved_mode = str(self.settings.get("ui_mode", "easy") or "easy")
        self.mode_combo.setCurrentIndex(max(0, self.mode_combo.findData(saved_mode)))
        configure_accessible(
            self.mode_combo,
            name=ui_text(self._language, "Режим интерфейса"),
            description=_ONBOARDING_HINTS[self._language]["mode"],
            identifier="wizard_ui_mode",
        )
        self.mode_label = QLabel()
        self.mode_label.setBuddy(self.mode_combo)
        form.addRow(self.mode_label, self.mode_combo)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        self.cancel_button = QPushButton()
        configure_accessible(self.cancel_button, identifier="wizard_cancel")
        self.cancel_button.clicked.connect(self.reject)
        self.start_button = QPushButton()
        self.start_button.setProperty("role", "primary")
        self.start_button.setMinimumWidth(180)
        configure_accessible(self.start_button, identifier="wizard_finish")
        self.start_button.clicked.connect(self.accept)
        buttons.addWidget(self.cancel_button)
        buttons.addWidget(self.start_button)
        outer.addLayout(buttons)

    def _text(self, key: str) -> str:
        return _ONBOARDING_TEXT.get(self._language, _ONBOARDING_TEXT["ru"]).get(key, key)

    def _language_changed(self, _index: int) -> None:
        code = str(self.language_combo.currentData() or "ru")
        self._language = code if code in LANGUAGES else "ru"
        self._retranslate()

    def _retranslate(self) -> None:
        self.setWindowTitle(self._text("title"))
        self.setAccessibleName(self._text("title"))
        self.setAccessibleDescription(self._text("subtitle"))
        self.title_label.setText(self._text("title"))
        self.subtitle_label.setText(self._text("subtitle"))
        self.language_label.setText(self._text("language"))
        self.folder_label.setText(self._text("folder"))
        self.quality_label.setText(self._text("quality"))
        self.mode_label.setText(self._text("mode"))
        self.browse_button.setText(self._text("browse"))
        self.cancel_button.setText(self._text("cancel"))
        self.start_button.setText(self._text("start"))
        self.cancel_button.setAccessibleName(self._text("cancel"))
        self.cancel_button.setAccessibleDescription("")
        self.start_button.setAccessibleName(self._text("start"))
        self.start_button.setAccessibleDescription("")
        hints = _ONBOARDING_HINTS.get(self._language, _ONBOARDING_HINTS["ru"])
        self.language_combo.setAccessibleName(self._text("language").rstrip(":"))
        self.language_combo.setAccessibleDescription(hints["language"])
        self.folder_edit.setAccessibleName(self._text("folder").rstrip(":"))
        self.folder_edit.setAccessibleDescription(hints["folder"])
        self.browse_button.setAccessibleName(ui_text(self._language, "Выбрать папку для аудиокниг"))
        self.browse_button.setAccessibleDescription(hints["browse"])
        self.quality_combo.setAccessibleName(self._text("quality").rstrip(":"))
        self.quality_combo.setAccessibleDescription(hints["quality"])
        self.mode_combo.setAccessibleName(self._text("mode").rstrip(":"))
        self.mode_combo.setAccessibleDescription(hints["mode"])
        quality_texts = {
            "standard": self._text("quality_standard"),
            "phone": self._text("quality_phone"),
            "normalize": self._text("quality_normalize"),
        }
        for index in range(self.quality_combo.count()):
            value = str(self.quality_combo.itemData(index) or "")
            self.quality_combo.setItemText(index, quality_texts.get(value, value))
        mode_texts = {"easy": self._text("mode_easy"), "advanced": self._text("mode_advanced")}
        for index in range(self.mode_combo.count()):
            value = str(self.mode_combo.itemData(index) or "")
            self.mode_combo.setItemText(index, mode_texts.get(value, value))

    def _choose_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            self,
            self._text("folder").rstrip(":"),
            self.folder_edit.text() or str(DEFAULT_OUTPUT),
        )
        if folder:
            self.folder_edit.setText(folder)

    def result_settings(self) -> dict:
        language = str(self.language_combo.currentData() or "ru")
        quality = str(self.quality_combo.currentData() or "standard")
        mode = str(self.mode_combo.currentData() or "easy")
        result = dict(self.settings)
        result.update({
            "language": language if language in LANGUAGES else "ru",
            "output_dir": self.folder_edit.text().strip() or str(DEFAULT_OUTPUT),
            "quality_preset": quality,
            "ui_mode": "easy" if mode == "easy" else "advanced",
            "first_run_complete": True,
        })
        if quality == "phone":
            result.update({"audio_preset": "64k_mono", "normalization_mode": "off"})
        elif quality == "normalize":
            result.update({"audio_preset": "128k_stereo", "normalization_mode": "two_pass"})
        else:
            result.update({"audio_preset": "copy", "normalization_mode": "off"})
        return result


__all__ = ["QtFirstRunWizard", "QUALITY_PRESETS"]
