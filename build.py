#!/usr/bin/env python3
"""把 data/site.json 產生成靜態頁面。

用法：python3 build.py
只用 Python 3 標準函式庫。產生的 index.html、各學期資料夾、404.html、sitemap.xml
都直接放在 repo 根目錄並一起 commit，GitHub Pages 不需要任何建置步驟。
"""

import json
import re
from datetime import date, datetime, timezone
from hashlib import sha256
from html import escape
from pathlib import Path
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

import program_viewer

ROOT = Path(__file__).resolve().parent
DATA = json.loads((ROOT / "data" / "site.json").read_text(encoding="utf-8"))
SITE = DATA["site"]
SEMESTERS = DATA["semesters"]  # 由新到舊

WEEKDAYS = "一二三四五六日"
EN_WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
EN_MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
LANGUAGES = ("zh-Hant-TW", "en")
ROLE_EN = {
    "指導": "Instructor", "薩克斯風": "Saxophone", "口琴": "Harmonica", "口風琴": "Melodica",
    "大提琴": "Cello", "中提琴": "Viola", "人聲": "Vocals", "吉他": "Guitar",
    "鋼琴": "Piano", "貝斯": "Bass", "鼓": "Drums", "客席鼓手": "Guest drummer",
    "演出者": "Performers", "客席薩克斯風": "Guest saxophone",
    "電貝斯": "Electric bass",
    "半音階口琴": "Chromatic harmonica",
    "主奏": "Lead", "和聲伴奏": "Comping", "貝斯聲部": "Bass part",
    "鼓聲部": "Drum part", "助教": "Teaching assistant",
}
STATUSES = ("performed", "scheduled", "syllabus")
FONTS = (
    "https://fonts.googleapis.com/css2?family=Noticia+Text:ital@1"
    "&family=Noto+Sans+TC:wght@300;400;500&family=Raleway:wght@200;300&display=swap"
)

e = escape


# ---------- 小工具 ----------

def label(lang, zh, en):
    return en if lang == "en" else zh


def localized(record, key, lang):
    return record.get(f"{key}_en", record.get(key)) if lang == "en" else record.get(key)


def prefix(lang):
    return "en/" if lang == "en" else ""


def weekday_line(day, lang):
    return label(lang, f"{day.year} 年・星期{WEEKDAYS[day.weekday()]}", f"{EN_WEEKDAYS[day.weekday()]}, {day.year}")


def parse(iso):
    return date.fromisoformat(iso)


def fmt_date(iso, lang):
    d = parse(iso)
    if lang == "en":
        return f"{EN_WEEKDAYS[d.weekday()][:3]}, {EN_MONTHS[d.month - 1]} {d.day}, {d.year}"
    return f"{d.year}/{d.month}/{d.day}（{WEEKDAYS[d.weekday()]}）"


def term(sem):
    """'114A' -> (114, 1)"""
    m = re.fullmatch(r"(\d{3})([AB])", sem["code"])
    if not m:
        raise SystemExit(f"學期代碼格式錯誤：{sem['code']}")
    return int(m.group(1)), 1 if m.group(2) == "A" else 2


def term_name(sem, lang):
    acy, n = term(sem)
    if lang == "en":
        return f"Fall {acy + 1911}" if n == 1 else f"Spring {acy + 1912}"
    return f"{acy} 學年度第 {n} 學期"


def slug(sem):
    return sem["code"].lower()


def syllabus_url(sem, lang):
    acy, n = term(sem)
    course_lang = label(lang, "zh-tw", "en-us")
    return (
        "https://timetable.nycu.edu.tw/?r=main/crsoutline"
        f"&Acy={acy}&Sem={n}&CrsNo={sem['crs_no']}&lang={course_lang}"
    )


def youtube_url(video):
    url = f"https://www.youtube.com/watch?v={video['id']}"
    return url + (f"&list={video['list']}" if video.get("list") else "")


def ext(url, text, cls="", *, lang):
    """外部連結：一律新分頁並標示。"""
    cls_attr = f' class="{cls}"' if cls else ""
    return (
        f'<a{cls_attr} href="{e(url)}" target="_blank" rel="noopener">'
        f'{text}<span class="visually-hidden">{label(lang, "（另開新分頁）", " (opens in a new tab)")}</span></a>'
    )


