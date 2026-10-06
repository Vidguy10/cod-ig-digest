"""Find Call of Duty candidate posts in the Apify sheet export.

Usage:
  python candidates.py sheet.csv [--hours 48] > candidates.json

Reads the CSV exported from the "COD IG Coverage Log" Google Sheet, keeps posts
from the last N hours whose caption or hashtags match a Call of Duty keyword,
and skips posts already stored in data/posts.json. Claude reviews the output,
drops false positives, writes summaries, and adds approved posts with add_posts.py.
Also prints run stats (accounts with posts, quiet accounts) for the page footer.
"""
import csv, json, re, sys, argparse, os
from datetime import datetime, timedelta, timezone

PATTERN = re.compile(
    r"call\s*of\s*duty|\bcod\b|\bactivision\b|modern\s*warfare|\bmw4\b|warzone|\bdmz\b"
    r"|black\s*ops|\bbo7\b|\bcdl\b",
    re.I,
)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--hours", type=int, default=48)
    args = ap.parse_args()

    csv.field_size_limit(10**9)
    with open(args.csv, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    here = os.path.dirname(os.path.abspath(__file__))
    store = os.path.join(here, "data", "posts.json")
    known = set()
    if os.path.exists(store):
        known = {p["url"] for p in json.load(open(store, encoding="utf-8"))}

    now = datetime.now(timezone.utc)
    since = now - timedelta(hours=args.hours)
    day_ago = now - timedelta(hours=24)
    cands, active, quiet, checked = [], set(), set(), 0

    for r in rows:
        if (r.get("error") or "").strip() == "no_items":
            handle = (r.get("inputUrl") or "").rstrip("/").split("/")[-1]
            if handle:
                quiet.add(handle)
            continue
        ts = r.get("timestamp") or ""
        if not ts:
            continue
        t = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        if t >= day_ago:
            active.add(r.get("ownerUsername", ""))
            checked += 1
        if t < since:
            continue
        tags = " ".join(v for k, v in r.items() if k.startswith("hashtags/") and v)
        text = (r.get("caption") or "") + " " + tags
        m = PATTERN.findall(text)
        if not m or r.get("url") in known:
            continue
        cands.append({
            "url": r.get("url"),
            "shortcode": r.get("shortCode"),
            "outlet": r.get("ownerFullName"),
            "handle": r.get("ownerUsername"),
            "likes": int(float(r.get("likesCount") or 0)),
            "comments": int(float(r.get("commentsCount") or 0)),
            "type": r.get("type"),
            "posted": ts,
            "matched_terms": sorted({x.lower() for x in m}),
            "caption": r.get("caption"),
            "hashtags": tags,
        })

    quiet |= {h for h in quiet if h not in active}
    json.dump({
        "generated": now.isoformat(),
        "posts_checked_24h": checked,
        "active_accounts": sorted(a for a in active if a),
        "quiet_accounts": sorted(quiet - active),
        "candidates": cands,
    }, sys.stdout, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()
