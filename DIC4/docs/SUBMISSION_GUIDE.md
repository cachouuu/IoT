# DIC4 繳交指引

## 作者資訊

論文作者欄已依本人提供的正式英文姓名設為 **Po Sheng Wei**，對應 `IEEEauthorblockN{Po Sheng Wei}`。學校使用 National Chung Hsing University；沒有代填未知的系所、學號或電子郵件。原專題為第 13 組交通配時助手，原團隊成員保留於來源文件與 README。

作者姓名已確認。後續若修改稿件，重新編譯並下載最新 PDF 作為繳交版本；GitHub 中的 `paper/main.tex` 與 `paper/main.pdf` 也同步更新，讓兩邊稿件一致。

## Overleaf

1. 登入自己的 Overleaf。
2. 選擇建立專案／Upload Project，上傳 **Traffic_Assistant_DIC4_Overleaf.zip**。此 ZIP 的根目錄就是 `main.tex`，可直接匯入。
3. 主檔選 `main.tex`，compiler 使用 **pdfLaTeX**，重新編譯。
4. 檢查題目、作者、圖表與參考文獻，確定 PDF 正常。
5. 依老師要求取得可檢視的專案連結；只有網址不代表對方已有存取權限。

Overleaf ZIP 內含 `main.tex`、`references.bib`、`IEEEtran.cls`、`IEEEtran.bst` 與 `figures/`。完整專案的 `paper/` 是同一份來源。

## GitHub

GitHub 上傳已完成，位置為既有公開 repository `cachouuu/IoT` 的 `DIC4/` 資料夾。繳交 GitHub 連結時使用：[DIC4 作業資料夾](https://github.com/cachouuu/IoT/tree/main/DIC4)。

以下檔案路徑皆相對於 `DIC4/`：

- `README.md`
- `openspec/`
- `paper/`
- `mcp/`
- `evidence/`
- `docs/`
- `scripts/`
- `package.json` 與 `package-lock.json`

## 課程作業區

截圖的明確要求是 IEEE conference Overleaf draft，以及 GitHub 上的 OpenSpec；標題要求使用 MCP。建議附上：

1. 論文 PDF。
2. 實際可開啟的 Overleaf 連結。
3. GitHub 作業連結：[DIC4 作業資料夾](https://github.com/cachouuu/IoT/tree/main/DIC4)。
4. 完整 DIC4 ZIP（若作業區接受附件）。

MCP 說明與執行證據已位於 `docs/MCP_WORKFLOW.md`、`evidence/current/mcp_run.json`。老師若指定的是另一個課堂 MCP server，可保留本成果，再補上指定整合；目前作業截圖沒有這項細節。

## 你需要知道的內容

- 論文是英文 IEEE 研討會草稿，已有摘要、背景、相關研究、方法、公式、架構圖、結果、限制與參考文獻。
- 18 組歷史合成案例總 QVS 改善 18.28%，但有 5 組退步。
- 6 組詳細案例與 18 組重疊，不可相加成 24 組。
- 本次做了數據重新計算、規格驗證與 MCP 示範；沒有重新跑板子或宣稱道路實測。
- 截止日為 **2026-11-28**，截圖未顯示具體時分。