def map_url(query):
    return "https://www.google.com/maps/search/?" + urlencode({"api": 1, "query": query})


def by_code(code):
    return next(s for s in SEMESTERS if s["code"] == code)


# ---------- 共用版型 ----------

def program_asset(root, filename):
    path = f"assets/{filename}"
    version = sha256((ROOT / path).read_bytes()).hexdigest()[:12]
    return f"{root}{path}?v={version}"


def page(*, lang, root, path, title, description, body, current="", has_program_viewer=False):
    base = SITE["url"].rstrip("/") + "/"
    alternate = "zh-Hant-TW" if lang == "en" else "en"
    relative_path = path.lstrip("/")
    canonical = base + prefix(lang) + relative_path
    home = root + prefix(lang) or "./"
    alternate_href = root + prefix(alternate) + relative_path or "./"
    alternate_text = label(lang, "English", "中文")
    home_name = label(lang, "NYCU Jazz 首頁", "NYCU Jazz home")
    repository = SITE["repository"].rstrip("/")
    program_css = f'\n<link rel="stylesheet" href="{program_asset(root, "program-viewer.css")}">' if has_program_viewer else ''
    program_js = f'\n<script src="{program_asset(root, "program-viewer.js")}" defer></script>' if has_program_viewer else ''

    def nav(href, label, key):
        cur = ' aria-current="page"' if key == current else ""
        return f'<a href="{href}"{cur}>{label}</a>'

    return f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(description)}">
<link rel="canonical" href="{e(canonical)}">
<link rel="alternate" hreflang="zh-Hant-TW" href="{e(base + relative_path)}">
<link rel="alternate" hreflang="en" href="{e(base + "en/" + relative_path)}">
<link rel="alternate" hreflang="x-default" href="{e(base + relative_path)}">
<meta property="og:type" content="website">
<meta property="og:locale" content="{label(lang, "zh_TW", "en_US")}">
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
<link rel="stylesheet" href="{root}assets/site.css">{program_css}
</head>
<body>
<a class="skip" href="#main">{label(lang, "跳到主要內容", "Skip to main content")}</a>
<header class="site-header">
  <div class="wrap">
    <a class="brand" href="{home}" aria-label="{home_name}">NYCU <b>Jazz</b></a>
    <nav class="nav" aria-label="{label(lang, "主要導覽", "Main navigation")}">
      {nav(f"{home}{slug(by_code(SITE['current']))}/", label(lang, "本學期", "This semester"), "current")}
      {nav(f"{home}#archive", label(lang, "歷屆演出", "Past performances"), "archive")}
      <a class="language-switch" href="{e(alternate_href)}" hreflang="{alternate}" lang="{alternate}">{alternate_text}</a>
    </nav>
  </div>
</header>
<main id="main">
{body}
</main>
<footer class="site-footer">
  <div class="wrap">
    <a class="brand" href="{home}" aria-label="{home_name}">NYCU <b>Jazz</b></a>
    <nav class="footer-links" aria-label="{label(lang, "頁尾導覽", "Footer navigation")}">
      {ext(repository, "GitHub", lang=lang)}
    </nav>
  </div>
