# Design-to-spec traceability

需求均有 WHEN／THEN 驗收情境。Baseline 是從既有設計與來源整理的契約；Proposed 是後續整合目標，不代表本次已實作。

| 細節 | 核心／取捨 | Requirement ID | 規格位置 | 來源／驗收 |
|---|---|---|---|---|
| D01 範圍 | C4 | DOC-02 | proposal-documentation | 原設計 §1、§10；限制檢查 |
| D02 任務 | C1 | TASK-01/02 | task-intake | 設計 §1/§6；AT01/02 |
| D03 資料資格 | C1 | DATA-01 | data-qualification | 設計 §5；AT03 |
| D04 容量／衍生 | C1 | DATA-02/03 | data-qualification | 設計 §5；AT04 |
| D05 特徵 | C2 | CORE-01/DEC-01 | traffic-control-core/decision-evidence | firmware；AT05 |
| D06 有效域 | C3/T1 | CORE-02/DEC-01/02 | traffic-control-core/decision-evidence | model header/firmware；AT06 |
| D07 合法方案 | C3 | CORE-02/EXEC-01 | traffic-control-core/execution-verification | 設計 §2；AT07 |
| D08 相位 | C4/T2 | CORE-03 | traffic-control-core | 設計 §2；AT08 |
| D09 生效 | C4 | EXEC-02 | execution-verification | 設計 §6；AT09/10 |
| D10 績效 | C5/T3 | EVAL-01/02/03/REP-01/02 | paired-evaluation/task-reporting | 原始實驗；AT11/12 |

Baseline 檔案位於 openspec/specs/；Proposed 檔案位於 openspec/changes/integrate-task-workflow/specs/。完成的文件需求 DOC-01/02/03 在封存後合併至 openspec/specs/proposal-documentation/。

原本「核心已有」不代表通用整合已有。驗收情境是預期行為，本次未執行產品 AT01-AT12；實際執行的是文件完整性、數據重算、OpenSpec 結構驗證與 PDF 視覺檢查。
