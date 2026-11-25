# 交通配時助手提案與規格重整

DIC3 Project Proposal Refactor using OpenSpec

物聯網數據分析與應用 AIOT　｜　個人作業　｜　2026 年 11 月 13 日

專題來源：第 13 組交通配時助手。原提案團隊：吳祁叡、魏柏勝、陳仁凱。

本作業將既有交通配時助手提案轉為可追溯、可驗收的規格。系統以單路口兩軸直行為範圍，由 ARM 上的小型決策樹選擇三種配時，FPGA 執行相位與倒數，再以回讀資料確認方案生效。重整重點是連結資料來源、決策依據、實際執行與同條件比較。

## 作業要求對照

| 作業要求 | 本次成果 | 對應檔案 |
|---|---|---|
| 1 安裝 OpenSpec 並了解 SDD | OpenSpec 2.0.0、初始化、規格驗證與文件變更封存 | OPEN_SPEC_WORKFLOW.md、evidence/ |
| 2 A–F 與 5／3／10 | 六段摘要、五個核心、三個取捨、十個設計細節 | 本報告第 2、6、7 部分 |
| 3 design.md 轉工作流程 | 設計文件、需求、WHEN／THEN 情境、實作任務與追溯表 | design.md、openspec/、TRACEABILITY.md |
| 4 Introduction refactor | 問題、證據、限制、研究問題與預期貢獻 | docs/Introduction.md |
| 5 Related Work refactor | 三個 AI 研究與三個交通來源、八欄摘要表及研究缺口 | docs/Related_Work.md |

## 成果與研究狀態

本次已完成的是提案與規格重整。決策樹與板端控制沿用既有原型；統一任務入口、跨來源資料資格檢查與通用報告仍為後續整合項目。OpenSpec 結構驗證通過只代表文件結構符合要求，不代表控制系統已通過全部功能驗收。

本報告以 2026-11-03 提案、目前 DESIGN.md、模型標頭與既有實驗紀錄為依據。既有數字分批呈現；本次沒有新訓練、交通實驗或實板測試。課堂 DietSense 內容作為寫作範例，本作業內容對應交通配時助手。

<!-- page -->
# 2 A–F 六段式摘要

## A Attention Getter　需求與重要性

路口各方向共享有限綠燈時間，需求不均或方向轉換時，固定配時可能造成不必要的排隊。香港政府 2025 年公布的自適應號誌試點提供了依人車需求調整配時的實務動機；Wu 等人的城市尺度研究也提醒我們，效益必須放在交通條件與評估假設下解讀。[D1][D2] 本專題關注如何以可負擔的開發板，展示「從車流資料到實際配時」的完整過程。

## B But　核心挑戰

第一，資料可取得不等於可用於控制；單分鐘流量、缺值與沒有證據的兩軸配對不能直接當作連續路口輸入。第二，模型推薦不代表硬體已執行，必須核對實際方案與週期。第三，平均排隊下降可能掩蓋某些情境或方向變差；因此需要固定配時基準、反例與清楚的評估邊界。

## C Cure　提出的解法

本專題提出「交通配時助手」，以結構化任務指定資料與模式，檢查資料資格，再由小型決策樹從均衡、南北優先、東西優先三種方案中選擇。系統保留規則回退、決策依據與執行回讀，將需求分析、方案選擇及執行確認串成受限的領域決策流程。

## D Development　方法

ARM 維護兩軸 FIFO 估計佇列與過去完整 30 秒到車數，形成四個整數特徵。513 節點、深度 10、儲存量 4,104 bytes 的既有決策樹學習配時評分規則提供的參考答案。有效域外使用韌體既有規則回退；FPGA 維持 30 秒週期與固定相位順序，只在完整週期邊界採用新方案。統一報告將連結資料批次、特徵、決策來源、提交及生效證據。

## E Experiments　評估

在相同保存輸入、初始條件、600 秒觀測窗及服務假設下，比較固定均衡配時與決策樹加規則回退。主要指標為排隊車秒，並列已放行平均等待、放行數、期末兩軸佇列與回退次數。既有 18 組主機配對合計車秒降低 18.28%，但 5 組變差；另一批 6 組與單一實板配對另列，不合併推論。[P3][P4]

