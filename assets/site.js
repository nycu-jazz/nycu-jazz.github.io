/* NYCU Jazz — 兩個小加強，沒有 JS 時頁面仍可完整使用。 */
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

  // 2. YouTube 影片：先顯示縮圖，按下後才在原位載入播放器。
  //    file:// 之下 YouTube 嵌入會被拒絕，所以保留原本的外部連結。
  if (!isFile) {
    document.addEventListener("click", function (event) {
      var frame = event.target.closest ? event.target.closest("a[data-yt]") : null;
      if (!frame || event.metaKey || event.ctrlKey || event.shiftKey || event.button) return;
      event.preventDefault();

      var src = "https://www.youtube-nocookie.com/embed/" + encodeURIComponent(frame.getAttribute("data-yt")) + "?autoplay=1&rel=0";
      var list = frame.getAttribute("data-list");
      if (list) src += "&list=" + encodeURIComponent(list);

      var holder = document.createElement("div");
      holder.className = "video-frame";
      var player = document.createElement("iframe");
      player.src = src;
      player.title = frame.getAttribute("data-title") || "YouTube 影片";
      player.allow = "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share";
      player.referrerPolicy = "strict-origin-when-cross-origin";
      player.allowFullscreen = true;
      holder.appendChild(player);
      frame.parentNode.replaceChild(holder, frame);
      player.focus();
    });
  }
})();
