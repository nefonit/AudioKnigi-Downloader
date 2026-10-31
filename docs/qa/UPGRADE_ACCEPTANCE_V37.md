# V37 — Windows EXE upgrade and NVDA/JAWS acceptance

**Release status: not approved.** This procedure collects evidence for an
exact, hashed candidate EXE. Only a human Windows tester can approve the
upgrade and screen-reader checklist. Unit tests do **not** replace these steps.

## Prerequisites

- Windows 10/11 with current NVDA and JAWS available for separate passes
- An old, known-working AudioKnigiDownloader_Qt.exe and the new candidate EXE
  in **different** directories
- Python 3.14.7 x64 and the project's `.venv-qt` (run `build_qt_exe.bat`)
- The candidate's `dist/qt_release_candidate.json` and accompanying legal
  notices, verified with `tools/release_candidate_audit.py`
- A **new disposable** Windows account or a temporary APPDATA profile. Never
  copy your real account's cookies, credentials, settings or audiobook library
  into a public test archive.

## 1. Prepare an isolated old-version profile

In a new Command Prompt, run:

```bat
mkdir C:\AK-V37-QA\Profile
set "APPDATA=C:\AK-V37-QA\Profile"
"C:\OldAudioKnigi\AudioKnigiDownloader_Qt.exe"
```

The application should create its private state under
`C:\AK-V37-QA\Profile\AudioKnigiDownloader`.
Use a separate disposable folder for downloads, not real personal books.
While running the **old** build, set a recognizable theme/language, queue
two sample tasks, finish one tiny permitted test download to populate history,
open a local test MP3 and advance the player position. Leave another task
queued or interrupted. Confirm the old program is fully closed.

The application does **not** currently ship a standalone MSI/in-place
installer. This exercise tests replacement of a one-file Windows EXE using
the same app profile; it does not claim installer-upgrade support.

## 2. Capture the old state (no writes to the profile)

From the project checkout, run:

```bat
run_qt_upgrade_acceptance.bat before "C:\AK-V37-QA\Profile\AudioKnigiDownloader" "C:\OldAudioKnigi\AudioKnigiDownloader_Qt.exe"
```

This saves `dist/qt_upgrade_before.json` **outside** the app profile.
Only SHA-256 digests, JSON types and counts are stored. No titles, paths
inside settings, selected tracks, passwords, cookies, tokens or audio bytes
are copied into the evidence. Keep this report private nonetheless.

## 3. Launch the new EXE with exactly the same test profile

Still in a Command Prompt with the isolated `APPDATA` environment:

```bat
set "APPDATA=C:\AK-V37-QA\Profile"
"C:\NewAudioKnigi\AudioKnigiDownloader_Qt.exe"
```

With the new EXE, verify manually and with NVDA:

1. The application opens without first-run setup, and the intended language,
   theme, scale, configured download folder and accessibility preferences
   remain recognizable.
2. The two queue entries preserve their order, selected chapters and modes.
   Any task formerly `running` becomes `interrupted`, not `completed`;
   it must not auto-start. Normal manual resume is still possible.
3. The completed book remains in history, and its audio file still plays.
   Duplicate preflight must not re-download a proven complete book.
4. The test MP3's saved position returns close to where playback stopped.
5. A valid small download can resume with no file loss; cancellation,
   closing with running workers and clean shutdown behave as documented.

Close the new program normally; do not modify/clear queue or history
between the before/after comparison, except for the expected normalization
of a previously running task.

## 4. Verify preservation of persisted state

```bat
run_qt_upgrade_acceptance.bat after "C:\AK-V37-QA\Profile\AudioKnigiDownloader" "C:\NewAudioKnigi\AudioKnigiDownloader_Qt.exe"
```

The tool writes `dist/qt_upgrade_after.json` and returns:

- Exit **0 — PASS**: all previously present JSON files have unchanged
  SHA-256 and shape, with a different EXE. *This is only the automated
  state comparison; manual approval is still required.*
- Exit **2 — REVIEW**: existing JSON was valid but changed, or a new file
  appeared. This can be normal (settings migration, queue task
  `running` → `interrupted`, playback progress), but the tester must
  compare behavior and sign off manually. Do not mark this as PASS on CI.
- Exit **1 — FAIL**: a previously present file disappeared, became invalid,
  changed top-level shape, lost queue/history rows, or the EXE hash did not
  change. Stop the upgrade test and preserve the disposable profile for
  investigation.

The tool does not modify profile files, execute the EXE or automatically
change a REVIEW to PASS. It uses only the explicitly supplied profile path;
there is no live-account location discovery. File hashes are evidence, not
proof that records retained their exact meaning, so human comparison is
essential.

## 5. Test the exact new EXE with *both* screen readers

```bat
run_qt_acceptance.bat
check_qt_acceptance.bat
```

These invoke `tools/qt_windows_acceptance.py`, which records the SHA-256
of the tested EXE and 14 keyboard/focus/speech checks for **NVDA and JAWS**
independently. Use the same candidate binary as in steps 3–4. Record a
result for every check, including the Help Center, queue, dialogs,
focus restoration, and the player's spoken time position. Inspect
`dist/qt_windows_acceptance.json` for an exact-hash PASS.

The upgrade-evidence tool and the existing screen-reader acceptance
report are separate artifacts: **both must be reviewed**. Neither
automated tests nor a green GitHub CI run can fill out manual results.

## 6. Adversarial and rollback exercises

In a second disposable profile (never the user's real account):
- Force-stop the **test** EXE with Windows Task Manager while a tiny test
  download runs; then restart the new EXE and check V33/V34 recovery of
  queue, history and `.part` bytes.
- Change one JSON file deliberately only **after** saving a copy of the test
  profile. The comparison must return FAIL for corruption/missing data.
- If the new build fails acceptance, close it and revert to the old EXE
  without overwriting the test profile or deleting its `*.lastgood.json`
  state files. Restore the pre-upgrade disposable backup if the old build
  cannot read a migrated settings schema. Do not claim downgrade support
  without actually testing it.

## Final Go/No-Go

Record the new EXE SHA-256, source commit, Windows version, NVDA/JAWS
versions, two acceptance-report statuses, upgrade evidence file, identified
regressions, and explicit manual reviewer decision. The project currently
has **no approved top-level application license**; finish Qt/FFmpeg notices
and licensing review before public distribution. Until these manual gates
and the real release build have completed, the project remains **No-Go**.

See `docs/development/RELEASE_PREFLIGHT_V36.md` and
`docs/qa/RELEASE_READINESS.md` for related gates.
