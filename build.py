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
    "scheduled": "課綱排程・場次未查證",
    "syllabus": "僅課綱排程",
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
    return f'<span class="status {sem["status"]}">{STATUS[sem["status"]]}</span>'


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
      {nav(f"{root}#about", "關於本站", "about")}
    </nav>
  </div>
</header>
<main id="main">
{body}
</main>
<footer class="site-footer">
  <div class="wrap">
    <div>
      <p><strong>本站由修課學生自行整理</strong>，不是國立陽明交通大學、跨域學程或授課教師的官方網站，內容未經其審閱或背書。</p>
      <p>各項資料查閱於 {fmt_date(SITE['checked'], weekday=False)}。課程與演出以課綱、E3 公告及學程官方頻道為準。</p>
    </div>
    <p class="cadence" aria-hidden="true">ii – V – I</p>
  </div>
</footer>
<script src="{root}assets/site.js" defer></script>
</body>
</html>
"""


# ---------- 影片 ----------

def video_block(video):
    title = e(video["title"])
    meta = e(f"{video['kind']}・{video['publisher']}")
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


def videos_block(videos):
    two = " two" if len(videos) > 1 else ""
    return f'<div class="videos{two}">\n' + "\n".join(video_block(v) for v in videos) + "\n</div>"


# ---------- 首頁 ----------

def archive_row(sem, root=""):
    show = sem.get("show")
    if show:
        when, label = fmt_date(show["date"]), "演出日"
    else:
        when, label = fmt_date(sem["syllabus_final"]["date"]), "課綱所列日期"
    tags = '<span class="tag">有影片</span>' if sem["videos"] else ""
    return f"""    <li>
      <a class="row" href="{root}{slug(sem)}/">
        <span class="row-code">{e(sem['code'])}</span>
        <span class="row-main">
          <span class="row-meta">{status_chip(sem)}{tags}</span>
          <span class="row-sum">{e(sem['summary'])}</span>
        </span>
        <span class="row-date">{when}<small>{label}</small></span>
        <span class="row-arrow" aria-hidden="true">→</span>
      </a>
    </li>"""


def build_home():
    cur = by_code(SITE["current"])
    latest = by_code(SITE["latest_show"])
    cur_final = parse(cur["syllabus_final"]["date"])
    first, last = SEMESTERS[-1], SEMESTERS[0]
    n_perf = sum(1 for s in SEMESTERS if s["status"] == "performed")
    gaps = "、".join(SITE["no_course"])

    body = f"""<section class="hero">
  <div class="wrap">
    <h1><span>NYCU</span><span>Jazz</span></h1>
    <span class="eyebrow" lang="en">{e(SITE['course_en'])}</span>
    <p class="lede">陽明交大<strong>「{e(SITE['course_zh'])}」</strong>每學期末的 combo 成果演出：哪一天、在哪裡、哪裡看得到錄影。</p>
    <p class="notice">修課學生自行整理，非學校或授課教師官方網站</p>
  </div>
</section>

<section class="section" id="now" aria-labelledby="now-h">
  <div class="wrap">
    <div class="section-head">
      <span class="eyebrow" lang="en">This semester</span>
      <h2 id="now-h">本學期・{e(cur['code'])}</h2>
    </div>
    <div class="now">
      <p class="now-date">{cur_final.month}/{cur_final.day}<small>{cur_final.year} 年・週{WEEKDAYS[cur_final.weekday()]}・課綱第 {cur['syllabus_final']['week']} 週<br>{status_chip(cur)}</small></p>
      <div class="now-body">
        <p>課綱在這一週排的進度是<strong>「{e(cur['syllabus_final']['text'])}」</strong>。這是課程排程，不是演出公告：對外場次的時間與地點，截至 {fmt_date(SITE['checked'], weekday=False)} 還沒有查到公開資料。</p>
        <p>課綱載明公告與重要訊息都在網路教學平台發布，修課同學請以 E3 上的課程公告為準。前三個可查證的學期，實際演出日都早於課綱所列日期。</p>
        <div class="actions">
          <a class="btn primary" href="{slug(cur)}/">{e(cur['code'])} 查證細節</a>
          {ext(syllabus_url(cur), "課綱", "btn ext")}
          {ext(SITE['links']['e3'], "E3 平台", "btn ext")}
        </div>
      </div>
    </div>
  </div>
