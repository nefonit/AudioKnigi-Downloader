# Shared-source recovery audit — 4.12.31

## Trigger

A real frozen Windows run on 2026-09-06 exposed a repeatable failure while downloading **«Подрыгин Иван - Сталкер 2.0»** from `audioknigi.com.ua`.

The public playlist described four cuts on one shared MP3 source:

- part 1: `0 → 2320`;
- part 2: `2320 → 7564`;
- part 3: `7564 → 12821`;
- part 4: `12821 → 14068`.

The downloaded shared source ended around `12254` seconds. FFmpeg therefore produced part 3 only up to the physical end of the source and part 4 could not represent the advertised timeline. This was not a normal MP3/VBR rounding difference.

## Root cause class

`audioknigi.com.ua` can expose correct chapter start/end metadata while a redirect-backed shared media URL points to an older, truncated or otherwise shorter recording. A byte-complete HTTP download is therefore not sufficient proof that the media object matches the playlist timeline.

The previous verifier caught the resulting short chapter only **after** FFmpeg split the file. That protected output integrity, but wasted the download and could not recover automatically.

## Fix

### 1. Pre-download remote timeline validation

For playlists where multiple tracks share one physical source and expose cut end-times, AudioKnigi now probes the direct source duration through the existing Cloudflare-routed remote FFprobe path.

The source is accepted when it reaches the final advertised cut within a conservative tolerance (`max(15 s, 0.1% of timeline)`). Small encoder/VBR differences therefore keep the existing behavior.

### 2. Automatic provider recovery

When an `audioknigi.com.ua` shared source is materially shorter than the playlist timeline:

1. the mismatch is logged as `shared_source_timeline_mismatch`;
2. the app searches `knigavuhe.org` for the title;
3. candidate identity is checked by normalized title, author and narrator tokens (name order does not matter);
4. narration-variant URLs are considered, so the same reader can be selected even when it is not the representative search row;
5. the fetched replacement book is verified again before it is accepted;
6. the app switches to the matching `knigavuhe.org` book before the user starts the actual media download.

A wrong-author/wrong-reader candidate is rejected rather than silently downloading another book.

### 3. Local pre-split guard

After a shared source has been downloaded, its real local duration is checked again immediately before FFmpeg splitting. If the file still ends materially before the last playlist cut, splitting stops with a clear diagnostic instead of creating truncated chapters.

This second guard covers cases where remote FFprobe was unavailable or the CDN object changed between analysis and download.

## Failure behavior

If the source is short and no matching fallback recording can be found, analysis fails with an explicit message that the `audioknigi.com.ua` source is incomplete and suggests choosing the matching `knigavuhe.org` result. The app does **not** enlarge duration tolerance or mark a shortened chapter as valid.

## Regression coverage

Added `tests/test_audioknigi_shared_source_recovery_41231.py` covering:

- valid complete shared source;
- the real `14068` vs `12254` mismatch shape;
- automatic same-title/author/narrator fallback;
- rejection of a wrong-author fallback;
- local downloaded-source guard;
- integration of recovery into the fast `audioknigi.com.ua` analysis path.

Validation after the first recovery change:

- focused source/download suite: **27/27 passed**;
- complete active pytest suite: **505/505 passed**;
- standalone visual UI smoketest: **OK**;
- `compileall`: **OK**.

## Windows follow-up: proxy reset + misleading VBR/Xing duration

A second frozen Windows reproduction showed that the first recovery layer was still insufficient in two edge cases.

1. Remote FFprobe was correctly routed through the application-owned Cloudflare-resolving proxy, but the destination HTTPS connection could be reset with `WinError 10054`. A failed duration probe therefore produced an unknown result. Treating “unknown” as “valid” allowed the old shared source to proceed.
2. A truncated MP3 may retain a VBR/Xing header that advertises the original full duration. A normal local duration probe can therefore report the expected ~14,068 seconds even though real audio frames end much earlier. The mismatch only becomes visible when FFmpeg actually seeks into the missing tail.

### Follow-up hardening

- Remote validation failure is now explicitly logged as `shared_source_remote_validation_unavailable`; it is never interpreted as positive validation.
- Local validation now performs an FFprobe **packet-presence scan** near the final advertised chapter timestamp. The source is considered incomplete when FFprobe succeeds but no real audio packets exist in that interval, regardless of what the VBR/Xing duration header claims.
- The local guard raises a typed `SharedSourceTimelineError`, allowing `_process_book()` to recover without terminating the user’s current download operation.
- On that typed failure, `audioknigi.com.ua` automatically searches for an identity-matched `knigavuhe.org` title/author/narrator, maps the selected parts and retries with the replacement source. If a safe fallback cannot be found or reached, the operation stops with an explicit error instead of accepting shortened chapters.
- Packet probing and duration probing share one cooperative, hidden FFprobe subprocess runner, preserving cancellation/shutdown behavior and avoiding subprocess-path proliferation.

### Follow-up regression coverage

The shared-source regression file now contains **10 tests**, including:

- a truncated VBR/Xing source whose header falsely reports the full duration;
- positive/negative packet-presence checks near requested timestamps;
- automatic in-download provider switch after local validation failure;
- safe refusal when the local source is incomplete and no matching fallback is available.

Final validation after the Windows follow-up:

- focused shared-source suite: **10/10 passed**;
- related downloader/provider suite: **28/28 passed**;
- complete active pytest suite: **509/509 passed**;
- standalone visual UI smoketest: **OK**;
- `compileall`: **OK**.
