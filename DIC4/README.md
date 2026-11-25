# DIC4 — Traffic Timing Assistant

IEEE conference draft using MCP and OpenSpec · 2026-11-25

本次 DIC4 成果整理於 `cachouuu/IoT` 的 `DIC4/` 資料夾。

**檔案入口：** [論文 PDF](paper/main.pdf) · [Overleaf 匯入 ZIP](Traffic_Assistant_DIC4_Overleaf.zip) · [OpenSpec 規格](openspec/) · [MCP 執行說明](docs/MCP_WORKFLOW.md)

## 這份作業包含什麼

這份 DIC4 沿用第 13 組「交通配時助手」，把 DIC3 提案整理為英文 IEEE 雙欄論文草稿。原專題團隊為吳祁叡、魏柏勝、陳仁凱；此個人作業草稿的作者欄已依本人提供的正式英文姓名設為 **Po Sheng Wei**。

| 作業項目 | 對應成果 |
|---|---|
| IEEE conference draft | `paper/main.tex`、`paper/references.bib`、兩張向量圖與編譯 PDF |
| GitHub 上的 OpenSpec（已發布） | `openspec/`、固定版次的 `package.json`／`package-lock.json` 與驗證程式 |
| Using MCP | 可執行的 `mcp/evidence_server.py`、`mcp/demo_client.py` 與真實呼叫紀錄 |
| 來源與實驗依據 | `evidence/archive/dic3/` 原檔、`evidence/current/` 本次查核輸出 |

**本機檔案完成與線上發布分開記錄。** Overleaf／GitHub 的實際狀態請看 `docs/PUBLICATION_STATUS.json`；沒有經過確認的網址不會填入，學習平台繳交也不會由產生 ZIP 自動視為完成。

## 論文重點

系統以 ARM 維護簡化 FIFO 佇列，根據四個整數特徵，透過既有決策樹與規則回退選擇 12/12、16/8 或 8/16 秒的 NS/EW 綠燈方案。FPGA 維持 30 秒完整週期，在週期邊界採用待生效方案，並提供 active plan／cycle 回讀。

論文保留 18 組保存案例的合計 QVS 改善 18.28%，也完整交代 5 組退步。6 組詳細案例是同 seed 子集，不是另外 6 組獨立測試。直接規則的保存結果略優於樹加回退，因此論文沒有把決策樹描述成已證明優於規則。

本次重新執行的是紀錄重算、規格驗證、MCP 工作流程與文件編譯。沒有重新訓練、重跑原始韌體、產生新車流或進行板測。歷史實板數字引用封存報告；當次 raw captures 不在這個 handoff 中。

## 快速使用

1. **先看論文 PDF。** 主要稿件位於 `paper/main.pdf`。
2. **Overleaf。** 將交付的 `Traffic_Assistant_DIC4_Overleaf.zip` 上傳為新專案，主檔選 `main.tex`，compiler 選 pdfLaTeX，按 Recompile。詳見 `docs/SUBMISSION_GUIDE.md`。
3. **GitHub。** 本次 DIC4 成果已上傳至既有公開 repository `cachouuu/IoT` 的 `DIC4/` 資料夾：[DIC4 作業資料夾](https://github.com/cachouuu/IoT/tree/main/DIC4)。繳交時可使用此連結。
4. **繳交。** 依課程作業區實際收件方式，提供論文 PDF、Overleaf 與 GitHub 連結，或完整作業 ZIP。截圖僅指定日期 2026-11-28，未顯示截止時分。

## 重跑已完成的檢查

### 1. 既有數據的獨立重算

```bash
python scripts/audit_evidence.py --source-root evidence/archive/dic3 --output-dir evidence/recheck
```

原始文件唯讀；使用新的輸出目錄即可保存本次交付的紀錄。這個命令重新查核數字與來源，不會重跑交通實驗。

### 2. OpenSpec 嚴格驗證

```bash
npm ci --ignore-scripts
python scripts/validate_openspec.py
```

使用固定版本 `@fission-ai/openspec@2.0.0`。三個 main specs 與兩個 active changes 的結構驗證通過，不代表所有軟體任務完成。原 `integrate-task-workflow` 保持未完成。

### 3. 真實 MCP 呼叫

```bash
python -m pip install -r mcp/requirements.txt
python mcp/demo_client.py
```

執行標準 stdio initialize、tools/list 及三個 tools/call，讀取固定的來源與查核結果，並重新保存實際回應。MCP 只支援文件來源追溯，不控制交通硬體，也不自動發布到外站。

### 4. 圖表與論文

```bash
python -m pip install -r scripts/requirements.txt
python scripts/make_figures.py
python scripts/build_paper.py
```

本機編譯需要已配置好的 TeX Live／MiKTeX，包含 pdfLaTeX、BibTeX；也可直接使用 Overleaf。官方 `IEEEtran.cls` 和 `IEEEtran.bst` 已隨稿附上。

## 閱讀路線

- `docs/SUBMISSION_GUIDE.md`：繁中上傳與繳交指引。
- `docs/CLAIM_TO_SOURCE.md`：每個主要論述的依據。
- `docs/EVIDENCE_AUDIT_NOTES.md`：數據、規則、窗外確認與缺失來源的完整查核。
- `docs/MCP_WORKFLOW.md`：MCP 的功能、實際結果與重跑方式。
- `docs/REFERENCE_VERIFICATION.md`：外部文獻的原始來源。
- `latest.md`：本次交付狀態與剩餘事項。