## F Findings　預期產出

預期交付可重現的交通配時展示、需求與驗收規格、比較結果及可追溯的決策／執行報告。貢獻在於讓「用了什麼資料、為何選擇、是否生效、是否改善」各有證據。現有交通指標來自合成輸入與簡化 FIFO 模型；實際道路效益、行人控制、多路口協調及道路安全認證不在本專題已證實的成果內。

<!-- page -->
# 3 精簡摘要與 IEEE 風格摘要

## 中文精簡摘要

固定號誌配時未必能適應不同方向與時段的車流需求，而模型推薦也不代表硬體已確實執行。本專題提出交通配時助手，以單路口兩軸直行為範圍，結合資料資格檢查、小型決策樹與 ARM／FPGA 分層控制。ARM 根據估計佇列及過去三十秒到車數，在均衡、南北優先與東西優先三種方案中選擇；超出模型有效域時採規則回退。FPGA 維持固定相位順序，於完整週期邊界採用方案，並提供生效回讀。評估以相同輸入比較固定配時與模型政策，觀察排隊車秒、等待、剩餘車輛及方向差異，同時保留退步案例。預期成果是能追溯資料、選擇依據與執行結果的課程原型，並以 OpenSpec 管理需求、情境與任務。既有結果僅支持合成情境與板端執行可行性，不推論實際道路效益。

## English Title

Traffic Timing Assistant: An Evidence-Traceable Decision-Tree Framework with ARM–FPGA Execution Feedback

## Abstract

Fixed signal plans may allocate green time poorly when directional demand changes. A traffic-control prototype must also distinguish a recommended plan from a plan that has actually taken effect. This project proposes a traffic timing assistant for a single intersection with two through-traffic axes. The framework combines data qualification, a compact decision-tree policy, and layered ARM–FPGA execution. The ARM processor maintains estimated FIFO queues and arrival counts from the preceding 30 seconds. A pre-existing integer decision tree selects one of three predefined timing plans, while the firmware uses reference-rule fallback for inputs outside the supported domain. The FPGA preserves a fixed phase order and adopts pending plans only at complete cycle boundaries. A planned task layer links data provenance, observed features, decision sources, submitted commands, and execution readback in a unified report. Evaluation compares the fixed balanced plan with the tree-plus-fallback policy under identical saved inputs, initial conditions, service assumptions, and observation windows. Queue vehicle-seconds are the primary metric, supplemented by completed-vehicle waiting time, throughput, residual queues, and fallback counts. Existing synthetic experiments show both improvements and regressions, motivating scenario-level reporting rather than a universal performance claim. OpenSpec specifications translate the design into explicit requirements, acceptance scenarios, and implementation tasks. The expected contribution is a reproducible educational system that connects traffic analysis to bounded decisions and verifiable execution feedback. The current evidence supports simplified-model evaluation and prototype execution; real-road effectiveness remains unverified.

Index Terms—Traffic signal control, decision trees, embedded systems, FPGA, execution feedback, spec-driven development.

<!-- page -->
# 4 Introduction 重整

## 4.1 問題背景與應用價值

交通號誌在互斥方向之間分配通行時間。當方向需求及時段改變時，固定配時可能與目前需求不一致，使某一方向持續累積排隊。香港政府報告描述了依人車流量調整綠燈的試點；Wu 等人的研究則以城市資料與模擬評估自適應號誌的潛在影響。[D1][D2] 這些來源支持需求導向配時具有研究與工程價值，但其方法、場域與成果不能直接移作本原型的效果。

## 4.2 使用者需求與問題界定

本系統的主要使用者是課堂展示者及原型開發者。使用者選擇資料批次與展示模式後，需要知道資料是否足夠、系統採用哪個方案、選擇依據為何，以及硬體是否確實採用。單獨顯示車流圖表、模型 plan ID 或 LED 變化，都無法完整回答這些問題；資料、決策、執行與效益須分別留存證據。

