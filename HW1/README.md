# IoT HW1 — Taiwan Weather App

臺灣天氣查詢作業。使用 **Python、中央氣象署（CWA）開放資料、SQLite、Streamlit**，查詢各縣市未來 36 小時的天氣、溫度與降雨機率。

依本次作業選擇臺灣天氣主題，使用 **Codex Agent** 協助實作，取代題目所列的 Antigravity。

- 作業網站：[Taiwan Weather App](https://cachouuu.github.io/IoT/HW1/)
- 個人首頁：[Sam Wei 的個人首頁](https://cachouuu.github.io/IoT/)
- 原始碼：[IoT / HW1](https://github.com/cachouuu/IoT/tree/main/HW1)

## 作業對應

| 項目 | 實作 |
| --- | --- |
| Python | `weather.py` 擷取、解析及儲存預報；`export_weather.py` 匯出公開快照 |
| CWA API | 使用 `F-C0032-001` 一般天氣預報，查詢臺灣 22 縣市 |
| SQLite | 將每次成功擷取的資料與時間存入本機 `data/weather.db` |
| Streamlit | `app.py` 提供本機查詢、更新與歷史紀錄介面 |
| 公開展示 | `docs/` 提供可直接開啟的 GitHub Pages 網站 |
| AI 協作 | Codex Agent 協助設計、程式實作與測試 |

## 兩種執行方式

**本機 Streamlit** 執行 Python、呼叫 CWA、使用 SQLite 儲存及讀取紀錄。**公開 GitHub Pages** 顯示 Python 事先匯出的 JSON 快照，支援瀏覽與篩選，但不是線上執行的 Streamlit 服務。GitHub Pages 僅提供靜態檔案，不能執行 Python。[GitHub Pages 說明](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages)

資料流程：

```text
CWA API → Python 解析與驗證 → SQLite
                            ├→ Streamlit 本機介面
                            └→ JSON 快照 → GitHub Pages
```

**預設使用合成示範資料，非真實或即時天氣。** 示範資料沿用 CWA 資料結構，不需金鑰即可操作介面與檢查資料流程。設定金鑰後，可手動取得 CWA 預報。

## 本機啟動

建議 Python 3.12。在 `IoT/HW1` 資料夾執行：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

Windows 啟用虛擬環境時使用 `.venv\Scripts\activate`。開啟終端機顯示的本機網址，預設即可使用示範模式。

真實天氣需要先到[氣象資料開放平台](https://opendata.cwa.gov.tw/)申請授權碼。可複製設定範本，在本機編輯檔案填入金鑰：

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

`.streamlit/secrets.toml` 已由 Git 忽略。也可使用環境變數 `CWA_API_KEY`；命令列匯出程式只讀取這個環境變數，不讀取 Streamlit 設定檔。

## 匯出公開網站資料

產生合成示範資料：

```bash
python export_weather.py --demo
```

如需真實預報，先在執行環境設定 `CWA_API_KEY`，再執行：

```bash
python export_weather.py
```

缺少金鑰或更新失敗時保留既有公開快照。成功資料先存入 SQLite，再完整替換 JSON；不會自動以示範資料代替失敗的 CWA 回應。

可指定其他位置：

```bash
python export_weather.py --demo --db data/weather.db --output docs/data/forecast.json
```

輸出檔案包含 `dataset`、`source`、`fetched_at`、`rows` 與 `history`。`source` 為 `cwa` 或 `demo`；預報列包含縣市、時段、天氣、天氣代碼、高低溫、降雨機率及舒適度。時間含臺灣時區 `+08:00`。

本機預覽公開網頁：

```bash
python -m http.server 8000 --directory docs
```

瀏覽 [http://localhost:8000](http://localhost:8000)。網頁上的重新載入只會取得目前已發布的快照，不會直接呼叫 CWA。

## GitHub Pages 發布與手動更新

1. 專案位於 `IoT` 儲存庫 `main` 分支的 `HW1/` 資料夾。
2. 在 **Settings → Pages → Build and deployment → Source** 選擇 **GitHub Actions**。
3. 若要取得真實預報，在 **Settings → Secrets and variables → Actions** 新增 repository secret，名稱為 `CWA_API_KEY`，值填入自己的 CWA 授權碼。示範模式不需設定。
4. 在 **Actions → Deploy IoT coursework** 選擇 **Run workflow**。部署完成後檢查網站的資料來源與擷取時間。

更新 `DIC1/`、`HW1/` 或 `.github/workflows/deploy.yml` 後推送到 `main`，會部署既有快照與網站檔案，不會呼叫 CWA。

手動 **Run workflow** 時，只有已設定 `CWA_API_KEY` 才會執行 Python 抓取預報、提交變更的 `HW1/docs/data/forecast.json`，並一起部署 DIC1 首頁與 HW1 網站。沒有金鑰時，直接發布既有快照並保留來源標示。API 抓取失敗時保留已發布的版本。

工作流程只使用 GitHub 官方 actions。`contents: write` 用於提交快照；`pages: write` 與 `id-token: write` 用於部署。只上傳 DIC1 網頁資產與 `HW1/docs/`，不發布 API 金鑰、SQLite 檔案或 Streamlit 設定。[官方部署工作流程說明](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)

**歷史紀錄範圍：** 本機 SQLite 保留各來源最近 100 次儲存的紀錄。GitHub Actions 每次使用新的執行環境，SQLite 不會跨次保存，也不會提交；因此公開快照的 `history` 只反映該次匯出環境的資料，不代表完整的雲端歷史資料庫。

## 測試

```bash
python -m unittest discover -s tests -v
```

測試使用合成資料與模擬 API 回應，檢查解析、儲存、公開快照格式，以及失敗時保留舊資料和避免洩漏金鑰。**目前尚未使用有效金鑰完成真實 CWA API 端到端驗證。**

## 資料與參考

- [CWA API 使用說明](https://opendata.cwa.gov.tw/devManual/insrtuction)
- 資料集：`F-C0032-001`，一般天氣預報，各縣市未來 36 小時。
- API 端點：`https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001`（需要授權碼）。
- [GitHub Pages 自訂工作流程](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)
