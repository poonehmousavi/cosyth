# Listening test site (Contextual Audio-Speech Co-Synthesis)

Published at https://claude.ai/artifact/YLRHCMJiGHUGYGyuRKri2b

- index.html      : the test page (single file, no build step)
- manifest.json   : sample list with roles (pool / anchor / example / practice), clip offsets, fixed anchors
- audio/<id>.mp4  : one AAC sprite per sample (clips concatenated, loudness-matched to -20 LUFS)
- build_sprites.py: rebuilds audio/ + manifest.json from ../user_survey_full_20260917 and pool50.json
- pool50.json     : the 50 selected pool samples (also ../listening_test_pool50.csv)

URL parameters: ?p=<rater number> (balanced coverage), na=6&ns=6 (trials per direction),
pool=<n>, practice=0, reveal=1 (team view), to=<email>, ex2=<id> (speech->sound example).

Results: raters copy a JSON blob at the end and send it to the study team; nothing is stored server-side.
Collect the blobs as one file each in a results/ folder for analysis.

## Automatic result collection (setup once)

1. Google Sheet: create a new sheet at sheets.google.com. Extensions > Apps Script. Replace the code with
   apps_script.gs. Deploy > New deployment > type "Web app", Execute as "Me", Who has access "Anyone" > Deploy.
   Authorize when asked. Copy the Web app URL (https://script.google.com/macros/s/.../exec).
2. In index.html replace PASTE_APPS_SCRIPT_URL_HERE with that URL (or append ?endpoint=<url> to every rater link).
3. Host the site on GitHub Pages: create an empty repo on github.com, then in this folder
       git remote add origin https://github.com/<user>/<repo>.git
       git branch -M main && git push -u origin main
   On github.com: Settings > Pages > Source "Deploy from a branch", branch main, folder / (root). Wait ~1 min.
   Rater links: https://<user>.github.io/<repo>/?p=1  (p=2, p=3, ...).
4. Each finished rater adds a row (status=complete) to the sheet; partial rows are written after every page,
   so an abandoned session is not lost. Analysis: keep the latest row per participant.
