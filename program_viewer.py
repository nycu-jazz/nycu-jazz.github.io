import re
from html import escape
from pathlib import Path
from urllib.parse import parse_qs, urlsplit


def cover_button(slug, caption, image, lang):
    description = 'Album cover and listening notes' if lang == 'en' else '專輯封面與延伸閱讀'
    return f'<button type="button" class="viewer-trigger cover-trigger" data-image="cover-{slug}" aria-haspopup="dialog" aria-controls="score-dialog" aria-label="{escape(caption)} · {description}">{image}</button>'


def lineup_html(performers, role_en, rotating, lang):
    entries = []
    for performer in performers:
        name = escape(performer['name'])
        instrument = performer['instrument']
        if lang == 'en':
            instrument = role_en.get(instrument, instrument)
        entries.append(f'<span class="player"><span class="instrument">{escape(instrument)}</span><span class="name">{name}</span></span>')
    if rotating:
        note = '... + rotating improvisers' if lang == 'en' else '... +輪流即興'
        entries.append(f'<span class="hint ensemble-note">{note}</span>')
    return ' '.join(entries)


def album_template(slug, piece, info, root, lang):
    english = lang == 'en'
    title = escape(piece.get('title_en', piece['title']) if english else piece['title'])
    album = piece['album']
    album_title = escape(album['title'])
    artist = escape(album['artist'])
    cover = escape(root + album['cover'])
    cover_label = 'album cover' if english else '專輯封面'
    source = info['source']
    source_url = escape(source['url'])
    publication = source['publication'].replace('，引自 ', ', via ') if english else source['publication']
    quote = info['quote']
    original = quote['lang'], quote['original']
    translated = ('en' if quote['lang'].startswith('zh') else 'zh-Hant-TW'), quote['translation']
    primary, secondary = (original, translated) if original[0] == lang else (translated, original)
    video_url = urlsplit(album['url'])
    video_id = parse_qs(video_url.query).get('v', [''])[0]
    if video_url.hostname != 'www.youtube.com' or not re.fullmatch(r'[A-Za-z0-9_-]{11}', video_id):
        raise ValueError(f'Invalid YouTube video URL for {slug}')
    play = 'Play video' if english else '播放影片'
    return f'''<template id="cover-{slug}"><article class="album-view">
  <img src="{cover}" width="480" height="480" alt="{album_title} {cover_label}">
  <div><h2>{title}</h2><p class="album-credit">{album_title}<br>{artist}</p>
    <figure class="tune-reference"><blockquote cite="{source_url}"><div lang="{escape(primary[0])}">{escape(primary[1])}</div><p class="reference-secondary" lang="{escape(secondary[0])}">{escape(secondary[1])}</p></blockquote>
      <figcaption><cite><a href="{source_url}" title="{escape(source['title'])}" target="_blank" rel="noopener noreferrer">{escape(publication)} ↗</a></cite></figcaption>
    </figure>
    <div class="album-video"><button type="button" aria-label="{play} · {title}" data-video-id="{video_id}" data-player-title="YouTube · {title}"><img src="https://i.ytimg.com/vi/{video_id}/hqdefault.jpg" alt="" width="480" height="360" loading="lazy" decoding="async"></button></div>
  </div>
</article></template>'''


def score_template(slug, title, sheets, sheet_root, lang):
    figures = []
    for number, sheet in enumerate(sheets, 1):
        alt = f'{title} sheet music, page {number}' if lang == 'en' else f'{title} 曲譜第 {number} 頁'
        lazy = ' loading="lazy"' if number > 1 else ''
        path = escape(sheet_root + sheet['file'])
        figures.append(f'<figure class="score-page"><img src="{path}" width="{sheet["width"]}" height="{sheet["height"]}" alt="{escape(alt)}"{lazy}></figure>')
    return f'<template id="score-{slug}">{"".join(figures)}</template>'


def dialog(lang):
    labels = (
        ('Image viewer', 'Close viewer', 'View sheet music', 'Sheet music zoom', 'Zoom out', 'Reset to full-page size', 'Zoom in')
        if lang == 'en' else ('圖片預覽', '關閉預覽', '檢視圖片', '曲譜縮放', '縮小', '重設為整頁大小', '放大')
    )
    title, close, score, zoom, smaller, reset, larger = labels
    return f'''<dialog class="score-dialog" id="score-dialog" aria-label="{title}">
  <form method="dialog"><button class="score-close" aria-label="{close}">×</button></form>
  <div class="score-scroll" tabindex="0" aria-label="{score}"><div class="score-pages"></div></div>
  <div class="album-scroll" tabindex="0" hidden></div>
  <div class="score-zoom" role="group" aria-label="{zoom}">
    <button type="button" data-zoom="out" aria-label="{smaller}">−</button>
    <button type="button" data-zoom="reset" aria-label="{reset}">100%</button>
    <button type="button" data-zoom="in" aria-label="{larger}">+</button>
  </div>
</dialog>'''


def render(program, details, root, semester, lang, role_en):
    english = lang == 'en'
    eyebrow, heading = (escape(semester), 'Program') if english else ('Program', '演出曲目')
    score_label = 'Sheet music' if english else '曲譜'
    rows, templates = [], []
    sheet_root = f'{root}assets/sheets/{semester.lower()}/'
    for number, piece in enumerate(program['pieces'], 1):
        album = piece['album']
        slug = Path(album['cover']).stem
        info = details[slug]
        title = piece.get('title_en', piece['title']) if english else piece['title']
        escaped_title = escape(title)
        composer = escape(info['composer'])
        cover = f'<img class="cover" src="{escape(root + album["cover"])}" alt="" width="56" height="56">'
        cover_control = cover_button(slug, title, cover, lang)
        score_control = f'<button type="button" class="viewer-trigger score-trigger" aria-haspopup="dialog" aria-controls="score-dialog" data-image="score-{slug}" aria-label="{escaped_title} · {score_label}"><strong class="song" lang="en">{escaped_title}</strong><span class="composer">{composer}</span></button>'
        lineup = lineup_html(piece['performers'], role_en, info.get('rotating_improvisers'), lang)
        rows.append(f'<li id="{slug}"><div class="card-top"><span class="number">{number:02d}</span>{cover_control}{score_control}</div><div class="players">{lineup}</div></li>')
        templates.append(score_template(slug, title, info['sheets'], sheet_root, lang))
        templates.append(album_template(slug, piece, info, root, lang))
    return f'''<section class="program-preview" aria-labelledby="program-h"><div class="wrap b2 sheets">
  <div class="mast"><div><p class="eyebrow">{eyebrow}</p><h2 id="program-h">{heading}</h2></div></div>
  <ol class="set" role="list">{chr(10).join(rows)}</ol>
</div></section>
{chr(10).join(templates)}
{dialog(lang)}'''