## 4.3 既有方法與實作限制

小型決策樹能以條件判斷表達政策，但可讀性不等於正確性，更不等於已完成形式驗證。[A1] 多路口協作 LLM 與事件導向分層控制展現更廣泛的決策能力，但也需要不同的模型、資訊與評估環境。[A2][A3] 本專題的輸入是四個整數、動作僅有三種，因此以既有決策樹與有限權限的硬體介面達成課程展示目標。

## 4.4 研究問題

RQ1：在相同車流及服務條件下，模型加回退政策在哪些情境降低排隊車秒，又在哪些情境變差？

RQ2：能否以實際特徵、模型或回退來源及明確的資料限制，產生不超出證據的選擇說明？

RQ3：能否區分待提交、已提交、已生效與逾期／不一致，並以回讀證據核對方案採用？

## 4.5 方法與預期貢獻

我們採 ARM 分析與 FPGA 相位執行的分工，保留三個合法方案、完整週期邊界更新及固定配時基準。新整合層將負責結構化需求、資料資格檢查及統一報告。預期貢獻包括可追溯的任務流程、對應實作的需求與驗收情境，以及同時呈現改善與退步案例的評估方式。此貢獻定位於系統整合與可驗證展示，尚不宣稱新的交通控制理論。

## 4.6 範圍

本案限單路口兩軸直行、三種候選配時與既有開發板。估計佇列來自簡化 FIFO，黃燈及全紅秒數是桌上展示設定；道路設計仍須另考量幾何、速率、清道與行人需求。[D3] 本次不新增 LLM、多模型競賽、再訓練或交通模擬平台。

<!-- page -->
# 5 Related Work 重整

## 5.1 可解釋政策與小模型部署

VIPER 透過參考神經政策及其 Q 函數抽取決策樹，並在特定控制任務驗證政策性質。[A1] 它提供「將政策表示為可檢查的樹」的研究背景。本專題則使用配時評分規則產生訓練標籤，沒有重現 VIPER、強化學習或形式驗證。兩者的連結是政策表示方式，不能因同樣使用樹就沿用其正確性保證。

## 5.2 協作與分層交通決策

CoLLMLight 以時空圖描述鄰接路口，結合協作推理與模擬回饋微調，在 CityFlow 中評估多路口控制。[A2] 它處理的是路網協調，本專題僅含單路口，因此將它用於說明擴充方向與範圍差異。

Virtual Traffic Police 採上層 LLM 調整下層控制器參數，並加入交通知識檢索及 verifier，在 SUMO 事件情境中評估。[A3] 本專題借鏡決策與執行分工的思路，讓 ARM 選擇預先定義的方案、FPGA 管理相位；這是本專題的工程取捨，並非該論文已替本平台驗證的結果。

## 5.3 交通領域證據與限制

香港政府試點報告說明傳統預設配時與變動人車需求之間的管理問題，但沒有提供完整可重現的演算法與對照設計。[D1] Wu 等人以中國百城資料與模擬分析自適應控制的潛在效益，提示成效須連同環境與假設解讀。[D2] FHWA 指南則提供綠燈、黃燈、清道與評估的基礎概念；本文引用的是已封存的 2008 年版，不把它當作最新規範或臺灣法規。[D3]

## 5.4 研究缺口與本專題定位

Existing Research：既有研究分別涵蓋可檢查政策、多路口協作、事件處理及城市尺度效益。

Limitations for this Project：其訓練、資訊需求、控制範圍及驗證環境，與本案單路口開發板展示不同。

Project Gap：本案已有決策與控制核心，但仍需把任務、資料資格、選擇依據及執行確認串接成統一流程；這是已識別的本專題整合缺口，不是宣稱整個領域無人研究。

Our Project：以四特徵、三方案及 ARM／FPGA 分層建立可追溯原型；以固定配時和反例檢查效果，並透過 OpenSpec 將上述缺口轉為明確需求與後續任務。

文獻組合為三個 AI 原始研究與三個交通來源。A2、A3 採指定 arXiv 版本；D1 是政府報告，D3 是工程指南，不將六個來源統稱為六篇近期學術論文。

