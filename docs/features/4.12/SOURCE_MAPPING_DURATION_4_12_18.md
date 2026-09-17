# AudioKnigi Downloader 4.12.18 — Stable Source Mapping & Duration Verification

## Problem reproduced from Windows log

A full five-part download originally created `_source_01.mp3` through `_source_05.mp3`. After verification marked a subset for repair, the retry rebuilt `unique_files` only from parts 2, 3 and 5 and renumbered that subset from 1. This caused track 2 to read `_source_01.mp3`, track 3 to read `_source_02.mp3`, and track 5 to read `_source_03.mp3`. FFmpeg itself succeeded, but it was given the wrong input.

## Fix

Temporary source slots are now computed from the complete `book.tracks` playlist and then reused by every subset. The mapping is stable across first download, retry, repair and selective download. A single shared source still uses the legacy `_source.mp3` name.

## Duration verification

The previous 2-second tolerance rejected a valid chapter reported by the playlist as 48:21 when the downloaded MP3 measured 48:24. The tolerance is now 5 seconds. This still rejects a wrong chapter such as 21:06 for an expected 48:21.

## Diagnostics

`BOOK FLOW | event=source_mapping` is emitted at DEBUG level for every active source with source slot, temporary filename and affected track indices.

## Validation environment

Source regression tests are executed in the available Linux environment. Windows release scripts remain strictly pinned to CPython 3.14.7 x64.