</footer>
<script src="{root}assets/site.js" defer></script>{program_js}
</body>
</html>
"""


# ---------- 影片 ----------

def video_poster(video, root):
    if thumbnail := video.get("thumbnail"):
        return root + thumbnail
    if video["type"] == "youtube":
        return f"https://i.ytimg.com/vi/{video['id']}/hqdefault.jpg"
    return ""


def video_block(video, root, lang):
    title = e(localized(video, "title", lang))
    poster = video_poster(video, root)
    if video["type"] == "youtube":
        url = youtube_url(video)
        player = f' data-yt="{e(video["id"])}"'
        if playlist := video.get("list"):
            player += f' data-list="{e(playlist)}"'
    else:
        url = video["url"]
        player = " data-fb"
    preview = ""
    if poster:
        width, height = (480, 360) if video["type"] == "youtube" and not video.get("thumbnail") else (1120, 630)
        preview = f"""
    <span class="video-frame">
      <img src="{e(poster)}" alt="" width="{width}" height="{height}" loading="lazy" decoding="async">
      <span class="play" aria-hidden="true"></span>
    </span>"""
    return f"""<a class="video-card" href="{e(url)}" target="_blank" rel="noopener"{player} data-title="{title}" aria-label="{label(lang, "播放：", "Play: ")}{title}">{preview}
    <span class="video-title">{title}</span>
  </a>"""


def videos_block(videos, root, lang):
    two = " two" if len(videos) > 1 else ""
    return f'<div class="videos{two}">\n' + "\n".join(video_block(v, root, lang) for v in videos) + "\n</div>"


def has_event_details(sem):
    return bool(
        sem.get("show")
        or (sem.get("program") or {}).get("pieces")
        or sem["videos"]
        or sem.get("credits_by_role")
    )


# ---------- 首頁 ----------

def archive_row(sem, root, lang, latest=False):
    date_display = ""
    if show := sem.get("show"):
        date_iso = show["date"]
        time = f'<span>{e(show["time"])}</span>' if show.get("time") else ""
        venue_name = localized(show, "venue", lang)
        venue = f'\n          <small>{e(venue_name)}</small>' if venue_name else ""
        date_display = f"""
        <span class="archive-date">
          <span><time datetime="{e(date_iso)}">{fmt_date(date_iso, lang)}</time>{time}</span>{venue}
        </span>"""
    section_id = ' id="latest"' if latest else ""
    videos = sem["videos"]
    recordings = ""
    if videos:
        recordings = f'\n      <div class="archive-recordings">{videos_block(videos, root, lang)}</div>'
    term_label = f'<span class="archive-term"><strong>{e(sem["code"])}</strong></span>'
    if has_event_details(sem):
        row = f"""<a class="archive-row" href="{slug(sem)}/">
        {term_label}{date_display}
        <span class="archive-more">{label(lang, "場次資訊", "Event details")} <span aria-hidden="true">→</span></span>
      </a>"""
    else:
        row = f'<div class="archive-row">{term_label}</div>'
    return f"""    <li{section_id}>
      {row}{recordings}
    </li>"""


def build_home(lang):
    root = "../" if lang == "en" else ""
    cur = by_code(SITE["current"])
    cur_show = cur.get("show") or {}
    event_date = ""
    if cur_show:
        cur_final = parse(cur_show["date"])
        event_date = f"""
      <time class="event-date" datetime="{cur_final.isoformat()}">
        <span class="event-day">{cur_final.month:02d}<span>/</span>{cur_final.day:02d}</span>
        <span class="event-weekday">{weekday_line(cur_final, lang)}</span>
      </time>"""
    time = e(cur_show.get("time") or label(lang, "時間待公布", "Time to be announced"))
    venue = e(localized(cur_show, "venue", lang) or label(lang, "地點待公布", "Venue to be announced"))
    if query := cur_show.get("map_query"):
        venue = ext(map_url(query), venue, "ext event-map", lang=lang)
    event_label = label(lang, "下一場演出", "Upcoming performance") if cur["status"] == "scheduled" else label(lang, "本學期演出", "This semester’s performance")
    program = cur.get("program", {}).get("pieces", [])
    primary_url = f"{slug(cur)}/"
    primary_label = label(lang, "查看演出資訊", "View event details")
    if program:
        primary_url += "#program-h"
        has_credits = cur.get("credits_by_role") or any(isinstance(piece, dict) and piece.get("performers") for piece in program)
        primary_label = label(lang, "查看曲目與演出者", "View the program and performers") if has_credits else label(lang, "查看曲目", "View the program")
    archive = "\n".join(archive_row(s, root, lang, latest=s["code"] == SITE["latest_show"]) for s in SEMESTERS)

    teacher_link = ext(SITE["teacher_url"], e(SITE["teacher"]), lang=lang)
    if lang == "en":
        intro = (
            f"Professor {teacher_link} of the Institute of Music first offered "
            "Jazz Harmony, Improvisation and Ensemble in spring 2020. In Room EE115 of "
            "Engineering Building V, students learn to swing, work with jazz harmony, "
            "and improvise together on their own instruments. Later in the semester, "
            "they choose jazz standards in small groups and prepare to perform."
        )
        site_note = "Students in the course built and maintain this site. For more information, see the "
        course_link = "course syllabus"
    else:
        intro = (
            f"2020 年春季，音樂研究所的{teacher_link}老師開了《{e(SITE['course_zh'])}》。"
            "在工程五館 EE115，同學從搖擺節奏和爵士和聲入手，學著用自己的樂器跟別人一起即興。"
            "到了學期後段，大家分組挑自己想演的爵士標準曲，準備期末上台。"
        )
        site_note = "本網頁為修課學生自行開發部署。更多課程資訊請見"
        course_link = "課程網頁"

    body = f"""<section class="hero" id="now" aria-labelledby="now-h">
  <div class="wrap hero-layout">
    <div class="hero-copy">
      <h1 id="now-h" lang="en">NYCU <span>Jazz</span></h1>
      <p class="lede">{e(SITE[label(lang, "course_zh", "course_en")])}</p>
    </div>
    <div class="hero-event">
      <p class="eyebrow event-label">{event_label}</p>
      <h2 class="event-title">{label(lang, "爵士期末成果發表", "End-of-Semester Jazz Concert")}</h2>{event_date}
      <p class="event-details"><strong>{time}</strong>{venue}</p>
      <a class="btn primary event-cta" href="{primary_url}">{primary_label}<span aria-hidden="true">→</span></a>
    </div>
    <section class="course-intro" aria-labelledby="intro-h">
      <h2 id="intro-h">{label(lang, "誰說新竹沒有爵士樂？", "Who Says There’s No Jazz in Hsinchu?")}</h2>
      <p>{intro}</p>
      <p>{site_note}{ext(syllabus_url(cur, lang), course_link, lang=lang)}{label(lang, "。", ".")}</p>
    </section>
  </div>
