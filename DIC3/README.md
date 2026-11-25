# DIC3 交通配時助手作業包

先閱讀 **Traffic_Assistant_DIC3_Report.pdf**。A4 橫式總覽在 **Traffic_Assistant_DIC3_Overview.pdf**。本次是 DIC3 個人作業的提案／規格重整，不是重交期末全部成果，也未代為上傳 LMS。

## 作業五項對照
1. 安裝／SDD：OpenSpec 2.0.0；OPEN_SPEC_WORKFLOW.md、evidence/openspec_*.txt/json。
2. A–F、5 核心、3 取捨、10 細節：DIC3_Report.md、docs/Abstract.md、docs/Cores_Tradeoffs_Details.md。
3. design.md 轉規格：design.md、TRACEABILITY.md、openspec/。
4. Introduction：docs/Introduction.md。
5. Related Work：docs/Related_Work.md，含八欄文獻摘要及研究缺口。

## 重現規格驗證
Node.js 22.12.0 以上；在此目錄使用 `npm install` 安裝已釘選的 OpenSpec 2.0.0，再執行 `npm run spec:validate`。
本機工作區已安裝，可直接使用 `powershell -File scripts/openspec.ps1 validate --all --strict --no-interactive`。
查看後續工作：`npm run spec:status`。規格完成不代表 tasks 已實作。

## 文件與產品狀態
refactor-project-proposal 是本次完成的文件變更，驗證後封存；integrate-task-workflow 是待實作產品整合，任務保留未勾選。原設計／提案與實驗快照在 source/、evidence/，雜湊在 source_manifest.json。
本包不是完整韌體原始碼發行版；RTL 與完整工程仍在既有 TrafficAgent/project。未訓練新模型、未上板、未新增交通實驗，未更動原始專案檔案。

## 建議繳交
上傳本完整 ZIP，讓老師同時取得報告及 OpenSpec 原始規格；若 LMS 只接受 PDF，先上傳主報告，再依可接受附件補 ZIP。實際檔案類型限制以 LMS 為準；四頁作業說明未列附件副檔名限制。
