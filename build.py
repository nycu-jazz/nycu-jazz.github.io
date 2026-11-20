#!/usr/bin/env python3
"""把 data/site.json 產生成靜態頁面。

用法：python3 build.py
只用 Python 3 標準函式庫。產生的 index.html、各學期資料夾、404.html、sitemap.xml
都直接放在 repo 根目錄並一起 commit，GitHub Pages 不需要任何建置步驟。
"""

import json
import re
from datetime import date
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = json.loads((ROOT / "data" / "site.json").read_text(encoding="utf-8"))
SITE = DATA["site"]
SEMESTERS = DATA["semesters"]  # 由新到舊

WEEKDAYS = "一二三四五六日"
STATUS = {
    "performed": "已演出",
    "scheduled": "課綱排程",
    "syllabus": "課綱排程",
}
FONTS = (
    "https://fonts.googleapis.com/css2?family=Noticia+Text:ital@1"
    "&family=Noto+Sans+TC:wght@300;400;500&family=Raleway:wght@200;300&display=swap"
)

e = escape


# ---------- 小工具 ----------

def parse(iso):
    return date.fromisoformat(iso)


def fmt_date(iso, weekday=True):
    d = parse(iso)
    text = f"{d.year}/{d.month}/{d.day}"
    return f"{text}（{WEEKDAYS[d.weekday()]}）" if weekday else text


def term(sem):
    """'114A' -> (114, 1)"""
    m = re.fullmatch(r"(\d{3})([AB])", sem["code"])
    if not m:
        raise SystemExit(f"學期代碼格式錯誤：{sem['code']}")
    return int(m.group(1)), 1 if m.group(2) == "A" else 2


def term_name(sem):
    acy, n = term(sem)
    return f"{acy} 學年度第 {n} 學期"


def slug(sem):
    return sem["code"].lower()


def syllabus_url(sem):
    acy, n = term(sem)
    return (
        "https://timetable.nycu.edu.tw/?r=main/crsoutline"
        f"&Acy={acy}&Sem={n}&CrsNo={sem['crs_no']}&lang=zh-tw"
    )


def youtube_url(video):
    url = f"https://www.youtube.com/watch?v={video['id']}"
    return url + (f"&list={video['list']}" if video.get("list") else "")


def ext(url, label, cls=""):
    """外部連結：一律新分頁並標示。"""
    cls_attr = f' class="{cls}"' if cls else ""
    return (
        f'<a{cls_attr} href="{e(url)}" target="_blank" rel="noopener">'
        f'{label}<span class="visually-hidden">（另開新分頁）</span></a>'
    )


def status_chip(sem):
    label = STATUS[sem["status"]]
    if sem["status"] == "scheduled" and sem.get("show"):
        label = "即將演出"
    return f'<span class="status {sem["status"]}">{label}</span>'


def by_code(code):
    return next(s for s in SEMESTERS if s["code"] == code)


# ---------- 共用版型 ----------

def page(*, root, path, title, description, body, current=""):
    canonical = SITE["url"].rstrip("/") + path
    home = root or "./"

    def nav(href, label, key):
        cur = ' aria-current="page"' if key == current else ""
        return f'<a href="{href}"{cur}>{label}</a>'

    return f"""<!doctype html>
<html lang="zh-Hant-TW">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(description)}">
<link rel="canonical" href="{e(canonical)}">
<meta property="og:type" content="website">
<meta property="og:locale" content="zh_TW">
<meta property="og:site_name" content="{e(SITE['name'])}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(description)}">
<meta property="og:url" content="{e(canonical)}">
<meta name="theme-color" content="#060606">
<meta name="color-scheme" content="dark">
<link rel="icon" href="{root}assets/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS}">
<link rel="stylesheet" href="{root}assets/site.css">
</head>
<body>
<a class="skip" href="#main">跳到主要內容</a>
<header class="site-header">
  <div class="wrap">
    <a class="brand" href="{home}" aria-label="NYCU Jazz 首頁">NYCU <b>Jazz</b></a>
    <nav class="nav" aria-label="主要導覽">
      {nav(f"{root}{slug(by_code(SITE['current']))}/", "本學期", "current")}
      {nav(f"{root}#archive", "歷屆演出", "archive")}
    </nav>
  </div>
</header>
<main id="main">
{body}
</main>
<script src="{root}assets/site.js" defer></script>
</body>
</html>
"""


# ---------- 影片 ----------