</section>

<section class="section" id="archive" aria-labelledby="archive-h">
  <div class="wrap">
    <div class="section-head">
      <h2 id="archive-h">{label(lang, "歷屆演出", "Past Performances")}</h2>
    </div>
    <ul class="archive">
{archive}
    </ul>
  </div>
</section>"""

    return page(
        lang=lang,
        root=root,
        path="/",
        title=label(lang, f"{SITE['name']}｜陽明交大「{SITE['course_zh']}」期末演出紀錄", "NYCU Jazz | Student Concerts and Course Information"),
        description=label(lang, f"陽明交大「{SITE['course_zh']}」歷屆期末成果發表的日期、曲目與影片。", "Concert dates, programs, performers, and recordings from NYCU’s Jazz Harmony, Improvisation and Ensemble course."),
        body=body,
    )


# ---------- 學期頁 ----------

def fact(label, value):
    return f'<div class="fact"><dt>{e(label)}</dt><dd>{e(value)}</dd></div>'


def split(heading_en, heading, inner, hid, lang, layout="split"):
    eyebrow = f'<span class="eyebrow" lang="en">{heading_en}</span>' if lang != "en" else ""
    return f"""<section class="section tight" aria-labelledby="{hid}">
  <div class="wrap {layout}">
    <h2 id="{hid}">{eyebrow}{label(lang, heading, heading_en)}</h2>
    <div>
{inner}
    </div>
  </div>