<!-- landscape -->
# 5.5 Article Summary Table

| Ref | Year | Problem | AI Method | Domain Knowledge | Dataset | Findings | Limitation |
|---|---|---|---|---|---|---|---|
| A1 VIPER | 2018 | 學習政策難檢查 | DNN 政策及 Q 函數引導決策樹抽取 | 政策、動作價值與控制性質 | 符號化 Pong、簡化 Pong、cart-pole | 在指定任務展示樹政策與性質驗證 | 非交通研究；本案未重現抽取或形式驗證 |
| A2 CoLLMLight | 2025 | 多路口缺少協作 | 時空圖、LLM 協作推理與微調 | 鄰接路口及需求時間變化 | 濟南、杭州、紐約交通流及合成流；CityFlow | 作者在所測路網中報告協作控制成效 | 指定預印本；模擬不等於道路部署；規模大於本案 |
| A3 Virtual Traffic Police | 2026 | 非預期事件使控制器難調整 | 上層 LLM 調參、檢索與 verifier | 事件資訊、控制器操作知識 | SUMO 單路口；60 分鐘事件情境 | 展示上層協助既有下層控制器的分工 | 指定預印本；本案未實作事件處理、RAG 或 LLM |
| D1 香港政府 | 2025 | 預定配時不易配合變動需求 | 官方稱以 AI 分析；細節未公開 | 不同方向、時段、人車需求 | 東涌八個連動路口等試點敘述 | 提供自適應配時的實務動機 | 官方報導非完整實驗論文；不能移植其效果 |
| D2 Wu 等 | 2025 | 城市號誌對壅塞及排放的影響 | 資料驅動自適應控制 | 流量、容量與情境條件 | 中國百城；路網、車速與 CBEngine 模擬 | 估計控制效益及其情境差異 | 城市模擬與估計不是本原型的道路或減碳證據 |
| D3 FHWA | 2008 | 通行需求與相位約束的取捨 | 不限定 AI | 最小綠燈、黃燈、清道與行人 | 工程概念、公式及案例 | 提供配時與評估的基礎框架 | 已由新版取代；非臺灣法規或本展示秒數的合規依據 |

應用方式：A1 支持政策表示的討論；A2、A3 用於比較架構與範圍；D1、D2 支持問題動機；D3 提醒相位與評估限制。文獻效果、既有原型結果與預期整合成果分開陳述。

<!-- page -->
# 6 五個核心與三個取捨

## 五個核心 C1–C5

| 核心 | 核心問題與設計 | 可檢查成果 |
|---|---|---|
| C1 資料可追溯 | 先確認來源、時間、單位、品質與兩軸配對；不以缺值冒充零車流 | 來源清單、資料雜湊及拒絕原因 |
| C2 需求狀態建模 | 同時考慮累積佇列及最近 30 秒需求；僅用已觀測歷史 | 四特徵與觀測時間界線 |
| C3 有限且可解釋決策 | 決策樹只選 0／1／2，記錄模型或規則回退，不宣稱全域最優 | 方案、特徵、模型識別與回退旗標 |
| C4 決策與執行分工 | ARM 提交 pending plan，FPGA 於完整週期邊界套用 | active_plan、cycle_count 與對應提交 |
| C5 同條件評估 | 比較固定與模型加回退，保留方向代價、未完成車輛及退步案例 | 配對結果、期末佇列、失敗案例 |

這五個核心也對應五種研究思維：由需求出發、以歷史狀態描述問題、限制決策權限、區分證據層級，以及以反例約束結論。

## 三個取捨 T1–T3

T1 規則直接決策 vs. 決策樹近似：直接規則容易追溯評分，決策樹則適合展示學習、固定記憶體推論與部署。[A1] 本案保留既有樹，規則作標籤來源及域外回退。代價是近似誤差；現有證據沒有證明樹優於規則，因此不將此列為成果。