def video_block(video, compact=False):
    title = e(video["title"])
    meta = e(video["kind"] if compact else f"{video['kind']}・{video['publisher']}")
    if video["type"] == "youtube":
        list_attr = f' data-list="{e(video["list"])}"' if video.get("list") else ""
        return f"""<figure class="video">
  <a class="video-frame" href="{e(youtube_url(video))}" target="_blank" rel="noopener" data-yt="{e(video['id'])}"{list_attr} data-title="{title}" aria-label="播放影片：{title}">
    <img src="https://i.ytimg.com/vi/{e(video['id'])}/hqdefault.jpg" alt="" width="480" height="360" loading="lazy" decoding="async">
    <span class="play" aria-hidden="true"></span>
  </a>
  <figcaption>
    <span class="video-title">{title}</span>
    <span class="video-meta">{meta}・{ext(youtube_url(video), "在 YouTube 觀看", "ext")}</span>
  </figcaption>
</figure>"""
    return f"""<figure class="video">
  <a class="video-link" href="{e(video['url'])}" target="_blank" rel="noopener">
    <span><span class="video-title">{title}</span><span class="video-meta">{meta}</span></span>
    <span class="go ext">在 Facebook 觀看<span class="visually-hidden">（另開新分頁）</span></span>
  </a>
</figure>"""


def videos_block(videos, compact=False):
    two = " two" if len(videos) > 1 else ""
    return f'<div class="videos{two}">\n' + "\n".join(video_block(v, compact=compact) for v in videos) + "\n</div>"


# ---------- 首頁 ----------

def archive_row(sem, latest=False):
    show = sem.get("show") or {}
    date_iso = show.get("date") or sem["syllabus_final"]["date"]
    time = f'<span>{e(show["time"])}</span>' if show.get("time") else ""
    venue = f'\n          <small>{e(show["venue"])}</small>' if show.get("venue") else ""
    section_id = ' id="latest"' if latest else ""
    status = '<span class="status performed">最近一場</span>' if latest else status_chip(sem)
    videos = sem["videos"]
    recordings = ""
    if videos:
        recordings = f'\n      <div class="archive-recordings">{videos_block(videos, compact=True)}</div>'
    return f"""    <li{section_id}>
      <a class="archive-row" href="{slug(sem)}/">
        <span class="archive-term">
          <strong>{e(sem['code'])}</strong>
          {status}
        </span>
        <span class="archive-date">
          <span><time datetime="{e(date_iso)}">{fmt_date(date_iso)}</time>{time}</span>{venue}
        </span>
        <span class="archive-more">場次資訊 <span aria-hidden="true">→</span></span>
      </a>{recordings}
    </li>"""


def build_home():
    cur = by_code(SITE["current"])
    cur_show = cur.get("show")
    cur_final = parse((cur_show or cur["syllabus_final"])["date"])
    time = (cur_show or {}).get("time")
    venue = (cur_show or {}).get("venue")
    details = f"{time or '時間待公布'}・{venue or '地點待公布'}" if time or venue else "時間與地點待公布"
    program = cur.get("program", {}).get("pieces", [])
    primary_url = f"{slug(cur)}/"
    primary_label = "查看演出資訊"
    if program:
        primary_url += "#program-h"
        primary_label = "查看曲目與編制"
    first, last = SEMESTERS[-1], SEMESTERS[0]
    archive = "\n".join(archive_row(s, latest=s["code"] == SITE["latest_show"]) for s in SEMESTERS)

    body = f"""<section class="hero" id="now" aria-labelledby="now-h">
  <div class="wrap hero-layout">
    <div class="hero-copy">
      <h1 id="now-h" lang="en">NYCU <span>Jazz</span></h1>
      <p class="eyebrow" lang="en">{e(SITE['course_en'])}</p>
      <p class="lede">陽明交大・{e(SITE['teacher'])}老師<br>{e(SITE['course_zh'])}</p>
    </div>
    <div class="hero-event">
      <p class="event-label">{status_chip(cur)}</p>
      <h2 class="event-title">{e(cur['code'])} 期末成果發表</h2>
      <time class="event-date" datetime="{cur_final.isoformat()}">
        <span class="event-day">{cur_final.month:02d}<span>/</span>{cur_final.day:02d}</span>
        <span class="event-weekday">{cur_final.year} 年・星期{WEEKDAYS[cur_final.weekday()]}</span>
      </time>
      <p class="event-details">{e(details)}</p>
      <a class="btn primary event-cta" href="{primary_url}">{primary_label}<span aria-hidden="true">→</span></a>
    </div>
  </div>
</section>

<section class="section" id="archive" aria-labelledby="archive-h">
  <div class="wrap">
    <div class="section-head">
      <span class="eyebrow" lang="en">{e(first['code'])} — {e(last['code'])}</span>
      <h2 id="archive-h">歷屆演出</h2>
    </div>
    <ul class="archive">
{archive}
    </ul>
  </div>
</section>"""

    return page(
        root="",
        path="/",
        title=f"{SITE['name']}｜陽明交大「{SITE['course_zh']}」期末演出紀錄",
        description=f"陽明交大「{SITE['course_zh']}」歷屆期末成果發表的日期、曲目與影片。",
        body=body,
    )


