# NYCU Jazz

陽明交大「爵士和聲、即興與合奏」歷屆期末 combo 成果演出的整理站。

純靜態網站：repo 根目錄就是 GitHub Pages 要發布的內容，線上不需要任何建置步驟。

## 網址

| 路徑 | 內容 |
| --- | --- |
| `/` | 首頁：本學期、歷屆演出（含錄影） |
| `/115a/`、`/114a/`、`/113b/` … `/108b/` | 各學期頁（A = 第 1 學期，B = 第 2 學期） |
| `/en/`、`/en/115a/` 等 | 英文首頁與各期演出，頁首可切換語言 |
| `/404.html`、`/en/404.html` | 找不到頁面 |

## 檔案

```
data/site.json     全站內容（唯一需要手動編輯的資料檔）
build.py           產生器，只用 Python 3 標準函式庫
assets/site.css    樣式（顏色、字體變數在最上面的 :root）
assets/site.js     file:// 預覽的連結修正、按需展開內嵌播放器
index.html、<學期>/index.html、en/、404.html、sitemap.xml   由 build.py 產生，請勿手改
```

## 更新內容

1. 編輯 `data/site.json`。
2. 執行 `python3 build.py`。
3. 直接用瀏覽器開 `index.html` 檢查（或 `python3 -m http.server` 後開 <http://localhost:8000/>）。
4. 把資料檔和產生的 HTML 一起 commit。

### 新增一個學期

在 `semesters` 陣列**最前面**加一筆（陣列由新到舊排列），並視情況更新 `site.current`（首頁「本學期」）與 `site.latest_show`（`#latest` 錨點對應的學期）。

```json
{
  "code": "115B",
  "crs_no": "課號",
  "credits": 3,
  "status": "scheduled",
  "show": null,
  "videos": [],
  "sources": []
}
```

- `status`：`scheduled`（本學期，尚未演出）、`performed`（過去場次）、`syllabus`（過去學期，無場次資料）。
- `show` 包含 `date`、`time`、`venue`，可加 `admission`。時間與場地可以留空。
- `videos`：YouTube 填 `{ "type": "youtube", "id": "影片 ID", "title", "kind", "publisher" }`（可加 `"list"`）；Facebook 填 `{ "type": "facebook", "url", "title", "kind", "publisher" }`。
- `program`（選填）：`{ "pieces": ["曲名"] }`。有來源支持曲序時加入 `"ordered": true`，曲目會顯示序號。
- 單曲可填 `{ "title": "曲名", "cue": "4:20", "url": "公開影片連結" }`，時間戳和連結都可省略。有公開字幕或說明時，可加單曲的 `"performers": ["姓名"]`。曲目可附 `"source": { "label": "連結文字", "url": "原始來源網址" }`。
- 可在學期層級填 `"credits_by_role": { "鋼琴": ["姓名"], "鼓": ["姓名"] }`，在曲目下方顯示整場名單。來源只列姓名時，可用「演出者」作為欄名。
- 本學期沒有公開曲目表時，可將 `pieces` 留空。
- 英文版由同一筆資料產生。場地、入場方式、影片或曲名、來源標題與發布者可分別填 `venue_en`、`admission_en`、`title_en`、`label_en` 與 `publisher_en`。演出者姓名共用原文。
- 課綱連結由 `code` 與 `crs_no` 自動組出，星期由日期自動算出，不用手填。

## 發布到 GitHub Pages

1. 在 GitHub 建立名為 `nycu-jazz.github.io` 的 repo（使用者或組織名稱須為 `nycu-jazz`），把這個資料夾推上 `main`。
2. Settings → Pages → Source 選 **Deploy from a branch**，分支 `main`、資料夾 `/ (root)`。
3. 之後每次 push 到 `main` 就會更新。

如果改用其他網域或專案頁（`https://帳號.github.io/repo/`），請改 `data/site.json` 的 `site.url` 後重新執行 `build.py`。頁面之間都用相對路徑，放在子路徑也能運作；只有 `404.html` 使用根目錄絕對路徑，放在子路徑時需把 `build.py` 裡 `build_404()` 的 `root="/"` 和共用版型所用的根目錄連結改成該子路徑。
