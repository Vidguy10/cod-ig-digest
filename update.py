"""Daily digest update, run by GitHub Actions.

1. Pull the latest successful Instagram Post Scraper run from Apify (needs APIFY_TOKEN),
   or read items from a local JSON file: python update.py --items items.json
2. Keep posts that mention Call of Duty (keyword rules below).
3. Merge them into data/posts.json (keeps 30 days), write data/run.json, rebuild index.html.
"""
import argparse, json, os, re, sys, urllib.request
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
APIFY_URL = ("https://api.apify.com/v2/acts/apify~instagram-post-scraper/runs/last/dataset/items"
             "?status=SUCCEEDED&clean=true&format=json&token={token}")

# Keyword rules. Case-sensitive where the lowercase word has other meanings
# ("cod" the fish, "warzones" as a figure of speech, "DMZ" the Korean border).
def classify(text):
    found = []
    if re.search(r"modern\s*warfare\s*(4|iv)\b|\bmw4\b", text, re.I):
        found.append(("Modern Warfare 4", True))
    if re.search(r"\bWarzone\b|\bWARZONE\b", text) or re.search(r"#warzone\b", text, re.I):
        found.append(("Warzone", True))
    if re.search(r"\bDMZ\b", text) and not re.search(r"korea", text, re.I):
        found.append(("DMZ", True))
    if re.search(r"black\s*ops|\bBO7\b", text, re.I):
        found.append(("Black Ops", False))
    if re.search(r"\bCDL\b", text) or re.search(r"call\s*of\s*duty\s*league", text, re.I):
        found.append(("CDL", False))
    if (re.search(r"call\s*of\s*duty|#callofduty|\bactivision\b|modern\s*warfare|#cod\b", text, re.I)
            or re.search(r"\bCOD\b|\bCoD\b", text)):
        found.append(("Call of Duty", False))
    if not found:
        return None, False
    return found[0][0], any(p for _, p in found)

def excerpt(caption, limit=220):
    c = re.sub(r"\s+", " ", caption or "").strip()
    c = re.sub(r"\s*(head to the )?link in (the )?(bio|comments)( for (more|our [^.]*))?\.?", "", c, flags=re.I).strip()
    m = re.match(r"(.+?[.!?])(\s|$)", c)
    s = m.group(1) if m and len(m.group(1)) >= 40 else c
    if len(s) > limit:
        s = s[:limit].rsplit(" ", 1)[0] + "..."
    return s

def load_items(args):
    if args.items:
        return json.load(open(args.items, encoding="utf-8"))
    token = os.environ.get("APIFY_TOKEN")
    if not token:
        sys.exit("APIFY_TOKEN is not set")
    with urllib.request.urlopen(APIFY_URL.format(token=token), timeout=120) as r:
        return json.load(r)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--items")
    args = ap.parse_args()
    items = load_items(args)

    now = datetime.now(timezone.utc)
    day_ago = now - timedelta(hours=24)
    os.makedirs(DATA, exist_ok=True)
    store_p = os.path.join(DATA, "posts.json")
    store = json.load(open(store_p, encoding="utf-8")) if os.path.exists(store_p) else []
    by_url = {p["url"]: p for p in store}

    active, quiet, checked, added = set(), set(), 0, 0
    for it in items:
        if it.get("error"):
            h = (it.get("inputUrl") or "").rstrip("/").split("/")[-1]
            if h:
                quiet.add(h)
            continue
        ts = it.get("timestamp")
        if not ts or not it.get("url"):
            continue
        t = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        if t >= day_ago:
            active.add(it.get("ownerUsername", ""))
            checked += 1
        if it.get("isPinned") and t < now - timedelta(days=3):
            continue
        tags = it.get("hashtags") or []
        if isinstance(tags, str):
            tags = [tags]
        text = (it.get("caption") or "") + " " + " ".join("#" + h.lstrip("#") for h in tags)
        title, pri = classify(text)
        if not title:
            continue
        if it["url"] not in by_url:
            added += 1
        by_url[it["url"]] = {
            "url": it["url"],
            "shortcode": it.get("shortCode"),
            "outlet": it.get("ownerFullName") or it.get("ownerUsername"),
            "handle": it.get("ownerUsername"),
            "likes": int(it.get("likesCount") or 0),
            "comments": int(it.get("commentsCount") or 0),
            "type": it.get("type"),
            "posted": ts,
            "title": title,
            "priority": pri,
            "summary": excerpt(it.get("caption")),
        }

    cutoff = now - timedelta(days=30)
    store = sorted((p for p in by_url.values()
                    if datetime.fromisoformat(p["posted"].replace("Z", "+00:00")) >= cutoff),
                   key=lambda p: p["posted"], reverse=True)
    json.dump(store, open(store_p, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    run = {
        "generated": now.isoformat(),
        "posts_checked_24h": checked,
        "active_accounts": sorted(a for a in active if a),
        "quiet_accounts": sorted(quiet - active),
        "new_posts": added,
        "demo": False,
    }
    json.dump(run, open(os.path.join(DATA, "run.json"), "w", encoding="utf-8"), indent=2)
    print(f"Items: {len(items)}, checked 24h: {checked}, new COD posts: {added}, stored: {len(store)}")

    import build
    build.main()

if __name__ == "__main__":
    main()
