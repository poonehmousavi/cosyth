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
