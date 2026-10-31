# Akniga description and HLS restart cache — experiment V8

Built on V7. All eight source providers and collection handling remain.

## Correct book descriptions

The Akniga book decoder no longer uses the SEO `<meta name="description">`
first. It extracts the visible synopsis from `itemprop="description"`,
common book-description containers, or the section headed `Описание`.
Only if visible text cannot be located does it fall back to the SEO meta
value, removing the promotional sentence `Аудиокнига «...», читает ...
Слушайте бесплатно онлайн.` without altering actual annotation prose.

Regression example: `https://akniga.org/kozhin-oleg-snegurochka`.
The synopsis begins with `Рассказ-победитель первого в истории DARKER...`
and continues with the story of the ethnographic expedition. The player,
chapters, and audio URLs are unchanged.

## Reusing completed HLS segments after interruption

When optional parallel HLS mode is enabled for a **whole book**, completed
segments are cached in `<book-folder>/.<source-stem>.hls-cache/`.
Only a byte-for-byte identical signed playlist URL + manifest can reuse
previous bytes. The program verifies SHA-256 and length of each cached segment
before reuse; mismatches are re-downloaded. It does not save original URLs,
access tokens, AES keys, or cookies in the persistent cache. HLS keys are
fetched each time into the automatically removed temporary staging folder.
When a full MP3 passes FFmpeg and duration verification and is installed,
the matching HLS cache folder is removed. Interrupted/failed tasks keep it.

**Important limitations:** Signed HLS URLs can expire/change on re-analysis.
If they change, cached segments deliberately cannot be reused. The cache is
not an arbitrary MP3 HTTP Range resume mechanism; individual chapter seek
still uses the normal FFmpeg path. The first download may have a small disk
I/O/checksum overhead. A failed attempt may leave a large hidden cache; close
the downloader and delete its `.hls-cache` folder manually if no longer needed.
Do not reuse cached media across different books or user accounts.

## Windows manual verification

1. Start with Cloudflare One enabled if it is needed to access Akniga.
2. Analyze `https://akniga.org/kozhin-oleg-snegurochka` and read the description.
   It should start with `Рассказ-победитель...`, not `Аудиокнига...`.
3. Enable parallel HLS, choose an authorized longer audiobook, and cancel
   while segments are downloading. Retry the *same previously analyzed book*
   soon afterward; unchanged segments should be reused. Changed signed
   URLs/manifests should cause a fresh download.
4. Verify the final MP3 plays through to the end and no incomplete MP3
   replaces an existing good download.
5. Confirm the HLS cache is automatically removed after a successful
   validated download. Check NVDA/JAWS reporting manually on Windows.

Automated tests are offline mocks; this environment has not verified a
live Akniga download on the user's network/Windows installation.
