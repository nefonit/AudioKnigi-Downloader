import json
import zipfile

from audioknigi.diagnostics import create_support_bundle, sanitized_settings


def test_sanitized_settings_redacts_secrets():
    result = sanitized_settings({"abs_api_key": "secret", "language": "ru", "geometry": "blob"})
    assert result["abs_api_key"] == "<redacted>"
    assert result["language"] == "ru"
    assert result["geometry"] == "<window-geometry>"


def test_support_bundle_contains_no_secret_value(tmp_path):
    target = create_support_bundle(tmp_path / "support.zip", settings={"abs_api_key": "TOPSECRET", "language": "en"})
    with zipfile.ZipFile(target) as zf:
        names = set(zf.namelist())
        assert "diagnostics/environment.json" in names
        assert "diagnostics/settings.sanitized.json" in names
        combined = b"\n".join(zf.read(name) for name in names)
    assert b"TOPSECRET" not in combined


def test_sanitized_settings_hides_urls_and_shortens_paths(tmp_path, monkeypatch):
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
    result = sanitized_settings({
        "abs_url": "https://nas.local:13378",
        "output_dir": str(tmp_path / "Books"),
    })
    assert result["abs_url"] == "<configured-url>"
    assert result["output_dir"].startswith("~")


def test_support_bundle_does_not_include_queue_titles(tmp_path, monkeypatch):
    from audioknigi.diagnostics import support_bundle
    queue_file = tmp_path / "queue.json"
    queue_file.write_text('[{"id":"1","title":"PRIVATE BOOK","status_code":"pending"}]', encoding="utf-8")
    monkeypatch.setattr(support_bundle, "QT_QUEUE_FILE", queue_file)
    target = create_support_bundle(tmp_path / "support.zip", settings={"language":"en"})
    with zipfile.ZipFile(target) as zf:
        combined = b"\n".join(zf.read(name) for name in zf.namelist())
    assert b"PRIVATE BOOK" not in combined
