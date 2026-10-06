# COD on Instagram digest

Public page: https://vidguy10.github.io/cod-ig-digest/

Each morning a GitHub Action (`.github/workflows/digest.yml`) runs `update.py`, which:
1. Pulls the latest successful Apify "Instagram Post Scraper" run (secret `APIFY_TOKEN`).
2. Keeps posts whose caption or hashtags mention Call of Duty (rules in `classify()`).
   Priority = Modern Warfare 4, Warzone or DMZ.
3. Updates `data/posts.json` (30 days kept) and `data/run.json`, then `build.py` renders
   `index.html` showing the last 7 days in Pacific time.

A scheduled Claude task then reads `data/posts.json` and `data/run.json` from the page
and emails Steve a short summary with the page link.

Run by hand: Actions tab, "Daily COD digest", "Run workflow".
