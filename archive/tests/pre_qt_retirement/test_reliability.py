import json
import tempfile
import threading
from pathlib import Path

from audioknigi.i18n import LANGUAGES, tr
from audioknigi.crash_report import build_report
from audioknigi.core import SiteStructureChanged
import audioknigi.player as player_module
from audioknigi.player import PlayerMixin

for code in LANGUAGES:
    assert tr(code, 'download_book')
assert 'ЗАВАНТАЖИТИ' in tr('uk', 'download_book')
assert 'HERUNTERLADEN' in tr('de', 'download_book')
assert 'DOWNLOAD' in tr('en', 'download_book')

try:
    raise RuntimeError('token=supersecret https://example.com/private ' + str(Path.home() / 'secret.txt'))
except RuntimeError as exc:
    report = build_report(type(exc), exc, exc.__traceback__, component='smoketest')
assert 'supersecret' not in report
assert 'https://example.com' not in report
assert '%USERPROFILE%' in report

class Var:
    def __init__(self, value=0): self.value=value
    def get(self): return self.value
    def set(self, value): self.value=value

class FakePlayer(PlayerMixin):
    pass

with tempfile.TemporaryDirectory() as td:
    player_module.PLAYER_POSITIONS_FILE = Path(td) / 'positions.json'
    audio = Path(td) / '01.mp3'; audio.write_bytes(b'abc')
    fake = FakePlayer(); fake.player_positions={}; fake.player_file=audio
    fake.player_position_var=Var(5824.0); fake.player_duration=9000.0
    fake._player_positions_write_lock=threading.Lock(); fake._player_positions_write_thread=None; fake._pending_player_positions=None
    fake._save_current_player_position(force=True)
    thread = fake._player_positions_write_thread
    if thread is not None: thread.join(1.0)
    data=json.loads(player_module.PLAYER_POSITIONS_FILE.read_text(encoding='utf-8'))
    assert data and abs(next(iter(data.values()))['position'] - 5824.0) < 0.1
    fake.player_positions=data
    assert abs(fake._saved_player_position(audio)-5824.0) < 0.1
    fake.player_position_var.set(6000.0)
    fake._save_current_player_position(force=True, sync=True)
    data2=json.loads(player_module.PLAYER_POSITIONS_FILE.read_text(encoding='utf-8'))
    assert abs(next(iter(data2.values()))['position'] - 6000.0) < 0.1

assert issubclass(SiteStructureChanged, RuntimeError)
print('I18N RU/UK/DE/EN: OK')
print('PRIVACY-SAFE CRASH REPORT: OK')
print('PLAYER POSITION PERSISTENCE: OK')
print('SITE STRUCTURE ERROR TYPE: OK')
print('RELIABILITY SMOKETEST: OK')
