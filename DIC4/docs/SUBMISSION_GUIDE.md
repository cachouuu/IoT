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

完整專案已整理成 repository 目錄。可先在自己的 GitHub 建立新 repository，再以 GitHub Desktop 或 Git 上傳該目錄內容。至少應看到：

- `README.md`
- `openspec/`
- `paper/`
- `mcp/`
- `evidence/`
- `docs/`
- `scripts/`
- `package.json` 與 `package-lock.json`

這份專案含原專題程式快照與內部實驗紀錄，適合先建立私人 repository，再依課程要求設定老師可讀取的方式。若選擇公開，先確認團隊對原始專題檔案的公開安排。

GitHub Desktop 的做法：將解壓後的 `traffic-assistant-dic4` 加入為 local repository，建立初始 commit，再 Publish repository。此文件沒有宣稱上述遠端操作已替你完成。

若 GitHub Desktop 提示這個目錄還不是 Git repository，先在同一個目錄初始化 repository，再建立初始 commit 與發布。

## 課程作業區

截圖的明確要求是 IEEE conference Overleaf draft，以及 GitHub 上的 OpenSpec；標題要求使用 MCP。建議附上：

1. 論文 PDF。
2. 實際可開啟的 Overleaf 連結。
3. 實際可開啟的 GitHub 連結。
4. 完整 DIC4 ZIP（若作業區接受附件）。

MCP 說明與執行證據已位於 `docs/MCP_WORKFLOW.md`、`evidence/current/mcp_run.json`。老師若指定的是另一個課堂 MCP server，可保留本成果，再補上指定整合；目前作業截圖沒有這項細節。

## 你需要知道的內容

- 論文是英文 IEEE 研討會草稿，已有摘要、背景、相關研究、方法、公式、架構圖、結果、限制與參考文獻。
- 18 組歷史合成案例總 QVS 改善 18.28%，但有 5 組退步。
- 6 組詳細案例與 18 組重疊，不可相加成 24 組。
- 本次做了數據重新計算、規格驗證與 MCP 示範；沒有重新跑板子或宣稱道路實測。
- 截止日為 **2026-11-28**，截圖未顯示具體時分。

