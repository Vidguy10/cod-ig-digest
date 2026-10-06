# COD on Instagram digest

Daily page of Call of Duty mentions from tracked Instagram accounts (Step 3).

Morning flow (run by a scheduled Claude task, about 5:20 AM PT):
1. Export the "COD IG Coverage Log" Google Sheet as CSV.
2. `python candidates.py sheet.csv --hours 48 > candidates.json` (keyword matches not already stored).
3. Review candidates, drop false positives, write title/priority/summary into `approved.json`.
4. `python add_posts.py approved.json` (updates data/posts.json and data/run.json).
5. `python build.py` (renders index.html, last 7 days in Pacific time).
6. Commit and push; GitHub Pages serves index.html.