</section>"""


def performer_credit(performer, lang):
    if isinstance(performer, str):
        return e(performer)
    instrument = performer["instrument"]
    instrument = ROLE_EN.get(instrument, instrument) if lang == "en" else instrument
    return e(performer["name"] + label(lang, f"（{instrument}）", f" ({instrument})"))


def program_block(program, lang):
    rows = []
    ordered = program.get("ordered", False)
    for number, piece in enumerate(program["pieces"], start=1):
        if isinstance(piece, str):
            piece = {"title": piece}
        title = f'<span class="piece-title">{e(localized(piece, "title", lang))}</span>'
        number_html = f'<span class="piece-number" aria-hidden="true">{number:02d}</span>' if ordered else ""
        cue = piece.get("cue", "")
        if lang == "en" and cue.startswith("約 "):
            cue = "Approx. " + cue.removeprefix("約 ")
        timestamp = f'<span class="piece-time">{e(cue)}</span>' if cue else ""
        if piece.get("url"):
            entry = ext(
                piece["url"],
                f'{title}{timestamp}<span class="piece-watch">{label(lang, "觀看", "Watch")}</span>',
                "piece-content",
                lang=lang,
            )
        else:
            entry = f'<div class="piece-content">{title}{timestamp}</div>'
        captions = []
        if performers := piece.get("performers"):
            names = label(lang, "、", ", ").join(performer_credit(performer, lang) for performer in performers)
            captions.append(f'<p class="piece-performers">{names}</p>')
        if captions:
            entry = f'<div>{entry}{"".join(captions)}</div>'
        rows.append(f"        <li>{number_html}{entry}</li>")
    list_html = ""
    if rows:
        tag = "ol" if ordered else "ul"
        style = "pieces lineup ordered" if ordered else "pieces lineup"
        list_html = f'      <{tag} class="{style}" role="list">\n' + "\n".join(rows) + f"\n      </{tag}>\n"
    if source := program.get("source"):
        list_html += f'      <p class="footnote">{ext(source["url"], e(localized(source, "label", lang)), lang=lang)}</p>'
    return split("Program", "演出曲目", list_html, "program-h", lang, "split lineup-layout")


def credits_block(roles, lang):
    separator = label(lang, "、", ", ")
    rows = "\n".join(
        f'<div class="credit-row"><dt>{e(ROLE_EN.get(role, role) if lang == "en" else role)}</dt><dd>{separator.join(e(name) for name in names)}</dd></div>'
        for role, names in roles.items()
    )
    return f"""
  <section class="section credits" aria-labelledby="credits-h">
    <div class="wrap split">
      <h2 id="credits-h">{label(lang, "演出名單", "Performers")}</h2>
      <dl class="credit-list">
        {rows}
      </dl>
    </div>
  </section>"""


def calendar_url(sem, title, lang):
    show = sem.get("show") or {}
    times = re.fullmatch(r"(\d{2}:\d{2})\s*[–-]\s*(\d{2}:\d{2})", show.get("time") or "")
    if not times or not show.get("date"):
        return ""
    try:
        start, end = [
            datetime.fromisoformat(f"{show['date']}T{value}").replace(tzinfo=ZoneInfo("Asia/Taipei"))
            for value in times.groups()
        ]
    except ValueError:
        return ""
    if end <= start:
        return ""
    dates = "/".join(value.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ") for value in (start, end))
    return "https://calendar.google.com/calendar/render?" + urlencode({
        "action": "TEMPLATE",
        "text": title,
        "dates": dates,
        "ctz": "Asia/Taipei",
        "location": localized(show, "venue", lang) or "",
        "details": f"{SITE['url'].rstrip('/')}/{prefix(lang)}{slug(sem)}/",
    })


def album_collage(program, root, lang, interactive=False):
    covers = []
    for piece in program.get("pieces", []):
        if not isinstance(piece, dict) or not (album := piece.get("album")):
            continue
        caption = label(
            lang,
            f"〈{piece['title']}〉・{album['artist']}《{album['title']}》",
            f"{localized(piece, 'title', lang)} by {album['artist']} from {album['title']}",
        )
        image = f'<img src="{e(root + album["cover"])}" width="480" height="480" alt="" decoding="async">'
        if interactive:
            control = program_viewer.cover_button(Path(album['cover']).stem, caption, image, lang)
            covers.append(f'        <li>{control}</li>')
            continue
        covers.append(
            f'        <li><a href="{e(album["url"])}" target="_blank" rel="noopener" '
            f'title="{e(caption)}" aria-label="{e(caption)}{label(lang, "（另開新分頁）", " (opens in a new tab)")}">{image}</a></li>'
        )
    if not covers:
        return ""
    layout = "album-grid album-grid--ten" if len(covers) == 10 else "album-grid"
    return f"""
      <figure class="concert-visual" aria-label="{label(lang, "曲目專輯封面", "Album covers for the program")}">
        <ul class="{layout}" role="list">
{chr(10).join(covers)}
        </ul>
      </figure>"""


def build_semester(index, lang):
    sem = SEMESTERS[index]
    root = "../" if lang != "en" else "../../"
    show = sem.get("show") or {}
    program = sem.get("program") or {}
    details_file = program.get("details")
    videos = sem["videos"]
    roles = sem.get("credits_by_role")
    title = label(lang, "陽明交大爵士期末成果發表", "NYCU End-of-Semester Jazz Concert")

    date_html = ""
    if date_iso := show.get("date"):
        day = parse(date_iso)
        month_day = f'{day.month:02d}<span>/</span>{day.day:02d}'
        weekday = weekday_line(day, lang)
        date_html = f"""
        <time class="concert-date" datetime="{day.isoformat()}">
          <span class="concert-day">{month_day}</span>
          <span class="concert-weekday">{weekday}</span>
        </time>"""

    facts = [
        fact(label(lang, zh, en), localized(show, key, lang))
        for key, zh, en in (("time", "演出時間", "Time"), ("venue", "地點", "Venue"), ("admission", "入場", "Admission"))
        if localized(show, key, lang)
    ]
    facts_html = f'\n      <dl class="concert-facts">{"".join(facts)}</dl>' if facts else ""
    actions = []
    sections = []
    if program.get("pieces"):
        if details_file:
            details = json.loads((ROOT / "data" / details_file).read_text(encoding="utf-8"))
            sections.append(program_viewer.render(program, details, root, sem["code"], lang, ROLE_EN))
        else:
            sections.append(f'<div class="concert-program">{program_block(program, lang)}</div>')
            actions.append(f'<a class="btn primary" href="#program-h">{label(lang, "看曲目", "Program")} <span aria-hidden="true">↓</span></a>')
    if roles:
        sections.append(credits_block(roles, lang))
        if not details_file:
            actions.append(f'<a class="btn" href="#credits-h">{label(lang, "看演出名單", "Performers")}</a>')
    if videos:
        sections.append(f"""<section class="section tight" id="video-h" aria-label="{label(lang, "影片", "Recordings")}">
  <div class="wrap">
    {videos_block(videos, root, lang)}
  </div>
