# OpenSpec 安裝、規格驅動開發與驗證紀錄

## 本次完成範圍

DIC3 要求的是提案與設計規格重整。本次已完成 A–F、五個核心、三個取捨、十個細節、Introduction、Related Work、設計轉換、PDF 與規格驗證；沒有執行新的訓練、韌體實作或實板交通實驗。

## 安裝與初始化

日期：2026-11-13。實際安裝的 CLI 為 `@fission-ai/openspec@2.0.0`，Node.js v24.22.1。安裝退出碼為 0，實際輸出在 `evidence/openspec_install.txt`；版本讀取在 `evidence/openspec_version.txt`。本機將工具裝在工作區 `tmp/dic3-openspec`，規格則位於本作業目錄。

規格驅動開發先把系統「應有行為」寫成可追溯的 requirements 和 scenarios，再記錄設計取捨與實作任務。`proposal.md` 說明為什麼改，`specs/` 定義必須成立的行為，`design.md` 說明如何做，`tasks.md` 列出可驗證的工作；實作與檢查完成後才 archive，將 delta 合併到主規格。

已執行的命令序列（`openspec` 代表已安裝的 CLI）：

```text
openspec --version
openspec init --tools none --no-animation
openspec new change refactor-project-proposal
openspec new change integrate-task-workflow
# 編寫並檢閱 proposal / design / specs / tasks
openspec validate --all --strict --no-interactive --json
openspec status --change integrate-task-workflow --json
openspec instructions apply --change integrate-task-workflow --json
# 文件與 PDF 檢查完成後，僅封存文件變更
openspec archive refactor-project-proposal --yes
# 補寫封存時自動建立之主規格 Purpose，再執行嚴格檢查
openspec validate --all --strict --no-interactive --json
```

初始化使用 `--tools none`，不依賴特定編輯器或 AI 助手；所有實際規格和變更檔均可直接閱讀。此命令序列展示真實安裝與完整文件變更流程，不把未執行的產品實作當成完成。

## 設計如何轉換

| 原設計主題 | OpenSpec 位置 | 狀態 |
|---|---|---|
| 四特徵、三方案、規則回退與相位時序 | specs/traffic-control-core | 既有核心的行為契約 |
| 配對輸入、600 筆觀測、退步與零分母 | specs/paired-evaluation | 既有評估的行為契約 |
| 本次作業文件與證據 | specs/proposal-documentation | 文件變更驗證完成後合併 |
| 任務入口、資料資格、決策證據、生效確認、報告 | changes/integrate-task-workflow/specs | 後續產品整合，尚未實作 |

`TRACEABILITY.md` 串接 D01–D10、核心、取捨、需求 ID 與 AT01–AT12。原設計保存在 `source/DESIGN_original.md`，沒有覆寫既有工程。

## 驗證結果及正確解讀

封存前嚴格檢查：4 / 4 通過，0 項失敗、0 個 issues。完整機器可讀輸出是 `evidence/openspec_validate_before_archive.json`。封存輸出和封存後再次驗證分別保存在 `evidence/openspec_archive.txt` 與 `evidence/openspec_validate_after_archive.json`。

封存第一次建立主規格時，CLI 自動留下 Purpose 佔位文字；嚴格檢查因此回報 1 個 warning。已依提示補寫真正用途，重新檢查後 4 / 4 通過、0 issues。原始中間結果保留為 `evidence/openspec_validate_archive_initial.json`，不是隱藏失敗或略過驗證。

`status` 顯示四份 artifacts 完整，是規格文件完整，不是產品完成。`instructions apply` 的真實輸出顯示產品整合任務 total = 12、complete = 0、remaining = 12。檔案為 `evidence/openspec_product_status.json`、`evidence/openspec_product_apply.json`。主報告中的 AT01–AT12 是後續驗收情境，本次均 NOT_RUN。

資料核算腳本 `scripts/audit_evidence.py` 只重算保存的結果。`evidence/data_audit.json` 確認兩批合計、改善／退步筆數，以及七個快照的 SHA-256；它不是新增實驗。PDF 全頁檢閱紀錄在 `evidence/pdf_qa.json`。

## 在其他電腦重現

安裝 Node.js 22.12.0 以上，在本目錄執行：

```text
npm install
npm run spec:validate
npm run spec:list
npm run spec:status
npx openspec instructions apply --change integrate-task-workflow --json
python scripts/audit_evidence.py
```

`package.json` 已釘選 CLI 2.0.0。封存後的文件變更在 `openspec/changes/archive/`；後續產品變更保留 active。若繼續開發，需執行對應驗收、保留證據，再逐項勾選 tasks；不能只憑格式驗證通過而宣稱板端功能已驗收。
