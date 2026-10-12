"""Independent regression tests for newly reproduced Round 90 defects."""

import json
import math
from decimal import Decimal
from fractions import Fraction

import pytest

from audioknigi.logging_utils import sanitize_log_text
from audioknigi.services.download_request import DownloadRequest
from audioknigi.services.player_position_store import PlayerPositionStore


@pytest.mark.parametrize("line,secret", [
    ("Authorization: Bearer TOP.SECRET-123", "TOP.SECRET-123"),
    ("Authorization: Basic dXNlcjpwYXNz", "dXNlcjpwYXNz"),
    ("Proxy-Authorization: Bearer specialtoken", "specialtoken"),
    ("Cookie: sid=ABC; auth=SECRETTWO", "SECRETTWO"),
    ("Set-Cookie: session=SECRET; Path=/; HttpOnly", "SECRET"),
])
def test_log_headers_never_expose_credentials(line, secret):
    sanitized = sanitize_log_text(line)
    assert secret not in sanitized
    assert "<hidden>" in sanitized


def test_log_redaction_preserves_next_line():
    output = sanitize_log_text("Authorization: Bearer TOP.SECRET-123\nNext: retries exhausted")
    assert "TOP.SECRET-123" not in output
    assert "Next: retries exhausted" in output


@pytest.mark.parametrize("index", [1.1, 2.99, -0.2, float("inf"), float("nan"), Decimal("2.7"), Fraction(5, 2)])
def test_fractional_or_nonfinite_track_indices_rejected(index):
    with pytest.raises(ValueError):
        DownloadRequest.track_index(index)


def test_integer_float_track_index_is_still_accepted():
    assert DownloadRequest.track_index(2.0) == 2


def test_inf_resume_position_never_saved(tmp_path):
    path = tmp_path / "player_positions.json"
    store = PlayerPositionStore(path)
    store.update("chapter.mp3", math.inf, duration=0)
    assert store.saved_seconds("chapter.mp3") == 0
    assert "Infinity" not in path.read_text(encoding="utf-8")
    json.loads(path.read_text(encoding="utf-8"), parse_constant=lambda s: (_ for _ in ()).throw(ValueError(s)))


def test_inf_from_legacy_position_file_never_restored(tmp_path):
    path = tmp_path / "player_positions.json"
    key = PlayerPositionStore.key("chapter.mp3")
    path.write_text(json.dumps({key: {"position": math.inf, "duration": 0}}))
    store = PlayerPositionStore(path)
    assert store.saved_seconds("chapter.mp3") == 0


def test_inf_duration_never_saved(tmp_path):
    path = tmp_path / "player_positions.json"
    store = PlayerPositionStore(path)
    store.update("chapter.mp3", 20, duration=math.inf)
    assert "Infinity" not in path.read_text(encoding="utf-8")
