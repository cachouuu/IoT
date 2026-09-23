# IoT — Sam Wei

本學期 IoT 課程作業，統一收錄在此儲存庫。

| 作業 | 原始碼 | 公開網站 |
| --- | --- | --- |
| DIC1：Personal Page | [DIC1](DIC1/) | [個人首頁](https://cachouuu.github.io/IoT/) |
| HW1：Taiwan Weather App | [HW1](HW1/) | [台灣天氣](https://cachouuu.github.io/IoT/HW1/) |

DIC1 是網站首頁，可從導覽列或作業入口進入 HW1，再返回首頁。

## 專案結構

```text
DIC1/          個人頁：HTML、CSS、JavaScript、圖片
HW1/           天氣 App：Python、CWA、SQLite、Streamlit
  docs/        天氣公開展示頁與 JSON 快照
  tests/       資料處理與匯出測試
.github/       共用 GitHub Pages 部署流程
```

HW1 目前使用合成示範資料，22 縣市各 3 個時段，非即時天氣預報。本機 Streamlit 與設定方式見 [HW1 說明](HW1/README.md)。

## 執行 HW1

```bash
cd HW1
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

## 測試與發布

```bash
cd HW1
python -m unittest discover -s tests -v
```

GitHub **Settings → Pages → Source** 設為 **GitHub Actions**。推送 `DIC1/`、`HW1/` 或部署流程的變更到 `main` 時，先執行測試，再將 DIC1 發布到網站根目錄、`HW1/docs/` 發布到 `/HW1/`。兩份作業的程式仍分別存放於原始碼資料夾中。

若之後需要 CWA 真實預報，在此 `IoT` 儲存庫設定 `CWA_API_KEY` secret，再手動執行 **Deploy IoT coursework**。沒有金鑰時維持已標示的示範資料，不會自動定時更新。真實 API 尚未完成端到端驗證。

使用 Codex Agent 協助實作、設計與測試。
