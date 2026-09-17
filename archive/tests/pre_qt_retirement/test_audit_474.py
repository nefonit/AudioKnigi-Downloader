from __future__ import annotations

import base64
import re
import tempfile
import threading
from pathlib import Path
from types import SimpleNamespace

from audioknigi import core
from audioknigi.integrations import _base
from audioknigi.logging_utils import sanitize_log_text
from audioknigi.models import Book, Track
from audioknigi.notifications import _windows_toast_script
from audioknigi.onboarding import FirstRunWizard
from audioknigi.player import PlayerMixin
from audioknigi.storage import StorageMixin
from audioknigi.templates import render_folder, template_values
from audioknigi.ui.settings_tab import SettingsTab
from audioknigi.ui_kit import Tooltip

ROOT = Path(__file__).resolve().parents[1]


class Var:
    def __init__(self, value=None):
        self.value = value
    def get(self):
        return self.value
    def set(self, value):
        self.value = value


# 1) Model mapping exposes only declared dataclass fields, never methods/class attrs.
book = Book(url="https://audioknigi.com.ua/test", title="Book")
assert book["title"] == "Book"
assert book.get("to_dict") is None
try:
    _ = book["to_dict"]
except KeyError:
    pass
else:
    raise AssertionError("MappingDataclass must not expose methods as mapping keys")

# 2) Main-tab context menu has an explicit widget master; dnd.py is complete.
main_source = (ROOT / "audioknigi" / "ui" / "main_tab.py").read_text(encoding="utf-8")
assert "tk.Menu(app.tree" in main_source and "tk.Menu(app," not in main_source
compile((ROOT / "audioknigi" / "dnd.py").read_text(encoding="utf-8"), "dnd.py", "exec")

# 3) Book/Track typed runtime access remains clean and disk helper really exists.
actions_source = (ROOT / "audioknigi" / "actions.py").read_text(encoding="utf-8")
for token in ("current_book.get(", "book.get(", "track.get(", 'book["tracks"]', 'track["'):
    assert token not in actions_source, token
from audioknigi.downloader import DownloaderMixin
assert callable(getattr(DownloaderMixin, "_disk_free_for_path", None))

# 4) None HTML is safe.
assert core.extract_metadata_from_html(None, "fallback") == ("fallback", "", "")

# 5) Resource path in source mode points at project-root assets.
assert core.resource_path("assets", "app_icon.png").is_file()

# 6) Audiobookshelf addresses without a scheme become ordinary HTTP URLs.
assert _base("demo.local:13378") == "http://demo.local:13378"
assert _base("https://demo.local/") == "https://demo.local"
try:
    _base("ftp://demo.local")
except ValueError:
    pass
else:
    raise AssertionError("non-http Audiobookshelf URLs must be rejected")

# 7) PowerShell code never contains raw notification text.
malicious = 'Book $(Start-Process calc) `" $env:USERPROFILE'
script = _windows_toast_script(malicious, malicious)
assert malicious not in script
payload = re.search(r"FromBase64String\('([^']+)'\)", script).group(1)
xml = base64.b64decode(payload).decode("utf-8")
assert "$(Start-Process calc)" in xml  # preserved as text inside XML payload only

# 8) Wizard X/cancel means skip onboarding and remembers that choice.
class FakeWin:
    def __init__(self): self.destroyed = False
    def grab_release(self): pass
    def destroy(self): self.destroyed = True
class FakeWizardApp:
    def __init__(self): self.settings = {}; self.after_called = False; self.saved = None
    def _save_settings(self, extra=None): self.saved = dict(extra or {})
    def _after_onboarding(self): self.after_called = True
wiz = FirstRunWizard.__new__(FirstRunWizard)
wiz.app = FakeWizardApp(); wiz.win = FakeWin()
wiz.cancel()
assert wiz.app.settings.get("first_run_complete") is True
assert wiz.app.saved == {"first_run_complete": True}
assert wiz.win.destroyed and wiz.app.after_called

# 9) Friendly speed label follows manual advanced segment count.
class FakeSettingsApp:
    def __init__(self): self.segment_count_var = Var("2")
st = SettingsTab.__new__(SettingsTab)
st.app = FakeSettingsApp(); st.speed_var = Var("old")
st._sync_speed_from_segment_count()
assert st.speed_var.get().startswith("Максимальная")
st.app.segment_count_var.set("1"); st._sync_speed_from_segment_count()
assert st.speed_var.get() == "Обычная"

