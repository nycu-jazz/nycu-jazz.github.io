/* 沒有 JavaScript 時，影片卡片會直接開啟來源。 */
(function () {
  "use strict";

  var isFile = location.protocol === "file:";

  // 1. 直接用檔案總管開啟（file://）時，資料夾連結不會自動找 index.html，這裡補上。
  if (isFile) {
    var links = document.querySelectorAll("a[href]");
    for (var i = 0; i < links.length; i++) {
      var raw = links[i].getAttribute("href");
      if (/^([a-z]+:|\/\/|#)/i.test(raw)) continue;
      var hashAt = raw.indexOf("#");
      var path = hashAt === -1 ? raw : raw.slice(0, hashAt);
      var hash = hashAt === -1 ? "" : raw.slice(hashAt);
      if (path === "" || path.charAt(path.length - 1) === "/") {
        links[i].setAttribute("href", path + "index.html" + hash);
      }
    }
  }

  // file:// 缺少嵌入播放器需要的網站來源，保留原連結。
  if (isFile) return;
  const cards = document.querySelectorAll(".video-card:is([data-yt], [data-fb])");
  if (!cards.length) return;

  const panel = document.createElement("section");
  panel.id = "video-player";
  panel.className = "video-panel";
  panel.setAttribute("aria-labelledby", "video-player-title");
  panel.inert = true;
  panel.innerHTML = `
    <div class="video-panel-content">
      <div class="video-panel-bar">
        <h2 id="video-player-title"></h2>
        <button class="video-panel-close" type="button">收起</button>
      </div>
      <div class="video-frame"></div>
      <div class="video-panel-bar">
        <a class="video-panel-original ext" target="_blank" rel="noopener">在新分頁開啟</a>
      </div>
    </div>`;

  const title = panel.querySelector("h2");
  const frame = panel.querySelector(".video-frame");
  const original = panel.querySelector(".video-panel-original");
  const close = panel.querySelector("button");
  let activeCard = null;

  function collapse() {
    const card = activeCard;
    card.setAttribute("aria-expanded", "false");
    card.removeAttribute("aria-controls");
    panel.classList.remove("is-expanded");
    panel.inert = true;
    frame.replaceChildren();
    activeCard = null;
    card.focus({ preventScroll: true });
    card.scrollIntoView({ block: "nearest" });
  }

  close.addEventListener("click", collapse);
  panel.addEventListener("keydown", function (event) {
    if (event.key === "Escape") collapse();
  });

  for (const card of cards) {
    card.setAttribute("aria-expanded", "false");
    card.addEventListener("click", function (event) {
      if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || event.button) return;
      event.preventDefault();
      if (activeCard === card) {
        collapse();
        return;
      }

      const group = card.closest(".videos");
      if (activeCard) {
        activeCard.setAttribute("aria-expanded", "false");
        activeCard.removeAttribute("aria-controls");
      }
      if (panel.previousElementSibling !== group) {
        panel.classList.remove("is-expanded");
        group.after(panel);
        // 先套用收合高度，讓移到其他場次的播放器也能展開。
        panel.getBoundingClientRect();
      }
      activeCard = card;
      card.setAttribute("aria-controls", panel.id);
      card.setAttribute("aria-expanded", "true");
      title.textContent = card.dataset.title;
      original.href = card.href;
      panel.inert = false;
      panel.classList.add("is-expanded");

      let url;
      if (card.dataset.yt) {
        url = new URL("https://www.youtube-nocookie.com/embed/" + encodeURIComponent(card.dataset.yt));
        url.searchParams.set("autoplay", "1");
        url.searchParams.set("rel", "0");
        if (card.dataset.list) url.searchParams.set("list", card.dataset.list);
      } else {
        url = new URL("https://www.facebook.com/plugins/video.php");
        url.searchParams.set("href", card.href);
        url.searchParams.set("autoplay", "true");
        url.searchParams.set("show_text", "false");
        url.searchParams.set("width", Math.round(frame.clientWidth).toString());
      }

      const player = document.createElement("iframe");
      player.src = url.href;
      player.title = title.textContent;
      player.allow = "autoplay; encrypted-media; picture-in-picture; fullscreen";
      player.referrerPolicy = "strict-origin-when-cross-origin";
      player.allowFullscreen = true;
      frame.replaceChildren(player);
      close.focus({ preventScroll: true });
      panel.scrollIntoView({ block: "start" });
    });
  }
})();