T2 即時改相位 vs. 週期邊界更新：頻繁調整可能更快回應突發需求，邊界更新則較容易維持相位與倒數的一致性。[A3][D3] 本案固定在完整週期採用新方案，接受短時需求的反應延遲；不新增中途延長或重啟綠燈功能。

T3 整體效率 vs. 方向代價與證據完整性：合計排隊車秒便於比較，但可能掩蓋某方向長等待及未放行車輛。[D2][D3] 本案同時報告期末兩向佇列、放行數與退步案例。代價是報告較複雜，但能避免只用平均值宣稱全面改善。

仍待回答：小動作空間是否需要模型、邊界更新對短突發需求的損失有多大，以及簡化 FIFO 結果可外推至何種場域。這些問題由實驗支持，不能只靠架構推論。

<!-- page -->
# 7 十個設計細節

| ID | 問題與決定 | 驗收重點 |
|---|---|---|
| D01 使用範圍 | 單路口、南北與東西兩軸直行；不含行人及轉彎 | 任務宣告範圍；不輸出域外成效聲稱 |
| D02 任務入口 | dataset_id、mode、policy、固定目標與觀測窗 | 缺欄位拒絕；review 模式不得寫入裝置 |
| D03 資料資格 | 保留來源、雜湊、時間、單位與配對證據 | 缺分鐘、未知單位或無兩軸證據時停止控制實驗 |
| D04 介面容量 | 現有逐秒到車介面每軸 0／1 | 大於 1 不默默縮放；分鐘資料另行標示衍生方法 |
| D05 特徵 | queue_NS、queue_EW、arrivals_NS_30、arrivals_EW_30 | 只用當下及過去完整 30 秒；不讀未來列 |
| D06 模型域 | 佇列每向 0–120，到車每向 0–30 | 域外標記規則回退，與樹推論次數分開 |
| D07 三方案 | 綠燈 12／12、16／8、8／16 秒，plan_id 0／1／2 | 方案代碼與政策代碼分開；非法方案拒絕 |
| D08 相位時序 | 每方向黃燈 2 秒、全紅 1 秒，總週期 30 秒 | 邊界前保持當期相位長度與倒數 |
| D09 生效確認 | 將 submitted、applied、timeout、mismatch 分開 | matching active_plan 加預期週期；僅 ACK 不算成功 |
| D10 績效邊界 | 600 筆輸入計分，最後一次生效可窗外確認 | 不增加第 601 筆到車或清空佇列以改善數字 |

## 三個容易混淆的介面

policy 0 代表固定均衡策略，policy 2 代表現有模型加規則回退策略；它們不是三個 plan_id 的同一組定義。plan_id 0／1／2 才分別對應均衡、南北優先、東西優先。

ta_model_predict() 的底層域外防護會回傳均衡方案，但正式 traffic_agent.c 先檢查有效域，域外走既有規則。比較結果及本規格使用的是「決策樹＋韌體規則回退」，不將底層防護誤寫成正式政策。

queue 為 ARM 簡化模型的估計值，並非現場攝影機或道路感測器量到的排隊。官方分鐘資料與合成逐秒輸入必須分開標示。

<!-- page -->
# 8 重整後的系統設計

## 八個模組與回饋

[[architecture]]

① 任務入口記錄資料批次、模式與政策。② 資料檢查決定控制資格，資料不足時回報缺口。③ 分析引擎維護 FIFO 與四特徵。④ 決策樹或既有回退規則選出方案。⑤ 領域限制檢查方案、模型域與週期條件。⑥ 依據報告記錄實際輸入及決策來源。⑦ ARM／AXI 提交 pending plan，FPGA 執行。⑧ 回讀方案與週期，提供確認或失敗結果。

既有基礎為③④⑤⑦⑧的板端核心及實驗紀錄；①②⑥的通用整合仍待實作，部分資料整理與實驗報告工具已存在。規格描述整合目標，不能據此把全部模組標為已完成。

## 三個合法方案

| plan_id | 用途 | NS 綠燈 | EW 綠燈 | 共通設定 |
|---|---|---:|---:|---|
| 0 | 均衡 | 12 秒 | 12 秒 | 各方向黃燈 2 秒、全紅 1 秒 |
| 1 | 南北優先 | 16 秒 | 8 秒 | 週期總長 30 秒 |
| 2 | 東西優先 | 8 秒 | 16 秒 | 完整週期邊界採用新方案 |