# 10) Queue/search StringVars are owned by app and builders only initialize if missing.
app_source = (ROOT / "audioknigi" / "app.py").read_text(encoding="utf-8")
queue_source = (ROOT / "audioknigi" / "ui" / "queue_tab.py").read_text(encoding="utf-8")
search_source = (ROOT / "audioknigi" / "ui" / "search_tab.py").read_text(encoding="utf-8")
assert "self.queue_url_var = tk.StringVar()" in app_source
assert "self.search_query_var = tk.StringVar()" in app_source
assert 'ensure_app_string_var(self.app, self.frame, name, default)' in queue_source
assert 'ensure_app_string_var(self.app, self.frame, name, default)' in search_source
assert 'show="tree headings"' in queue_source
assert 'show="tree headings"' in (ROOT / "audioknigi" / "ui" / "history_tab.py").read_text(encoding="utf-8")

# 11) Unmap handler filters child events.
class BoolVar:
    def get(self): return True
class FakeUnmap:
    minimize_to_tray_var = BoolVar(); queue_running = True
    def __init__(self): self.calls = []
    def after(self, ms, cb): self.calls.append((ms, cb))
    def _maybe_hide_to_tray(self): pass
fake = FakeUnmap()
from audioknigi.app import AudioKnigiApp
AudioKnigiApp._on_unmap(fake, SimpleNamespace(widget=object()))
assert not fake.calls
AudioKnigiApp._on_unmap(fake, SimpleNamespace(widget=fake))
assert len(fake.calls) == 1

# 12) Player position snapshots/lock are safe across threads and initialize once.
class FakePlayer(PlayerMixin):
    def __init__(self): self.player_positions = {}
fp = FakePlayer()
locks = []
def get_lock(): locks.append(fp._player_positions_lock())
threads = [threading.Thread(target=get_lock) for _ in range(16)]
for t in threads: t.start()
for t in threads: t.join()
assert len({id(x) for x in locks}) == 1
with fp._player_positions_lock():
    fp.player_positions["a"] = {"position": 1}
assert fp._player_positions_snapshot()["a"]["position"] == 1

# 13) Corrupt bandwidth_limit no longer blocks settings restore.
class FakeStorage(StorageMixin):
    def __init__(self):
        self.settings = {"bandwidth_limit": "not-a-number"}
        self.bandwidth_limit_var = Var(99)
        self.language = "ru"
fs = FakeStorage(); fs._apply_settings_to_ui()
assert fs.bandwidth_limit_var.get() == 0.0

# 14) Template edge cases: title 0 is kept and invalid folder data never returns base.
vals = template_values(Book(url="u", title="B"), {"index": 1, "title": 0})
assert vals["Track_Title"] == "0"
with tempfile.TemporaryDirectory() as td:
    base = Path(td)
    folder = render_folder(base, "???", Book(url="u", title="???"))
    assert folder != base and folder.is_dir()

# 15) Logging masks secrets/URLs while preserving separators under normal home dirs.
clean = sanitize_log_text("token=SECRET https://example.org/?password=abc")
assert "SECRET" not in clean and "example.org" not in clean

# 16) Search worker's status helper is thread-safe because set_status posts to UI bus.
set_status_block = re.search(r"def set_status\(self, text\):(.*?)(?=\n    def )", actions_source, re.S).group(1)
assert "self.ui(apply)" in set_status_block

# 17) Native compatibility mappings and Tooltip destroy filter are present.
ui_source = (ROOT / "audioknigi" / "ui_kit.py").read_text(encoding="utf-8")
assert 'kwargs["orient"] = orientation' in ui_source
assert 'kwargs["compound"] = compound' in ui_source
assert "def get(self):" in ui_source

class FakeWidget:
    def __init__(self): self.exists = True
    def bind(self, *_a, **_k): pass
    def winfo_exists(self): return self.exists
    def after_cancel(self, _x): pass
fw = FakeWidget(); tip = Tooltip(fw, "x")
class Tip:
    def __init__(self): self.destroyed = False
    def destroy(self): self.destroyed = True
child_tip = Tip(); tip._tip = child_tip
tip._on_destroy(SimpleNamespace(widget=object()))
assert not child_tip.destroyed
fw.exists = False
tip._on_destroy(SimpleNamespace(widget=object()))
assert child_tip.destroyed

print("AUDIT 4.7.4 MODELS/UI: OK")
print("AUDIT 4.7.4 NETWORK/NOTIFICATIONS: OK")
print("AUDIT 4.7.4 PLAYER/STORAGE: OK")
print("AUDIT 4.7.4 TEMPLATES/FALLBACK: OK")
