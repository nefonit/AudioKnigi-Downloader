from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from audioknigi.app import AudioKnigiApp
from audioknigi.accessibility import AccessibilityManager
from audioknigi.library_visuals import LibraryVisualMixin
from audioknigi.models import Book, Track
from audioknigi.notifications import _windows_toast_script
from audioknigi.ui.settings_tab import SettingsTab
import audioknigi.logging_utils as logging_utils

ROOT = Path(__file__).resolve().parents[1]

# 1) app.py is complete and the localization helper really exists.
app_source = (ROOT / "audioknigi" / "app.py").read_text(encoding="utf-8")
compile(app_source, str(ROOT / "audioknigi" / "app.py"), "exec")
assert hasattr(AudioKnigiApp, "t")
assert "self.player_time_var" in app_source
assert "def restore_from_tray" in app_source

# 2) to_dict must not deepcopy native/Tk/PIL-like objects from cover_cache.
class _NoDeepcopy:
    def __deepcopy__(self, memo):
        raise RuntimeError("must not deepcopy")

book = Book(
    url="u",
    title="Book",
    tracks=[Track(index=1, title="01", file="f.mp3")],
    cover_cache=_NoDeepcopy(),
)
data = book.to_dict()
assert data["title"] == "Book"
assert data["tracks"][0]["index"] == 1
assert data["cover_cache"] is None
cover_payload = (b"jpeg-bytes", "image/jpeg")
assert Book(url="u", title="B", cover_cache=cover_payload).to_dict()["cover_cache"] == cover_payload

# 3) Empty cover tuple has an explicit fast-path rather than exception-driven flow.
mix = LibraryVisualMixin()
assert mix._photo_from_payload((), {}, "empty") is None
assert mix._payload_key("q", "id", ()) == "q:id:"
library_source = (ROOT / "audioknigi" / "library_visuals.py").read_text(encoding="utf-8")
assert "if not data:" in library_source

# 4) PowerShell toast uses explicit WinRT type notation for construction/showing.
script = _windows_toast_script("Title $(not-code)", "Message ` still text")
assert "Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom, ContentType = WindowsRuntime]::New()" in script
assert "Windows.UI.Notifications.ToastNotification, Windows.UI.Notifications, ContentType = WindowsRuntime]::New($doc)" in script
assert "Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime]::CreateToastNotifier" in script
assert "New-Object Windows.Data.Xml.Dom.XmlDocument" not in script
# User text is transported as Base64, never executable PowerShell source.
assert "$(not-code)" not in script

# 5) Privacy logging hides both Windows slash spellings of the home directory.
with mock.patch.object(logging_utils.Path, "home", return_value=logging_utils.Path(r"C:\Users\Serio")):
    masked_back = logging_utils.sanitize_log_text(r"C:\Users\Serio\Books\a.mp3")
    masked_forward = logging_utils.sanitize_log_text("C:/Users/Serio/Books/a.mp3")
assert "%USERPROFILE%" in masked_back and "Serio" not in masked_back
assert "%USERPROFILE%" in masked_forward and "Serio" not in masked_forward

# 6) Interrupted-queue restore uses typed QueueItem access and synchronizes normalization UI state.
storage_source = (ROOT / "audioknigi" / "storage.py").read_text(encoding="utf-8")
assert 'any(x.url == record["url"] for x in self.queue_items)' in storage_source
assert 'self._safe_set_ui_var("normalize_audio_var", normalization_mode != "off")' in storage_source

# 7) Removed output-format controls cannot drift from the MP3-only runtime.
st = SettingsTab.__new__(SettingsTab)
st.app = SimpleNamespace()
settings_source = (ROOT / "audioknigi" / "ui" / "settings_tab.py").read_text(encoding="utf-8")
assert "output_mode_var" not in settings_source
assert "_output_friendly_trace_id" not in settings_source

# Language combo intentionally stores display text; app accepts both display text and code.
assert 'raw if raw in LANGUAGES else' in app_source

# 8) Accessibility label discovery also understands CTkLabel-like visual labels.
class FakeCTkLabel:
    def cget(self, key):
        return "Адрес сервера:" if key == "text" else ""
    def winfo_class(self):
        return "CTkLabel"

assert AccessibilityManager._label_text(FakeCTkLabel()) == "Адрес сервера"

print("AUDIT 4.7.7 APP/I18N: OK")
print("AUDIT 4.7.7 MODEL/COVER SERIALIZATION: OK")
print("AUDIT 4.7.7 WINRT/PRIVACY: OK")
print("AUDIT 4.7.7 RESTORE/SETTINGS SYNC: OK")
print("AUDIT 4.7.7 ACCESSIBILITY LABELS: OK")