相位順序：NS 綠 → NS 黃 → 全紅 → EW 綠 → EW 黃 → 全紅。以上數字僅是桌上原型設定，不是實際道路設計標準。

<!-- page -->
# 9 工作流程與核心演算法

## 任務狀態

任務依序為 received、qualified、observing、decided。資料不合格進入 rejected；review 模式到 reported 結束而不提交。execute 模式經 submitted 後，只有與預期週期相符的回讀才轉 applied；逾期或不一致分別轉 timeout 或 mismatch。所有結果都進入任務報告。

## 核心偽碼

```text
01 Read request, dataset manifest, mode and policy
02 Validate fields, source, timestamps, units and paired axes
03 If invalid: report rejection; do not submit a plan
04 Initialize queues and keep the existing balanced first cycle
05 For each actual observation in the declared window:
06   Update FIFO queues and the causal 30-second history
07   If a complete decision window is not ready: continue
08   If fixed policy: choose plan 0
09   Else if in-domain: infer with the existing tree
10   Else: choose by existing rules; mark fallback
11   Record features, model ID, plan and decision source
12   If review-only: emit recommendation; continue
13   Validate legal plan, device state and submission deadline
14   If invalid: record rejection or expiry; continue
15   Submit pending plan without restarting the current phase
16   Wait for readback at the expected complete cycle
17   Record applied, timeout or mismatch with the evidence
18 Freeze metrics after the declared observations are consumed
19 Verify the last application without adding arrivals or metrics
20 Emit provenance, decisions, comparison and limitations
```

這是整合目標的偽碼，新增的通用任務層尚未實作。已有板端引擎、相位控制與實驗腳本提供部分對應元件，後續以 TRACEABILITY.md 串接需求與實作。

## 指標定義

排隊車秒 QVS = sum_t (q_NS(t) + q_EW(t)) × 1 秒；q 在每筆到車與本秒放行後統計。已放行平均等待 = 已放行車輛等待總秒數 ÷ 放行數，分母為零時記為未定義，不填零。

相對變化 = 100 × (QVS_model − QVS_fixed) ÷ QVS_fixed。負值代表模型政策較少；固定值為零時不計百分比，改列絕對差。合計比例由加總後的數字計算，不平均各組百分比。

<!-- page -->
# 10 既有證據與評估計畫

## 分批呈現既有結果

| 證據批次 | 固定車秒 | 模型＋回退車秒 | 相對變化 | 解讀 |
|---|---:|---:|---:|---|
| 18 組主機配對 | 399,954 | 326,830 | −18.28% | 13 組改善，5 組退步 |
| 另一批 6 組主機配對 | 137,493 | 110,395 | −19.71% | 4 組改善，2 組退步 |
| 1 組實板方向轉換 | 10,369 | 3,089 | −70.21% | 單一合成輸入；FPGA 驅動 ARM FIFO |

上述批次可能共用情境與輸入，不當作獨立樣本合併，不據此作統計顯著性聲稱。18 組數字取自 firmware_validation.json；6 組與實板數字取自 2026-10-30 實驗報告及比較檔。[P3][P4]

## 六組主機案例與反例

| 情境 | 固定 | 模型＋回退 | 變化 | 模型／回退次數 |
|---|---:|---:|---:|---:|
| balanced | 3,035 | 3,263 | +7.51% | 20／0 |
| ns_heavy | 11,815 | 3,202 | −72.90% | 20／0 |
| ew_heavy | 14,972 | 3,126 | −79.12% | 20／0 |
| direction_switch | 10,369 | 3,089 | −70.21% | 20／0 |
| bursty | 3,485 | 4,126 | +18.39% | 20／0 |
| overload | 93,817 | 93,589 | −0.24% | 10／10 |

平衡與突發情境均變差。超載情境兩政策各剩 306 輛，但期末 NS／EW 佇列由固定的 155／151 變為模型的 79／227；微小合計改善不能解讀為解決超載或改善所有方向。