# ---------- 學期頁 ----------

def fact(label, value, detail=""):
    detail_html = f'<span class="fact-detail">{e(detail)}</span>' if detail else ""
    return f'<div class="fact"><dt>{label}</dt><dd>{value}{detail_html}</dd></div>'


def split(heading_en, heading, inner, hid, layout="split"):
    return f"""<section class="section tight" aria-labelledby="{hid}">
  <div class="wrap {layout}">
    <h2 id="{hid}"><span class="eyebrow" lang="en">{heading_en}</span>{heading}</h2>
    <div>
{inner}
    </div>
  </div>
</section>"""


def program_block(program):
    rows = []
    ordered = program.get("ordered", False)
    roles = dict.fromkeys(
        role
        for piece in program["pieces"] if isinstance(piece, dict)
        for role in piece.get("parts", {})
    )
    for number, piece in enumerate(program["pieces"], start=1):
        if isinstance(piece, str):
            piece = {"title": piece}
        title = e(piece["title"])
        number_html = f'<span class="piece-number" aria-hidden="true">{number:02d}</span>' if ordered else ""
        timestamp = f'<span class="piece-time">{e(piece["cue"])}</span>' if piece.get("cue") else ""
        if piece.get("url"):
            entry = ext(
                piece["url"],
                f'<span>{title}</span>{timestamp}<span class="piece-watch">觀看</span>',
                "piece-content",
            )
        else:
            entry = f'<div class="piece-content"><span>{title}</span>{timestamp}</div>'
        if parts := piece.get("parts"):
            credits = "".join(
                f"<div><dt>{e(role)}</dt><dd>{e(parts.get(role) or '—')}</dd></div>"
                for role in roles
            )
            entry = f'<div class="piece-score">{entry}<dl class="piece-parts">{credits}</dl></div>'
        rows.append(f"        <li>{number_html}{entry}</li>")
    list_html = ""
    if rows:
        tag = "ol" if ordered else "ul"
        style = "pieces ordered" if ordered else "pieces"
        if roles:
            style += " lineup"
        list_html = f'      <{tag} class="{style}" role="list">\n' + "\n".join(rows) + f"\n      </{tag}>\n"
    if source := program.get("source"):
        list_html += f'      <p class="footnote">{ext(source["url"], e(source["label"]))}</p>'
    layout = "split lineup-layout" if roles else "split"
    return split("Program", "演出曲目", list_html or "<p>曲目待補</p>", "program-h", layout)