</section>

<section class="section" id="latest" aria-labelledby="latest-h">
  <div class="wrap">
    <div class="section-head">
      <span class="eyebrow" lang="en">Latest performance</span>
      <h2 id="latest-h">最近一場・{e(latest['code'])}</h2>
      <p>{fmt_date(latest['show']['date'])} {e(latest['show']['time'])}，{e(latest['show']['venue'])}。<a href="{slug(latest)}/">曲目與來源</a></p>
    </div>
    {videos_block(latest['videos'][:1])}
  </div>
</section>

<section class="section" id="archive" aria-labelledby="archive-h">
  <div class="wrap">
    <div class="section-head">
      <span class="eyebrow" lang="en">{e(first['code'])} — {e(last['code'])}</span>
      <h2 id="archive-h">歷屆演出</h2>
      <p>課程時間表上查得到這門課的 {len(SEMESTERS)} 個學期。其中 {n_perf} 個學期的演出日期有公告或官方影片可以佐證，其餘只有課綱上排定的日期。</p>
    </div>
    <p class="legend" aria-hidden="true">
      <span class="status performed">{STATUS['performed']}：日期有公告或官方影片佐證</span>
      <span class="status scheduled">{STATUS['scheduled']}</span>
      <span class="status syllabus">{STATUS['syllabus']}：實際演出未查證</span>
    </p>
    <ul class="archive">
{chr(10).join(archive_row(s) for s in SEMESTERS)}
    </ul>
    <p class="footnote">學期代碼：A 是第 1 學期，B 是第 2 學期。{gaps} 在課程時間表上查不到這門課，所以沒有頁面。</p>
  </div>
</section>

<section class="section" id="about" aria-labelledby="about-h">
  <div class="wrap">
    <div class="section-head">
      <span class="eyebrow" lang="en">About this site</span>
      <h2 id="about-h">關於本站</h2>
    </div>
    <div class="about">
      <div class="prose">
        <h3>這是什麼</h3>
        <p>「{e(SITE['course_zh'])}」是{e(SITE['teacher'])}老師在陽明交大開設的選修課。課綱安排學期末分組合奏，每組自選爵士標準曲，每位同學都要在自己的樂器上即興，最後以 combo 成果發表收尾。</p>
        <p>本站是<strong>修課學生自己做的整理</strong>，把散在課綱、學程公告與官方影片裡的演出資訊收在一處，方便同學和想來聽的人查。</p>
        <p>版面的深色舞台感參考了{e(SITE['teacher'])}老師個人網站的公開設計，但沒有使用該站的圖像或標誌，也不代表老師認可本站。</p>
      </div>
      <div class="prose">
        <h3>怎麼查證</h3>
        <p>每一頁都把「課綱上排的日期」和「實際演出的日期」分開寫。只有找到活動公告、官方影片說明或影片畫面可以佐證時，才標為<strong>已演出</strong>；查不到的欄位直接寫未查證，不用推測補上。</p>
        <p>課綱日期不等於演出日期：114A、113B、112B 的實際演出分別比課綱所列日期早 21、14、8 天。</p>
        <h3>官方管道</h3>
        <ul class="linklist">
          <li>{ext(SITE['links']['youtube'], "<span>學程 YouTube 頻道</span><span>演出錄影 ↗</span>")}</li>
          <li>{ext(SITE['links']['facebook'], "<span>學程 Facebook 專頁</span><span>活動消息 ↗</span>")}</li>
          <li>{ext(SITE['links']['timetable'], "<span>陽明交大課程時間表</span><span>各學期課綱 ↗</span>")}</li>
          <li>{ext(SITE['links']['e3'], "<span>E3 數位教學平台</span><span>課程公告，需登入 ↗</span>")}</li>
        </ul>
      </div>
    </div>
  </div>