## 後續驗收

整合驗收將涵蓋正常任務、資料拒絕、域外回退、唯讀模式、方案逾期、不一致與統一報告。沿用已保存輸入作比較，紀錄雜湊、政策、觀測窗、初始條件及模型版本。硬體功能與交通效益分開評估；官方資料未達連續、同路口兩軸及介面資格時，只輸出資料品質結果。

<!-- page -->
# 11 OpenSpec 工作流程

## SDD 的用途

規格驅動開發先明確寫出系統應有的行為、條件及例外，再將它們轉成實作與驗收任務。OpenSpec 使用 proposal 說明改變原因、specs 定義需求與情境、design 記錄方法與取捨、tasks 追蹤工作；完成並驗證後可 archive，將差異合併到主規格。[O1][O2]

本作業已安裝 OpenSpec 2.0.0，以 init --tools none 建立獨立規格目錄。文件重整變更 refactor-project-proposal 於實際完成後封存；後續產品整合變更 integrate-task-workflow 保留為未實作，避免把文件存在誤當功能完成。

## DESIGN.md 到規格的映射

| 原設計內容 | OpenSpec 對應 | 主要行為 |
|---|---|---|
| 模型、方案與相位 | specs/traffic-control-core | 四特徵、三方案、域外回退、邊界更新 |
| 相同輸入與指標 | specs/paired-evaluation | 公平配對、績效窗、反例與證據批次 |
| 通用需求入口 | changes/integrate-task-workflow/specs/task-intake | 必要欄位及 review／execute 分流 |
| 資料資格檢查 | changes/integrate-task-workflow/specs/data-qualification | 缺值、來源、兩軸、時間與容量 |
| 選擇理由 | changes/integrate-task-workflow/specs/decision-evidence | 特徵、決策來源與模型識別 |
| 生效確認 | changes/integrate-task-workflow/specs/execution-verification | 提交與採用分離，逾期／不一致 |
| 統一結果 | changes/integrate-task-workflow/specs/task-reporting | 任務、選擇、執行與結果互相對應 |

## 需求情境示例

```text
### Requirement: Distinguish submission from application
The system SHALL confirm application only from matching
active_plan and the expected cycle, linked to the submission.
#### Scenario: Receipt without application evidence
- WHEN a command is acknowledged but the expected cycle has
  not been observed
- THEN its status remains submitted, not applied.
```

openspec validate 檢查規格格式與結構；驗收測試才檢查產品行為。status 顯示 artifacts complete 時，也必須查看 tasks 是否尚未完成。完整指令、實際版本、退出碼與輸出存於 OPEN_SPEC_WORKFLOW.md 及 evidence/。

<!-- page -->
# 12 驗收情境與實作任務

以下為未來整合必須滿足的產品驗收規格，尚未以本次文件工作執行；不能將本表當成測試通過紀錄。

| 情境 ID | 輸入或事件 | 預期行為 |
|---|---|---|
| AT01 | 必要任務欄位缺漏 | 回傳 missing_fields；不寫入裝置 |
| AT02 | mode = review | 產生建議與依據；裝置寫入數為零 |
| AT03 | 官方資料只有一分鐘或沒有兩軸證據 | 拒絕控制用途，保留品質摘要 |
| AT04 | 缺分鐘、未知單位或每軸每秒值大於 1 | 指出原因；不補零、不縮放、不任意配對 |
| AT05 | 尚未取得完整 30 秒歷史 | 不作模型決策，維持既有初始方案 |
| AT06 | queue = 121 或 arrivals_30 = 31 | 走韌體規則回退，增加回退計數 |
| AT07 | plan_id 不在 0／1／2 | 拒絕提交並記錄非法方案 |
| AT08 | 在當前綠燈期間收到新方案 | 不重啟倒數；只在完整週期套用 |
| AT09 | 有 ACK 但沒有對應週期回讀 | 保持 submitted；逾時後標 timeout |
| AT10 | 回讀週期正確但 active_plan 不符 | 標 mismatch，保留原始提交及回讀 |
| AT11 | 已消耗 600 筆且最後方案未確認 | 凍結績效，僅繼續確認，不加到車 |
| AT12 | 模型比固定差或有殘餘佇列 | 報告退步、兩向佇列及未服務需求 |

