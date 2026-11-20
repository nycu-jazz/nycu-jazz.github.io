# NYCU Jazz

陽明交大「爵士和聲、即興與合奏」歷屆期末 combo 成果演出的整理站。
**修課學生自行整理，不是學校、跨域學程或授課教師的官方網站。**

純靜態網站：repo 根目錄就是 GitHub Pages 要發布的內容，線上不需要任何建置步驟。

## 網址

| 路徑 | 內容 |
| --- | --- |
| `/` | 首頁：本學期、最近一場、歷屆列表、關於本站 |
| `/115a/`、`/114a/`、`/113b/` … `/108b/` | 各學期頁（A = 第 1 學期，B = 第 2 學期） |
| `/404.html` | 找不到頁面 |

## 檔案

```
data/site.json     全站內容（唯一需要手動編輯的資料檔）
build.py           產生器，只用 Python 3 標準函式庫
assets/site.css    樣式（顏色、字體變數在最上面的 :root）
assets/site.js     file:// 預覽的連結修正、YouTube 點擊後才載入
index.html、<學期>/index.html、404.html、sitemap.xml   由 build.py 產生，請勿手改
```

## 更新內容

1. 編輯 `data/site.json`。
2. 執行 `python3 build.py`。
3. 直接用瀏覽器開 `index.html` 檢查（或 `python3 -m http.server` 後開 <http://localhost:8000/>）。
4. 把資料檔和產生的 HTML 一起 commit。

### 新增一個學期

在 `semesters` 陣列**最前面**加一筆（陣列由新到舊排列），並視情況更新 `site.current`（首頁「本學期」）與 `site.latest_show`（首頁「最近一場」，必須是有 `show` 與 YouTube 影片的學期）。

```json
{
  "code": "115B",
  "crs_no": "課號",
  "credits": 3,
  "status": "scheduled",
  "syllabus_final": { "date": "2027-06-15", "week": 16, "text": "課綱該週的原文" },
  "show": null,
  "summary": "列表上的一句話摘要。",
  "notes": ["查證說明，一點一句。"],
  "videos": [],
  "sources": []
}
```

- `status`：`scheduled`（本學期，只有課綱排程）、`performed`（演出日期有公告或官方影片佐證）、`syllabus`（過去學期，只有課綱日期）。
- 演出確認後把 `status` 改成 `performed` 並填 `show`：
  `{ "date": "2026-12-22", "time": "19:00–20:30", "venue": "地點", "date_basis": "依據", "time_basis": "依據", "venue_basis": "依據" }`。
  查不到的 `time`、`venue` 填 `null`，頁面會顯示「未查證」。
- `videos`：YouTube 填 `{ "type": "youtube", "id": "影片 ID", "title", "kind", "publisher" }`（可加 `"list"`）；Facebook 填 `{ "type": "facebook", "url", "title", "kind", "publisher" }`。
- `program`（選填）：`{ "pieces": ["曲名"], "basis": "曲目依據" }`。
- 課綱連結由 `code` 與 `crs_no` 自動組出，星期由日期自動算出，不用手填。

### 查證原則

- 「課綱所列日期」和「實際演出日期」分開記；沒有公告、官方影片說明或影片畫面佐證，就不標 `performed`。
- 查不到就寫未查證，不推測。
- 只連到第一手公開資料（課綱、學程公告、學程官方 YouTube／Facebook）。不轉載演出者姓名，也不放授課教師個人網站的圖像、標誌或聯絡方式。
- 重新查證後更新 `site.checked`（頁尾的查閱日期）。

## 發布到 GitHub Pages

1. 在 GitHub 建立名為 `nycu-jazz.github.io` 的 repo（使用者或組織名稱須為 `nycu-jazz`），把這個資料夾推上 `main`。
2. Settings → Pages → Source 選 **Deploy from a branch**，分支 `main`、資料夾 `/ (root)`。
3. 之後每次 push 到 `main` 就會更新。

如果改用其他網域或專案頁（`https://帳號.github.io/repo/`），請改 `data/site.json` 的 `site.url` 後重新執行 `build.py`。頁面之間都用相對路徑，放在子路徑也能運作；只有 `404.html` 使用根目錄絕對路徑，放在子路徑時需把 `build.py` 裡 `build_404()` 的 `root="/"` 與連結改成該子路徑。

## 設計說明

深色舞台、極細的大字、黃銅色重點與襯線斜體英文小標，視覺方向參考林明學老師個人網站的公開設計；沒有使用該站的圖像、標誌或文字，也不代表老師認可本站。字體 Raleway、Noticia Text、Noto Sans TC 由 Google Fonts 載入，載入失敗時退回系統字體。
