"""V32 checksums and corruption recovery for resumable Range segments."""

from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
import json
from pathlib import Path
import threading

import pytest

from audioknigi.download import segment_integrity
from audioknigi.download.book_flow import BookFlowMixin
from audioknigi.download.network import NetworkDownloadMixin
from audioknigi.download.segment_integrity import (
    SegmentChecksums, copy_verified_segment, file_digest,
)


URL = "https://cdn.invalid/book.mp3"
PAYLOAD = b"abcdefgh"


def _paths(tmp_path):
    target = tmp_path / "_source.mp3"
    part = Path(str(target) + ".part")
    seg0 = Path(str(part) + ".seg000")
    seg1 = Path(str(part) + ".seg001")
    geometry = {
        "version": 1,
        "url": URL,
        "total_size": 8,
        "task_count": 2,
        "ranges": [[0, 3], [4, 7]],
    }
    meta = Path(str(part) + ".segments.json")
    checksums = Path(str(part) + ".segments.sha256.json")
    return target, seg0, seg1, meta, checksums, geometry


def _seed(tmp_path, *, first=b"abcd", second=b"efgh"):
    target, seg0, seg1, meta, hashes, geometry = _paths(tmp_path)
    meta.write_text(json.dumps(geometry), encoding="utf-8")
    proof = SegmentChecksums(hashes, geometry)
    if first is not None:
        seg0.write_bytes(first)
        proof.record(seg0)
    if second is not None:
        seg1.write_bytes(second)
        proof.record(seg1)
    return target, seg0, seg1, meta, hashes, proof


class Harness(NetworkDownloadMixin):
    runtime_segment_count = "2"
    runtime_bandwidth_limit = 0.0
    runtime_auto_chunk_min_kbytes_per_sec = 256
    cancel_event = None
    _suppress_source_transfer_ui = True

    def __init__(self, payload=PAYLOAD, *, fail_once=False):
        self.payload = payload
        self.fail_once = fail_once
        self.calls = []
        self.guard = threading.Lock()

    def _check_cancel(self):
        pass

    def _download_segment(self, _url, seg_path, start, end, _referer, callback, peer_abort_event=None):
        seg = Path(seg_path)
        existing = seg.stat().st_size if seg.exists() else 0
        with self.guard:
            self.calls.append((start, end, existing))
            fail_here = self.fail_once and start == 0
            if fail_here:
                self.fail_once = False
        new_data = self.payload[start + existing:end + 1]
        if fail_here:
            new_data = new_data[:1]
        with open(seg, "ab") as out:
            out.write(new_data)
        callback(len(new_data), force=True)
        if fail_here:
            raise RuntimeError("simulated interrupted download")
        return end - start + 1

    def _cancel_active_network_io(self):
        pass

    def set_progress(self, *_args):
        pass

    def set_status(self, *_args):
        pass

    def record_transfer_metrics(self, *_args):
        pass

    def log(self, *_args):
        pass


def test_ledger_detects_same_size_disk_corruption_and_invalid_metadata(tmp_path):
    _, seg0, _, _, hashes, geometry = _paths(tmp_path)
    seg0.write_bytes(b"abcd")
    proofs = SegmentChecksums(hashes, geometry)
    assert not proofs.matches(seg0)
    proofs.record(seg0)
    assert proofs.matches(seg0)
    seg0.write_bytes(b"zzzz")
    assert not proofs.matches(seg0)
    assert not SegmentChecksums(hashes, {**geometry, "url": "other"}).matches(seg0)
    hashes.write_text("broken-json", encoding="utf-8")
    assert not SegmentChecksums(hashes, geometry).matches(seg0)


def test_checkpoints_written_atomically_by_parallel_workers(tmp_path):
    _, seg0, seg1, _, hashes, geometry = _paths(tmp_path)
    seg0.write_bytes(b"abcd")
    seg1.write_bytes(b"efgh")
    proof = SegmentChecksums(hashes, geometry)
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(proof.record, [seg0, seg1]))
    loaded = SegmentChecksums(hashes, geometry)
    assert loaded.matches(seg0) and loaded.matches(seg1)
    assert len(json.loads(hashes.read_text(encoding="utf-8"))["segments"]) == 2


def test_checked_copy_rejects_changed_bytes_and_wrong_lengths(tmp_path):
    seg = tmp_path / "segment"
    seg.write_bytes(b"abcd")
    size, digest = file_digest(seg)
    out = BytesIO()
    with open(seg, "rb") as inp:
        copy_verified_segment(inp, out, expected_size=size,
                              expected_sha256=digest, name=seg.name)
    assert out.getvalue() == b"abcd"
    seg.write_bytes(b"wxyz")
    with open(seg, "rb") as inp:
        with pytest.raises(RuntimeError, match="контрольная сумма"):
            copy_verified_segment(inp, BytesIO(), expected_size=size,
                                  expected_sha256=digest, name=seg.name)
    seg.write_bytes(b"abcdef")
    with open(seg, "rb") as inp:
        with pytest.raises(RuntimeError, match="увеличился"):
            copy_verified_segment(inp, BytesIO(), expected_size=size,
                                  expected_sha256=digest, name=seg.name)


