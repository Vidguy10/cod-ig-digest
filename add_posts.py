"""Merge approved posts into data/posts.json and save run stats to data/run.json.

Usage: python add_posts.py approved.json

approved.json:
{
  "generated": "<ISO time of this run>",
  "posts_checked_24h": 123,
  "active_accounts": [...],
  "quiet_accounts": [...],
  "posts": [ {url, shortcode, outlet, handle, likes, comments, type, posted,
              title, priority, summary}, ... ]
}
title: one of "Modern Warfare 4", "Warzone", "DMZ", "Black Ops 7", "CDL", "Call of Duty".
priority: true if the post is about Modern Warfare 4, Warzone or DMZ.
Posts older than 30 days are dropped from the store.
"""
import json, os, sys
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
KEEP = ["url", "shortcode", "outlet", "handle", "likes", "comments", "type",
        "posted", "title", "priority", "summary"]

def main():
    new = json.load(open(sys.argv[1], encoding="utf-8"))
    os.makedirs(DATA, exist_ok=True)
    store_p = os.path.join(DATA, "posts.json")
    store = json.load(open(store_p, encoding="utf-8")) if os.path.exists(store_p) else []
    by_url = {p["url"]: p for p in store}
    for p in new.get("posts", []):
        by_url[p["url"]] = {k: p.get(k) for k in KEEP}
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    store = [p for p in by_url.values()
             if datetime.fromisoformat(p["posted"].replace("Z", "+00:00")) >= cutoff]
    store.sort(key=lambda p: p["posted"], reverse=True)
    json.dump(store, open(store_p, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    run = {k: new.get(k) for k in ["generated", "posts_checked_24h", "active_accounts", "quiet_accounts"]}
    run["demo"] = bool(new.get("demo"))
    json.dump(run, open(os.path.join(DATA, "run.json"), "w", encoding="utf-8"), indent=2)
    print(f"Stored {len(store)} posts; added/updated {len(new.get('posts', []))}")

if __name__ == "__main__":
    main()
