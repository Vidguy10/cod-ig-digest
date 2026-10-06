"""Render index.html (the COD on Instagram digest page) from data/posts.json.

Usage: python build.py

data/posts.json  list of approved Call of Duty posts (see add_posts.py)
data/run.json    stats from the latest morning run (accounts checked, quiet accounts)
Shows the last 7 days in Pacific time, newest first.
"""
import json, os, html
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

PT = ZoneInfo("America/Los_Angeles")
HERE = os.path.dirname(os.path.abspath(__file__))
DAYS = 7

def load(name, default):
    p = os.path.join(HERE, "data", name)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else default

def esc(s):
    return html.escape(str(s or ""), quote=True)

def fmt_day(d, today):
    label = d.strftime("%a %b ") + str(d.day)
    if d == today:
        return "Today", label
    if d == today - timedelta(days=1):
        return "Yesterday", label
    return d.strftime("%A"), label

def fmt_time(dt):
    return dt.strftime("%I:%M %p").lstrip("0") + " PT"

TYPE_NAMES = {"Image": "Image", "Sidecar": "Carousel", "Video": "Video"}

def card(p):
    posted = datetime.fromisoformat(p["posted"].replace("Z", "+00:00")).astimezone(PT)
    code = esc(p.get("shortcode") or p["url"].rstrip("/").split("/")[-1])
    pri = bool(p.get("priority"))
    badge_cls = "badge pri" if pri else "badge"
    return f"""
<article class="post{' is-pri' if pri else ''}" data-priority="{1 if pri else 0}">
  <div class="embed"><iframe src="https://www.instagram.com/p/{code}/embed/" loading="lazy" scrolling="no" allowtransparency="true" title="Instagram post by @{esc(p['handle'])}"></iframe></div>
  <div class="body">
    <div class="who"><span class="outlet">{esc(p['outlet'])}</span> <span class="handle">@{esc(p['handle'])}</span></div>
    <div><span class="{badge_cls}">{esc(p.get('title') or 'Call of Duty')}</span>{' <span class="badge spon">Sponsored</span>' if p.get('sponsored') else ''}</div>
    <p class="summary">{esc(p.get('summary'))}</p>
    <div class="meta">{p.get('likes', 0):,} likes · {p.get('comments', 0):,} comments · {TYPE_NAMES.get(p.get('type'), esc(p.get('type')))} · {fmt_time(posted)}</div>
    <a class="view" href="{esc(p['url'])}" target="_blank" rel="noopener">View on Instagram</a>
  </div>
</article>"""

def main():
    posts = load("posts.json", [])
    run = load("run.json", {})
    now = datetime.now(timezone.utc)
    gen = datetime.fromisoformat(run["generated"]) if run.get("generated") else now
    gen_pt = gen.astimezone(PT)
    today = gen_pt.date()
    first = today - timedelta(days=DAYS - 1)

    by_day = {}
    for p in posts:
        d = datetime.fromisoformat(p["posted"].replace("Z", "+00:00")).astimezone(PT).date()
        if first <= d <= today:
            by_day.setdefault(d, []).append(p)

    recent = [p for p in posts
              if datetime.fromisoformat(p["posted"].replace("Z", "+00:00")) >= gen - timedelta(hours=24)]
    week = [p for ps in by_day.values() for p in ps]
    stats = (f"<b>{len(recent)}</b> in the last 24 hours "
             f"(<b>{sum(1 for p in recent if p.get('priority'))}</b> Priority) · "
             f"<b>{len(week)}</b> in the last 7 days")

    sections = []
    for i in range(DAYS):
        d = today - timedelta(days=i)
        ps = sorted(by_day.get(d, []), key=lambda p: (not p.get("priority"), -p.get("likes", 0)))
        name, label = fmt_day(d, today)
        npri = sum(1 for p in ps if p.get("priority"))
        body = "".join(card(p) for p in ps) if ps else ""
        sections.append(f"""
<section class="day" data-total="{len(ps)}" data-pri="{npri}">
  <h2><span>{name}</span> <small>{label}</small> <em class="count"></em></h2>
  {body}
  <p class="empty">No Call of Duty posts.</p>
</section>""")

    demo = ""
    if run.get("demo"):
        demo = ('<div class="demo"><b>Test page.</b> No Call of Duty posts have been found yet, so these are '
                'real Games posts from the tracked accounts, shown in the exact layout COD posts will use.</div>')

    tracked = ", ".join(esc(a) for a in run.get("active_accounts", [])) or "n/a"
    quiet = ", ".join(esc(a) for a in run.get("quiet_accounts", [])) or "none"
    out = TEMPLATE.format(
        updated=esc(gen_pt.strftime("%a %b ") + str(gen_pt.day) + ", " + fmt_time(gen_pt)),
        stats=stats, demo=demo, sections="".join(sections),
        tracked=tracked, quiet=quiet, checked=f"{run.get('posts_checked_24h', 0):,}",
    )
    open(os.path.join(HERE, "index.html"), "w", encoding="utf-8").write(out)
    print(f"Built index.html: {len(week)} posts in last {DAYS} days")

TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>COD on Instagram</title>
<style>
:root{{--bg:#f6f5f2;--card:#fff;--ink:#1c1c1a;--mut:#6b6a65;--line:#e4e2dc;--acc:#3d5a3a;--pri:#b4560f;--pri-bg:#fbeee2;--demo:#fff4d6;--demo-line:#e8c766}}
@media (prefers-color-scheme:dark){{:root{{--bg:#151614;--card:#1e1f1c;--ink:#ecebe6;--mut:#a09f98;--line:#33342f;--acc:#9cc298;--pri:#f0a35e;--pri-bg:#3a2a1c;--demo:#3a3220;--demo-line:#7a6a3a}}}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}}
.wrap{{max-width:880px;margin:0 auto;padding:24px 16px 48px}}
header h1{{margin:0;font-size:26px;letter-spacing:-.01em}}
header p{{margin:4px 0 0;color:var(--mut);font-size:14px}}
.stats{{margin:16px 0 8px;font-size:15px}}
.filters{{display:flex;gap:8px;margin:12px 0 4px}}
.filters button{{font:inherit;font-size:14px;padding:6px 14px;border-radius:999px;border:1px solid var(--line);background:var(--card);color:var(--ink);cursor:pointer}}
.filters button[aria-pressed=true]{{background:var(--acc);border-color:var(--acc);color:var(--bg)}}
.demo{{background:var(--demo);border:1px solid var(--demo-line);border-radius:8px;padding:10px 12px;margin:16px 0;font-size:14px}}
.day{{margin-top:28px}}
.day h2{{font-size:17px;margin:0 0 10px;padding-bottom:6px;border-bottom:1px solid var(--line);display:flex;gap:8px;align-items:baseline}}
.day h2 small{{color:var(--mut);font-weight:400;font-size:14px}}
.day h2 .count{{margin-left:auto;color:var(--mut);font-style:normal;font-weight:400;font-size:14px}}
.empty{{color:var(--mut);font-size:14px;margin:6px 0}}
.day[data-total="0"] .empty{{display:block}} .day .empty{{display:none}}
body.only-pri .post:not(.is-pri){{display:none}}
body.only-pri .day[data-pri="0"] .empty{{display:block}}
.post{{display:grid;grid-template-columns:330px 1fr;gap:18px;background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px;margin:12px 0}}
.post.is-pri{{border-left:4px solid var(--pri)}}
.embed iframe{{width:100%;max-width:330px;height:420px;border:0;border-radius:6px;background:var(--bg);display:block}}
.who .outlet{{font-weight:650;font-size:16px}} .who .handle{{color:var(--mut)}}
.badge{{display:inline-block;font-size:12px;padding:2px 8px;border-radius:4px;background:var(--bg);border:1px solid var(--line);margin:6px 0 2px}}
.badge.spon{{background:transparent;border-style:dashed;color:var(--mut);margin-left:4px}}
.badge.pri{{background:var(--pri-bg);border-color:var(--pri);color:var(--pri);font-weight:600}}
.summary{{margin:8px 0}}
.meta{{color:var(--mut);font-size:13px}}
.view{{display:inline-block;margin-top:10px;color:var(--acc);font-weight:600;text-decoration:none}}
.view:hover{{text-decoration:underline}}
footer{{margin-top:40px;color:var(--mut);font-size:13px;border-top:1px solid var(--line);padding-top:12px}}
@media (max-width:640px){{.post{{grid-template-columns:1fr}} .embed iframe{{max-width:100%}}}}
</style>
</head>
<body>
<div class="wrap">
<header>
  <h1>COD on Instagram</h1>
  <p>Call of Duty mentions from tracked Games and entertainment outlets · Updated {updated}</p>
</header>
{demo}
<div class="stats">{stats}</div>
<div class="filters" role="group" aria-label="Filter">
  <button type="button" data-f="all" aria-pressed="true">All COD</button>
  <button type="button" data-f="pri" aria-pressed="false">Priority only</button>
</div>
{sections}
<footer>
  <p>Priority = posts mentioning Modern Warfare 4, Warzone or DMZ. Sponsored = the post is marked as a paid partnership or tagged #ad. Posts are matched on caption text and hashtags, so posts that only show the game visually may be missed.</p>
  <p>Last run checked {checked} posts. Accounts with posts in the last 24 hours: {tracked}. Quiet accounts: {quiet}.</p>
</footer>
</div>
<script>
(function(){{
  var btns=document.querySelectorAll('.filters button');
  function counts(){{
    var only=document.body.classList.contains('only-pri');
    document.querySelectorAll('.day').forEach(function(s){{
      var n=+s.getAttribute(only?'data-pri':'data-total');
      s.querySelector('.count').textContent=n?(n+(n===1?' post':' posts')):'';
    }});
  }}
  btns.forEach(function(b){{b.addEventListener('click',function(){{
    btns.forEach(function(x){{x.setAttribute('aria-pressed',x===b?'true':'false')}});
    document.body.classList.toggle('only-pri',b.getAttribute('data-f')==='pri');
    counts();
  }})}});
  counts();
}})();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main()