def test_known_good_segments_are_reused_without_network(monkeypatch, tmp_path):
    target, seg0, seg1, meta, hashes, _ = _seed(tmp_path)
    harness = Harness()
    assert harness._download_segmented(URL, target, "", 8, 2) == target
    assert target.read_bytes() == PAYLOAD
    assert harness.calls == []
    assert not seg0.exists() and not seg1.exists()
    assert not meta.exists() and not hashes.exists()


def test_corrupt_same_size_cached_segment_is_redownloaded(monkeypatch, tmp_path):
    target, seg0, _, _, _, _ = _seed(tmp_path)
    seg0.write_bytes(b"XXXX")
    harness = Harness()
    assert harness._download_segmented(URL, target, "", 8, 2) == target
    assert target.read_bytes() == PAYLOAD
    assert harness.calls == [(0, 3, 0)]


def test_legacy_unverified_partial_is_not_silently_reused(tmp_path):
    target, seg0, seg1, meta, hashes, _ = _seed(tmp_path)
    hashes.unlink()
    harness = Harness()
    assert harness._download_segmented(URL, target, "", 8, 2) == target
    assert target.read_bytes() == PAYLOAD
    assert sorted((s, e, offset) for s, e, offset in harness.calls) == [
        (0, 3, 0), (4, 7, 0),
    ]


def test_verified_partial_resumes_at_saved_offset(tmp_path):
    target, seg0, _, _, _, _ = _seed(tmp_path, first=b"ab")
    harness = Harness()
    assert harness._download_segmented(URL, target, "", 8, 2) == target
    assert target.read_bytes() == PAYLOAD
    assert harness.calls == [(0, 3, 2)]


def test_worker_failure_checkpoints_valid_partial_for_next_run(tmp_path):
    target, seg0, seg1, meta, hashes, _ = _paths(tmp_path)
    harness = Harness(fail_once=True)
    with pytest.raises(RuntimeError, match="simulated interrupted download"):
        harness._download_segmented(URL, target, "", 8, 2)
    assert seg0.read_bytes() == b"a"
    proof = SegmentChecksums(hashes, _paths(tmp_path)[-1])
    assert proof.matches(seg0)
    retry = Harness()
    assert retry._download_segmented(URL, target, "", 8, 2) == target
    assert target.read_bytes() == PAYLOAD
    assert (0, 3, 1) in retry.calls


def test_changed_file_during_assembly_never_replaces_existing_final(monkeypatch, tmp_path):
    target, seg0, _, _, hashes, _ = _paths(tmp_path)
    target.write_bytes(b"original-final")
    orig_record = segment_integrity.SegmentChecksums.record

    def record_then_corrupt(self, path):
        orig_record(self, path)
        path = Path(path)
        if path.name.endswith("seg000"):
            path.write_bytes(b"ZZZZ")

    monkeypatch.setattr(segment_integrity.SegmentChecksums, "record", record_then_corrupt)
    with pytest.raises(RuntimeError, match="контрольная сумма"):
        Harness()._download_segmented(URL, target, "", 8, 2)
    assert target.read_bytes() == b"original-final"
    assert not Path(str(target) + ".part.assembling").exists()
    assert hashes.exists()
    assert seg0.read_bytes() == b"ZZZZ"

    monkeypatch.setattr(segment_integrity.SegmentChecksums, "record", orig_record)
    retry = Harness()
    assert retry._download_segmented(URL, target, "", 8, 2) == target
    assert target.read_bytes() == PAYLOAD
    assert (0, 3, 0) in retry.calls


def test_engine_cleanup_removes_checksum_sidecar_not_unrelated_files(tmp_path):
    target, _, _, _, hashes, _ = _seed(tmp_path)
    extra = tmp_path / "user-notes.txt"
    extra.write_text("keep")
    harness = Harness()
    harness._cleanup_partial_download(target)
    assert not hashes.exists()
    assert extra.read_text() == "keep"


def test_expired_media_source_cleanup_recognizes_new_owned_sidecar(tmp_path):
    target, _, _, _, hashes, _ = _seed(tmp_path)
    unowned = tmp_path / "_source notes.mp3.part.segments.sha256.json"
    unowned.write_text("user")
    class Flow(BookFlowMixin):
        def _book_folder(self, _book, create=False):
            return tmp_path
        def log(self, *_args):
            pass
    count = Flow()._clear_stale_source_downloads(object())
    assert count >= 1
    assert not hashes.exists()
    assert unowned.read_text() == "user"