</section>""")
    if query := show.get("map_query"):
        actions.append(ext(map_url(query), label(lang, "地圖導航", "Directions"), "btn ext", lang=lang))
    if sem["status"] == "scheduled" and (calendar := calendar_url(sem, title, lang)):
        actions.append(ext(calendar, label(lang, "加入 Google 日曆", "Add to Google Calendar"), "btn ext", lang=lang))
    actions_html = f'\n      <nav class="concert-actions" aria-label="{label(lang, "演出導覽", "Concert navigation")}">{"".join(actions)}</nav>' if actions else ""

    visual = album_collage(program, root, lang, interactive=bool(details_file))
    if not visual and videos and (poster := video_poster(videos[0], root)):
        visual = f"""
      <a class="concert-visual video-frame" href="#video-h" aria-label="{label(lang, "前往播放器", "Go to the player")}">
        <img src="{e(poster)}" alt="" decoding="async">
        <span class="play" aria-hidden="true"></span>
      </a>"""

    if sources := sem.get("sources"):
        src_html = "\n".join(
            f'        <li><div>{ext(source["url"], e(localized(source, "label", lang)), lang=lang)}<small>{e(localized(source, "publisher", lang))}</small></div></li>'
            for source in sources
        )
        sections.append(split("Sources", "資料來源", f'      <ol class="sources">\n{src_html}\n      </ol>', "sources-h", lang))

    newer = next((term for term in reversed(SEMESTERS[:index]) if has_event_details(term)), None)
    older = next((term for term in SEMESTERS[index + 1:] if has_event_details(term)), None)
    pager_newer = (
        f'<a href="{root}{prefix(lang)}{slug(newer)}/" rel="next"><small>{label(lang, "← 較新的學期", "← Newer semester")}</small><b>{e(newer["code"])}</b></a>'
        if newer
        else '<span class="empty"></span>'
    )
    pager_older = (
        f'<a href="{root}{prefix(lang)}{slug(older)}/" rel="prev"><small>{label(lang, "較早的學期 →", "Earlier semester →")}</small><b>{e(older["code"])}</b></a>'
        if older
        else f'<a href="{root}{prefix(lang)}#archive"><small>{label(lang, "回到列表 →", "Back to the archive →")}</small><b>{label(lang, "歷屆演出", "Past Performances")}</b></a>'
    )

    body = f"""<section class="concert-hero" aria-labelledby="concert-title">
  <div class="wrap concert-layout">
    <div class="concert-copy">
      <div class="concert-kicker">
        <p>{e(SITE[label(lang, "course_zh", "course_en")])} <span>{label(lang, f"{e(SITE['teacher'])}教授", f"Professor {e(SITE['teacher'])}")}</span></p>
        {ext(syllabus_url(sem, lang), label(lang, "課程綱要", "Course syllabus"), "ext", lang=lang)}
      </div>
      <h1 id="concert-title">{label(lang, "爵士期末<br>成果發表", "End-of-Semester<br>Jazz Concert")}</h1>
      <p class="concert-term">{term_name(sem, lang)}</p>{date_html}{facts_html}{actions_html}
    </div>{visual}
  </div>