def build_semester(index):
    sem = SEMESTERS[index]
    show = sem.get("show")
    syl = sem["syllabus_final"]
    root = "../"

    facts = []
    if show:
        facts.append(fact("演出日期", fmt_date(show["date"])))
        for key, label in (("time", "演出時間"), ("venue", "地點"), ("admission", "入場")):
            if value := show.get(key):
                facts.append(fact(label, e(value)))
    if sem["status"] == "scheduled":
        missing = [label for key, label in (("time", "演出時間"), ("venue", "地點")) if not (show or {}).get(key)]
        if missing:
            facts.append(fact("與".join(missing), "待公布"))
    if not show or show["date"] != syl["date"]:
        facts.append(
            fact(
                "課綱所列成果發表",
                fmt_date(syl["date"]),
                f"課綱第 {syl['week']} 週「{syl['text']}」",
            )
        )
    facts.append(fact("當期課號", e(sem["crs_no"]), f"{sem['credits']} 學分・{SITE['teacher']}老師"))

    sections = [
        f"""<section class="section tight" aria-label="場次資訊">
  <div class="wrap">
    <dl class="facts">
      {chr(10).join(facts)}
    </dl>
  </div>
</section>"""
    ]

    jumps = []
    if sem.get("program"):
        sections.append(program_block(sem["program"]))
        jumps.append('<a href="#program-h">看曲目</a>')

    if sem["videos"]:
        sections.append(split("Video", "演出影片", videos_block(sem["videos"]), "video-h"))
        jumps.append('<a href="#video-h">看演出影片</a>')
    jumps_html = f'\n    <nav class="term-jumps" aria-label="本頁導覽">{"".join(jumps)}</nav>' if jumps else ""

    # 來源：課綱一定有，接著是影片與額外來源
    sources = [
        {
            "label": f"{sem['code']} 課程綱要（課號 {sem['crs_no']}）",
            "url": syllabus_url(sem),
            "publisher": "國立陽明交通大學課程時間表",
        }
    ]
    for v in sem["videos"]:
        sources.append(
            {
                "label": f"{v['kind']}〈{v['title']}〉",
                "url": youtube_url(v) if v["type"] == "youtube" else v["url"],
                "publisher": v["publisher"],
            }
        )
    sources += sem.get("sources", [])
    src_html = "\n".join(
        f'        <li><div>{ext(s["url"], e(s["label"]))}<small>{e(s["publisher"])}</small></div></li>'
        for s in sources
    )
    sections.append(split("Sources", "資料來源", f'      <ol class="sources">\n{src_html}\n      </ol>', "sources-h"))

    newer = SEMESTERS[index - 1] if index > 0 else None
    older = SEMESTERS[index + 1] if index + 1 < len(SEMESTERS) else None
    pager_newer = (
        f'<a href="{root}{slug(newer)}/" rel="next"><small>← 較新的學期</small><b>{e(newer["code"])}</b></a>'
        if newer
        else '<span class="empty"></span>'
    )
    pager_older = (
        f'<a href="{root}{slug(older)}/" rel="prev"><small>較早的學期 →</small><b>{e(older["code"])}</b></a>'
        if older
        else f'<a href="{root}#archive"><small>回到列表 →</small><b>歷屆演出</b></a>'
    )

    hero_class = "term-hero term-hero-current" if sem["code"] == SITE["current"] else "term-hero"
    body = f"""<section class="{hero_class}">
  <div class="wrap">
    <a class="back" href="{root}#archive">← 歷屆演出</a>
    <span class="eyebrow" lang="en">{e(SITE['course_en'])}</span>
    <h1>{e(sem['code'])}</h1>
    <div class="term-sub">
      <span class="term-name">{term_name(sem)}・{e(SITE['course_zh'])}</span>
      {status_chip(sem)}
    </div>{jumps_html}
  </div>
</section>

{chr(10).join(sections)}

<nav class="pager wrap" aria-label="前後學期">
  {pager_newer}
  {pager_older}
</nav>"""

    return page(
        root=root,
        path=f"/{slug(sem)}/",
        title=f"{sem['code']} 期末演出｜{SITE['name']}",
        description=f"陽明交大「{SITE['course_zh']}」{term_name(sem)}（{sem['code']}）期末成果發表。",
        body=body,
        current="current" if sem["code"] == SITE["current"] else "",
    )


def build_404():
    body = """<section class="lost">
  <div class="wrap">
    <span class="eyebrow" lang="en">Not found</span>
    <h1>404</h1>
    <p>找不到這個頁面。</p>
    <div class="actions"><a class="btn primary" href="/#archive">看歷屆演出</a><a class="btn" href="/">回首頁</a></div>
  </div>
</section>"""
    # 404 可能出現在任何路徑深度，所以資源一律用根目錄絕對路徑。
    return page(root="/", path="/404.html", title=f"找不到頁面｜{SITE['name']}", description="找不到這個頁面。", body=body)


def build_sitemap():
    base = SITE["url"].rstrip("/")
    urls = [f"{base}/"] + [f"{base}/{slug(s)}/" for s in SEMESTERS]
    items = "\n".join(f"  <url><loc>{u}</loc></url>" for u in urls)
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{items}\n</urlset>\n'


def main():
    codes = [s["code"] for s in SEMESTERS]
    if len(set(codes)) != len(codes):
        raise SystemExit("學期代碼重複")
    for s in SEMESTERS:
        if s["status"] not in STATUS:
            raise SystemExit(f"{s['code']}：status 必須是 {list(STATUS)}")
        if s["status"] == "performed" and not s.get("show"):
            raise SystemExit(f"{s['code']}：已演出的學期必須填 show")

    out = {"index.html": build_home(), "404.html": build_404(), "sitemap.xml": build_sitemap()}
    for i, s in enumerate(SEMESTERS):
        out[f"{slug(s)}/index.html"] = build_semester(i)
    for rel, text in out.items():
        target = ROOT / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    (ROOT / ".nojekyll").touch()
    print(f"已產生 {len(out)} 個檔案：{'、'.join(sorted(out))}")


if __name__ == "__main__":
    main()
