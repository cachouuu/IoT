# 交通配時助手系統設計

日期：2026-11-13。本文件由 source/DESIGN_original.md 與原提案重整，維持既有模型、三方案、30 秒週期與 ARM／FPGA 架構。新增的是需求與驗收定義，沒有據此宣稱通用任務層已實作。

## Context and scope
單路口兩軸直行桌上原型；既有 CART 樹由配時評分規則產生的標籤訓練。四特徵為兩向估計佇列及各向過去完整 30 秒到車數。模型為 513 節點、深度 10、4,104 bytes。queue 0–120、arrivals_30 0–30；資料介面各向每秒 0/1。

## Request contract (proposed)
必填 task_id、dataset_id、dataset_sha256、mode（review/execute）、policy（fixed_balanced/tree_with_rules_fallback）、objective（queue_vehicle_seconds）、observation_count、manifest_path。原型的 execute 僅指實驗模式，不是道路部署。

## Decisions
維持三個 plan_id：0=12/12、1=16/8、2=8/16 秒 NS/EW 綠燈。各方向黃燈 2 秒、全紅 1 秒，30 秒完整週期。policy 0/2 與 plan_id 0/1/2 不混用。
ARM 只選合法方案，FPGA 掌管固定相位順序。新方案於完整週期邊界生效，不重啟當期倒數。韌體在模型域外走既有規則；底層模型函式的均衡防護不等於韌體實際域外政策。

## Data qualification (proposed integration)
合成逐秒資料與官方分鐘資料分開。確認來源、雜湊、單位、時間連續性、觀測窗、車道涵蓋、同路口兩軸配對與介面容量。缺分鐘不補零，單快照不重複成長序列，未知方向不人工配對。若另有逐秒重建，需獨立標示 derived 與重建假設；本次沒有此完成證據。

## State and exception contract
received -> qualified -> observing -> decided。
無效資料 -> rejected；review -> reported（零裝置寫入）；execute -> submitted -> applied / timeout / mismatch -> reported。
applied 必須有匹配的 active_plan、預期 cycle_count 及與提交紀錄的關聯；只有 ACK 仍是 submitted。實作時須使用現有可用命令識別或序列關聯，不虛構不存在的硬體暫存器。

## Metrics and evidence
僅在已宣告觀測窗內累加每筆到車及放行後的剩餘佇列。600 筆績效窗後可確認第 20 次生效，但不得增加到車、延長績效或清空佇列。報告排隊車秒、已放行平均等待、放行數、兩向期末佇列及回退次數。不同批次不混加或當獨立樣本推論。

## Risks and trade-offs
模型近似規則可能有誤差；週期更新可能錯過短突發；合計改善可能掩蓋方向差異。三個取捨及十個細節見 docs/Cores_Tradeoffs_Details.md。

## Implementation mapping
既有核心：project/embedded/model/traffic_model.c/.h、project/embedded/firmware/traffic_agent.c、main_arm.c、project/embedded/rtl/traffic_axi.v、project/rtl/traffic_fsm.v。
部分資料工具：project/embedded/data/taipei/；實驗證據：project/embedded/validation/。
待整合：task-intake、data-qualification、decision-evidence、execution-verification、task-reporting。實作路徑相對原 TrafficAgent 根目錄；本作業包只攜帶必要來源快照，並非完整韌體專案。

## Workflow and verification
本文件 -> OpenSpec proposal/specs/design/tasks -> 實作 -> acceptance verification -> archive。
本次文件變更已完成；產品整合任務仍未勾選。詳見 TRACEABILITY.md、OPEN_SPEC_WORKFLOW.md 與 openspec/changes/integrate-task-workflow/tasks.md。


## Goals / Non-Goals
Implement only the missing task/evidence layer; retain baseline contracts. Do not add new models or claim road efficacy.

## Migration Plan
Build request and qualification layers, integrate existing decisions, connect readback, then validate saved-input and failure scenarios.

## Open Questions
Verify available command correlation fields and device-health/readback timeout settings against the implementation before coding. Expose them as configuration and tests; do not invent new registers.