</section>

{chr(10).join(sections)}

<nav class="pager wrap" aria-label="{label(lang, "前後學期", "Semester navigation")}">
  {pager_newer}
  {pager_older}
</nav>"""

    return page(
        lang=lang,
        root=root,
        path=f"/{slug(sem)}/",
        title=label(lang, f"{sem['code']} 期末演出｜{SITE['name']}", f"{sem['code']} Jazz Concert | {SITE['name']}"),
        description=label(lang, f"陽明交大「{SITE['course_zh']}」{term_name(sem, lang)}（{sem['code']}）期末成果發表。", f"{term_name(sem, lang)} ({sem['code']}) for NYCU’s Jazz Harmony, Improvisation and Ensemble course."),
        body=body,
        current="current" if sem["code"] == SITE["current"] else "",
        has_program_viewer=bool(details_file),
    )


def build_404(lang):
    home = "/" + prefix(lang)
    body = f"""<section class="lost">
  <div class="wrap">
    <span class="eyebrow" lang="en">Not found</span>
    <h1>404</h1>
    <p>{label(lang, "找不到這個頁面。", "This page could not be found.")}</p>
    <div class="actions"><a class="btn primary" href="{home}#archive">{label(lang, "看歷屆演出", "Past performances")}</a><a class="btn" href="{home}">{label(lang, "回首頁", "Home")}</a></div>
  </div>
</section>"""
    return page(lang=lang, root="/", path="/404.html", title=label(lang, "找不到頁面｜NYCU Jazz", "Page not found | NYCU Jazz"), description=label(lang, "找不到這個頁面。", "This page could not be found."), body=body)


def build_sitemap():
    base = SITE["url"].rstrip("/")
    paths = [""] + [f"{slug(s)}/" for s in SEMESTERS]
    urls = [f"{base}/{prefix(lang)}{path}" for lang in LANGUAGES for path in paths]
    items = "\n".join(f"  <url><loc>{u}</loc></url>" for u in urls)
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{items}\n</urlset>\n'


def main():
    codes = [s["code"] for s in SEMESTERS]
    if len(set(codes)) != len(codes):
        raise SystemExit("學期代碼重複")
    for s in SEMESTERS:
        if s["status"] not in STATUSES:
            raise SystemExit(f"{s['code']}：status 必須是 {list(STATUSES)}")
        if s["status"] == "performed" and not s.get("show"):
            raise SystemExit(f"{s['code']}：performed 必須填 show")

    out = {"sitemap.xml": build_sitemap()}
    for lang in LANGUAGES:
        out[f"{prefix(lang)}index.html"] = build_home(lang)
        out[f"{prefix(lang)}404.html"] = build_404(lang)
        for i, semester in enumerate(SEMESTERS):
            out[f"{prefix(lang)}{slug(semester)}/index.html"] = build_semester(i, lang)
    for rel, text in out.items():
        target = ROOT / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    (ROOT / ".nojekyll").touch()
    print(f"已產生 {len(out)} 個檔案：{'、'.join(sorted(out))}")


if __name__ == "__main__":
    main()
