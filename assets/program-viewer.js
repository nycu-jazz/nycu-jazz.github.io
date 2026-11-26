const viewer = document.querySelector('#score-dialog');
const scoreScroll = viewer.querySelector('.score-scroll');
const scorePages = viewer.querySelector('.score-pages');
const albumScroll = viewer.querySelector('.album-scroll');
const zoomControls = viewer.querySelector('.score-zoom');
const zoomOut = zoomControls.querySelector('[data-zoom="out"]');
const zoomReset = zoomControls.querySelector('[data-zoom="reset"]');
const zoomIn = zoomControls.querySelector('[data-zoom="in"]');
const minZoom = .5;
const maxZoom = 4;
let zoom = 1;
let openedBy;
let pinch;

const clamp = (value, lower, upper) => Math.min(upper, Math.max(lower, value));

function layoutScore() {
  const viewportWidth = scoreScroll.clientWidth;
  const viewportHeight = scoreScroll.clientHeight;
  for (const page of scorePages.children) {
    const image = page.firstElementChild;
    const ratio = Number(image.getAttribute('width')) / Number(image.getAttribute('height'));
    const width = Math.min(viewportWidth, viewportHeight * ratio) * zoom;
    page.style.width = `${width}px`;
    if (page === scorePages.firstElementChild) {
      const leadingSpace = Math.max(0, (viewportHeight - width / ratio) / 2);
      scorePages.style.setProperty('--score-leading-space', `${leadingSpace}px`);
    }
  }
  zoomOut.disabled = zoom <= minZoom;
  zoomIn.disabled = zoom >= maxZoom;
  zoomReset.textContent = `${Math.round(zoom * 100)}%`;
}

function zoomTo(next, point) {
  next = clamp(next, minZoom, maxZoom);
  if (next === zoom || !scorePages.firstElementChild) return;
  const viewport = scoreScroll.getBoundingClientRect();
  const center = point || { x: viewport.left + viewport.width / 2, y: viewport.top + viewport.height / 2 };
  const anchor = [...scorePages.children].find(page => page.getBoundingClientRect().bottom >= center.y) || scorePages.lastElementChild;
  const before = anchor.getBoundingClientRect();
  const relativeX = clamp((center.x - before.left) / before.width, 0, 1);
  const relativeY = clamp((center.y - before.top) / before.height, 0, 1);
  zoom = next;
  layoutScore();
  const after = anchor.getBoundingClientRect();
  scoreScroll.scrollLeft += after.left + after.width * relativeX - center.x;
  scoreScroll.scrollTop += after.top + after.height * relativeY - center.y;
}

function pinchPoint(touches) {
  const [first, second] = touches;
  return {
    x: (first.clientX + second.clientX) / 2,
    y: (first.clientY + second.clientY) / 2,
    distance: Math.hypot(first.clientX - second.clientX, first.clientY - second.clientY),
  };
}

new ResizeObserver(() => { if (viewer.open && viewer.dataset.mode === 'score') layoutScore(); }).observe(scoreScroll);
zoomOut.addEventListener('click', () => zoomTo(zoom / 1.25));
zoomReset.addEventListener('click', () => zoomTo(1));
zoomIn.addEventListener('click', () => zoomTo(zoom * 1.25));
scoreScroll.addEventListener('wheel', (event) => {
  if (!event.ctrlKey && !event.metaKey) return;
  event.preventDefault();
  const delta = event.deltaY * (event.deltaMode === 1 ? 16 : 1);
  zoomTo(zoom * Math.exp(-delta * .008), { x: event.clientX, y: event.clientY });
}, { passive: false });
scoreScroll.addEventListener('touchstart', (event) => {
  if (event.touches.length !== 2) return;
  const { distance } = pinchPoint(event.touches);
  pinch = distance > 0 ? { distance, zoom } : undefined;
}, { passive: true });
scoreScroll.addEventListener('touchmove', (event) => {
  if (!pinch || event.touches.length !== 2) return;
  if (event.cancelable) event.preventDefault();
  const point = pinchPoint(event.touches);
  zoomTo(pinch.zoom * point.distance / pinch.distance, point);
}, { passive: false });
scoreScroll.addEventListener('touchend', () => { pinch = undefined; });
scoreScroll.addEventListener('touchcancel', () => { pinch = undefined; });
viewer.addEventListener('keydown', (event) => {
  if (viewer.dataset.mode !== 'score' || event.ctrlKey || event.metaKey || event.altKey) return;
  if (event.key === '+' || event.key === '=') zoomTo(zoom * 1.25);
  else if (event.key === '-') zoomTo(zoom / 1.25);
  else if (event.key === '0') zoomTo(1);
  else return;
  event.preventDefault();
});
document.addEventListener('click', (event) => {
  const trigger = event.target.closest('.viewer-trigger');
  if (!trigger || viewer.open) return;
  const template = document.getElementById(trigger.dataset.image);
  const isAlbum = trigger.classList.contains('cover-trigger');
  const scrollArea = isAlbum ? albumScroll : scoreScroll;
  viewer.dataset.mode = isAlbum ? 'album' : 'score';
  albumScroll.hidden = !isAlbum;
  (isAlbum ? albumScroll : scorePages).replaceChildren(template.content.cloneNode(true));
  viewer.setAttribute('aria-label', trigger.getAttribute('aria-label'));
  openedBy = trigger;
  zoom = 1;
  viewer.showModal();
  if (!isAlbum) layoutScore();
  scrollArea.scrollTo(0, 0);
  scrollArea.focus({ preventScroll: true });
});
viewer.addEventListener('close', () => {
  scorePages.replaceChildren();
  albumScroll.replaceChildren();
  pinch = undefined;
  openedBy?.focus({ preventScroll: true });
});
albumScroll.addEventListener('click', (event) => {
  const trigger = event.target.closest('.album-video button');
  if (!trigger) return;
  const player = document.createElement('iframe');
  player.title = trigger.dataset.playerTitle;
  player.allow = 'autoplay; encrypted-media; picture-in-picture';
  player.referrerPolicy = 'strict-origin-when-cross-origin';
  player.allowFullscreen = true;
  player.src = `https://www.youtube-nocookie.com/embed/${encodeURIComponent(trigger.dataset.videoId)}?autoplay=1&playsinline=1`;
  trigger.replaceWith(player);
  player.focus({ preventScroll: true });
});