## 實作順序

第一階段建立 request／manifest schema 與資格檢查，接著將既有 FIFO、決策樹及回退包成可追溯的任務流程。第二階段整合 readback 狀態與報告。第三階段以保存資料執行上述情境，確認來源與結果一致後，再安排必要的實板驗收。

每個階段皆在 tasks.md 保留未勾選狀態；只有取得對應測試或回讀證據，才改為完成。來源不合格不代表系統故障，能明確拒絕並說明原因也是驗收行為。

## 本次重整的結論

本專題已有模型與板端控制基礎，下一步核心是任務與證據整合。重整後的 A–F、Introduction、Related Work、design.md 與 OpenSpec 指向相同範圍：讓交通配時建議可以解釋、可以核對，也可以在相同條件下被比較與反駁。

<!-- page -->
# 13 References

[A1] O. Bastani, Y. Pu, and A. Solar-Lezama. Verifiable Reinforcement Learning via Policy Extraction. NeurIPS 31, 2018. https://proceedings.neurips.cc/paper/2018/hash/e6d8545daa42d5ced125a4bf747b3688-Abstract.html

[A2] Z. Yuan, S. Lai, and H. Liu. CoLLMLight: Cooperative Large Language Model Agents for Network-Wide Traffic Signal Control. arXiv:2503.11739v1, 2025-03-14. https://arxiv.org/html/2503.11739v1

[A3] S. Wei, Q. Wang, and K. Yang. Virtual Traffic Police: Large Language Model-Augmented Traffic Signal Control for Unforeseen Incidents. arXiv:2601.15816v1, 2026-01-22. https://arxiv.org/html/2601.15816v1

[D1] Hong Kong Information Services Department. Adaptive system optimises traffic flow. 2025-11-23. https://www.news.gov.hk/eng/2025/11/20251120/20251120_183103_322.html?type=ticker

[D2] K. Wu et al. Big-data empowered traffic signal control could reduce urban carbon emission. Nature Communications 16, 2013, 2025. DOI: 10.1038/s41467-025-56701-4. https://doi.org/10.1038/s41467-025-56701-4

[D3] P. Koonce et al. Traffic Signal Timing Manual. FHWA-HOP-08-024, 2008. Archived edition; replaced by the second edition. https://ops.fhwa.dot.gov/publications/fhwahop08024/chapter5.htm

[O1] Fission AI. OpenSpec, official repository. https://github.com/Fission-AI/OpenSpec

[O2] Fission AI. OpenSpec CLI documentation. https://openspec.dev/docs/cli

[P1] 第 13 組。交通配時助手期末專題提案，2026-11-03。Traffic_Assistant_Proposal_2026-11-03.pdf。

[P2] TrafficAgent/DESIGN.md 與 project/embedded/model/traffic_model.h；於 2026-11-13 讀取。本包保留原 DESIGN 快照及雜湊。

[P3] project/embedded/validation/firmware_validation.json：54 案例中的 18 組固定／模型配對；本包 evidence/ 保留原始結果與重新計算摘要。

[P4] project/embedded/validation/experiments/2026-10-30_fixed_vs_model/report/EXPERIMENT_REPORT.md 及 host/results_004/comparison.json；本包 evidence/ 保留副本。

[H1] DIC3-Project Proposal Refactor using Openspec，iLearning 3.0，四頁作業說明。https://lms2020.nchu.edu.tw/course/homework/76781

[H2] 課堂範例 repository。https://github.com/huanchen1107/2026-11-11-DIC3-ProjectRefactor

查核日期：2026-11-13。D2 的出版者全文頁有存取限制，本次以原提案研究筆記、出版者索引與 PubMed 書目核對；不聲稱重新逐頁審閱完整論文。其餘學術來源以列出的正式頁或指定預印本版本為準。
