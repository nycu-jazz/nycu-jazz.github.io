import re
from html import escape
from pathlib import Path
from urllib.parse import parse_qs, urlsplit


def cover_button(slug, caption, image):
    return f'<button type="button" class="viewer-trigger cover-trigger" data-image="cover-{slug}" aria-haspopup="dialog" aria-controls="score-dialog" aria-label="{escape(caption)} · 專輯封面與延伸閱讀">{image}</button>'


def lineup_html(performers, rotating):
    entries = []
    for performer in performers:
        name = escape(performer['name'])
        instrument = performer['instrument']
        entries.append(f'<span class="player"><span class="instrument">{escape(instrument)}</span><span class="name">{name}</span></span>')
    if rotating:
        entries.append('<span class="hint ensemble-note">... +輪流即興</span>')
    return ' '.join(entries)


def album_template(slug, piece, info, root):
    title = escape(piece['title'])
    album = piece['album']
    album_title = escape(album['title'])
    artist = escape(album['artist'])
    cover = escape(root + album['cover'])
    source = info['source']
    source_url = escape(source['url'])
    publication = source['publication']
    quote = escape(info['quote'])
    video_url = urlsplit(album['url'])
    video_id = parse_qs(video_url.query).get('v', [''])[0]
    if video_url.hostname != 'www.youtube.com' or not re.fullmatch(r'[A-Za-z0-9_-]{11}', video_id):
        raise ValueError(f'Invalid YouTube video URL for {slug}')
    return f'''<template id="cover-{slug}"><article class="album-view">
  <img src="{cover}" width="480" height="480" alt="{album_title} 專輯封面">
  <div><h2>{title}</h2><p class="album-credit">{album_title}<br>{artist}</p>
    <figure class="tune-reference"><blockquote cite="{source_url}">{quote}</blockquote>
      <figcaption><cite><a href="{source_url}" title="{escape(source['title'])}" target="_blank" rel="noopener noreferrer">{escape(publication)} ↗</a></cite></figcaption>
    </figure>
    <div class="album-video"><button type="button" aria-label="播放影片 · {title}" data-video-id="{video_id}" data-player-title="YouTube · {title}"><img src="https://i.ytimg.com/vi/{video_id}/hqdefault.jpg" alt="" width="480" height="360" loading="lazy" decoding="async"></button></div>
  </div>
</article></template>'''


def score_template(slug, title, sheets, sheet_root):
    figures = []
    for number, sheet in enumerate(sheets, 1):
        alt = f'{title} 曲譜第 {number} 頁'
        lazy = ' loading="lazy"' if number > 1 else ''
        path = escape(sheet_root + sheet['file'])
        figures.append(f'<figure class="score-page"><img src="{path}" width="{sheet["width"]}" height="{sheet["height"]}" alt="{escape(alt)}"{lazy}></figure>')
    return f'<template id="score-{slug}">{"".join(figures)}</template>'


def dialog():
    return '''<dialog class="score-dialog" id="score-dialog" aria-label="圖片預覽">
  <form method="dialog"><button class="score-close" aria-label="關閉預覽">×</button></form>
  <div class="score-scroll" tabindex="0" aria-label="檢視圖片"><div class="score-pages"></div></div>
  <div class="album-scroll" tabindex="0" hidden></div>
  <div class="score-zoom" role="group" aria-label="曲譜縮放">
    <button type="button" data-zoom="out" aria-label="縮小">−</button>
    <button type="button" data-zoom="reset" aria-label="重設為整頁大小">100%</button>
    <button type="button" data-zoom="in" aria-label="放大">+</button>
  </div>
</dialog>'''


def render(program, details, root, semester):
    rows, templates = [], []
    sheet_root = f'{root}assets/sheets/{semester.lower()}/'
    for number, piece in enumerate(program['pieces'], 1):
        album = piece['album']
        slug = Path(album['cover']).stem
        info = details[slug]
        title = piece['title']
        escaped_title = escape(title)
        composer = escape(info['composer'])
        cover = f'<img class="cover" src="{escape(root + album["cover"])}" alt="" width="56" height="56">'
        cover_control = cover_button(slug, title, cover)
        score_control = f'<button type="button" class="viewer-trigger score-trigger" aria-haspopup="dialog" aria-controls="score-dialog" data-image="score-{slug}" aria-label="{escaped_title} · 曲譜"><strong class="song" lang="en">{escaped_title}</strong><span class="composer">{composer}</span></button>'
        lineup = lineup_html(piece['performers'], info.get('rotating_improvisers'))
        rows.append(f'<li id="{slug}"><div class="card-top"><span class="number">{number:02d}</span>{cover_control}{score_control}</div><div class="players">{lineup}</div></li>')
        templates.append(score_template(slug, title, info['sheets'], sheet_root))
        templates.append(album_template(slug, piece, info, root))
    return f'''<section class="program-preview" aria-labelledby="program-h"><div class="wrap b2 sheets">
  <div class="mast"><h2 id="program-h">演出曲目</h2></div>
  <ol class="set" role="list">{chr(10).join(rows)}</ol>
</div></section>
{chr(10).join(templates)}
{dialog()}'''
