# NYCU Jazz

陽明交大《爵士和聲、即興與合奏》的演出紀錄。網站由修課學生開發與維護，首頁有本學期場次，歷屆頁面收錄曲目、演出者和公開錄影。

[首頁](https://nycu-jazz.github.io/)・[歷屆演出](https://nycu-jazz.github.io/#archive)・[115A 演出頁](https://nycu-jazz.github.io/115a/)

網站以繁體中文呈現，曲名與演出者姓名沿用原文。需要其他語言時，可使用瀏覽器的翻譯功能。

## 維護網站

使用 Python 3.9 以上，建置只用標準函式庫。修改 [`data/site.json`](data/site.json) 後，在 repo 根目錄產生頁面並啟動本機預覽。

```sh
python3 build.py
python3 -m http.server 8000
```

開啟[本機預覽](http://localhost:8000/)。[`build.py`](build.py) 會產生首頁、各學期頁、404 和 sitemap。調整介面時可編輯 [`assets/site.css`](assets/site.css) 和 [`assets/site.js`](assets/site.js)。

### 新增或更新一場演出

在 `semesters` 裡填寫學期代碼 `code`、課號 `crs_no`、學分 `credits`、狀態 `status`、演出資訊 `show`、錄影 `videos` 和來源 `sources`。新學期放在陣列最前面，並更新 `site.current`。若要讓 `#latest` 指向新的場次，也更新 `site.latest_show`。

| 欄位 | 填寫方式 |
| --- | --- |
| `status` | `scheduled` 是即將演出，`performed` 是有場次資訊的過去演出，`syllabus` 是僅有課綱或錄影等資料的歷屆學期。 |
| `show` | 有日期時填 `date`（`YYYY-MM-DD`）。可加 `time`（`HH:MM–HH:MM`、台灣時間）、`venue`、`admission` 和供地圖搜尋的 `map_query`。缺少場次日期時可填 `null`。 |
| `program.pieces` | 可直接填曲名，也可用物件填 `title`、該曲的 `performers`、影片連結 `url` 和時間戳 `cue`。`performers` 的每筆可填姓名，或用 `{"name": "姓名", "instrument": "口風琴"}` 標註該曲使用的樂器。有確定曲序時，在 `program` 設定 `ordered: true`。 |
| `credits_by_role` | 整場名單以角色分組，例如 `{"鋼琴": ["姓名"], "鼓": ["姓名"]}`。只有人名時可用「演出者」作為欄名。 |
| `videos` | YouTube 用 `type: "youtube"` 和 `id`，Facebook 用 `type: "facebook"` 和 `url`。每支影片填 `title`，可另外指定 `thumbnail`。 |
| `sources` | 來源以 `label`、`url`、`publisher` 記錄。曲目表的來源可填在 `program.source`。 |

115A 的 `program.details` 指向 [`data/115a-program.json`](data/115a-program.json)，保存作曲家、中文引文、原始出處與曲譜頁面尺寸；曲譜 WebP 放在 `assets/sheets/115a/`。封面、錄音連結與演出名單仍從 `data/site.json` 讀取。

## 發布

更新內容後，將資料、資源及重新產生的頁面一起提交並推送到 `main`。GitHub Pages 會從根目錄自動發布，不需另外觸發建置。
