# AudioKnigi Downloader 4.12.9 — expired media URL recovery

Direct audio URLs may expire or disappear while the public book page remains valid. Version 4.12.9 treats HTTP 404/410 during media download as a refreshable source failure: it re-analyzes the book page, reloads the playlist, preserves track selection/local state, clears only temporary source chunks, and retries once. A repeated 404/410 after refresh is surfaced as a real unavailable-media error.