</section>"""

    return page(
        root="",
        path="/",
        title=f"{SITE['name']}｜陽明交大「{SITE['course_zh']}」期末演出紀錄",
        description=(
            f"陽明交大「{SITE['course_zh']}」歷屆期末 combo 成果演出的日期、地點與官方影片連結，"
            "由修課學生依課綱、學程公告與官方影片整理。"
        ),
        body=body,
    )


# ---------- 學期頁 ----------

def fact(label, value, basis="", unknown=False):
    cls = ' class="unknown"' if unknown else ""
    basis_html = f'<span class="basis">{e(basis)}</span>' if basis else ""
    return f'<div class="fact"><dt>{label}</dt><dd{cls}>{value}{basis_html}</dd></div>'


def split(heading_en, heading, inner, hid):
    return f"""<section class="section tight" aria-labelledby="{hid}">
  <div class="wrap split">
    <h2 id="{hid}"><span class="eyebrow" lang="en">{heading_en}</span>{heading}</h2>
    <div>
{inner}
    </div>
  </div>
</section>"""


def build_semester(index):
    sem = SEMESTERS[index]
    show = sem.get("show")
    syl = sem["syllabus_final"]
    root = "../"

    facts = []
    if show:
        facts.append(fact("演出日期", fmt_date(show["date"]), show.get("date_basis", "")))
        facts.append(
            fact("時間", e(show["time"]), show.get("time_basis", ""))
            if show.get("time")
            else fact("時間", "未查證", show.get("time_basis", ""), unknown=True)
        )
        facts.append(
            fact("地點", e(show["venue"]), show.get("venue_basis", ""))
            if show.get("venue")
            else fact("地點", "未查證", show.get("venue_basis", ""), unknown=True)
        )
    else:
        facts.append(fact("實際演出日期", "未查證", "沒有找到公告或官方說明", unknown=True))
        facts.append(fact("時間與地點", "未查證", "", unknown=True))
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

    if sem["videos"]:
        sections.append(split("Video", "演出影片", videos_block(sem["videos"]), "video-h"))

    if sem.get("program"):
        pieces = "\n".join(f"        <li>{e(p)}</li>" for p in sem["program"]["pieces"])
        sections.append(
            split(
                "Set list",
                "曲目",
                f'      <ol class="pieces">\n{pieces}\n      </ol>\n'
                f'      <p class="footnote">{e(sem["program"]["basis"])}</p>',
                "program-h",
            )
        )

    notes = "\n".join(f"        <li>{e(n)}</li>" for n in sem["notes"])
    sections.append(split("Notes", "查證說明", f'      <ul class="notes">\n{notes}\n      </ul>', "notes-h"))

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

    body = f"""<section class="term-hero">
  <div class="wrap">
    <a class="back" href="{root}#archive">← 歷屆演出</a>
    <span class="eyebrow" lang="en">{e(SITE['course_en'])}</span>
    <h1>{e(sem['code'])}</h1>
    <div class="term-sub">
      <span class="term-name">{term_name(sem)}・{e(SITE['course_zh'])}</span>
      {status_chip(sem)}
    </div>
    <p class="term-summary">{e(sem['summary'])}</p>
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
        description=f"陽明交大「{SITE['course_zh']}」{term_name(sem)}（{sem['code']}）：{sem['summary']}",
        body=body,
        current="current" if sem["code"] == SITE["current"] else "",
    )


def build_404():
    body = """<section class="lost">
  <div class="wrap">
    <span class="eyebrow" lang="en">Not found</span>
    <h1>404</h1>
    <p>沒有這一頁。可能是那個學期在課程時間表上查不到這門課，或是網址打錯了。</p>
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
