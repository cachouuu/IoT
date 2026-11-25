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

# 3 精簡摘要與 IEEE 風格摘要

## 中文精簡摘要

固定號誌配時未必能適應不同方向與時段的車流需求，而模型推薦也不代表硬體已確實執行。本專題提出交通配時助手，以單路口兩軸直行為範圍，結合資料資格檢查、小型決策樹與 ARM／FPGA 分層控制。ARM 根據估計佇列及過去三十秒到車數，在均衡、南北優先與東西優先三種方案中選擇；超出模型有效域時採規則回退。FPGA 維持固定相位順序，於完整週期邊界採用方案，並提供生效回讀。評估以相同輸入比較固定配時與模型政策，觀察排隊車秒、等待、剩餘車輛及方向差異，同時保留退步案例。預期成果是能追溯資料、選擇依據與執行結果的課程原型，並以 OpenSpec 管理需求、情境與任務。既有結果僅支持合成情境與板端執行可行性，不推論實際道路效益。

## English Title

Traffic Timing Assistant: An Evidence-Traceable Decision-Tree Framework with ARM–FPGA Execution Feedback

## Abstract

Fixed signal plans may allocate green time poorly when directional demand changes. A traffic-control prototype must also distinguish a recommended plan from a plan that has actually taken effect. This project proposes a traffic timing assistant for a single intersection with two through-traffic axes. The framework combines data qualification, a compact decision-tree policy, and layered ARM–FPGA execution. The ARM processor maintains estimated FIFO queues and arrival counts from the preceding 30 seconds. A pre-existing integer decision tree selects one of three predefined timing plans, while the firmware uses reference-rule fallback for inputs outside the supported domain. The FPGA preserves a fixed phase order and adopts pending plans only at complete cycle boundaries. A planned task layer links data provenance, observed features, decision sources, submitted commands, and execution readback in a unified report. Evaluation compares the fixed balanced plan with the tree-plus-fallback policy under identical saved inputs, initial conditions, service assumptions, and observation windows. Queue vehicle-seconds are the primary metric, supplemented by completed-vehicle waiting time, throughput, residual queues, and fallback counts. Existing synthetic experiments show both improvements and regressions, motivating scenario-level reporting rather than a universal performance claim. OpenSpec specifications translate the design into explicit requirements, acceptance scenarios, and implementation tasks. The expected contribution is a reproducible educational system that connects traffic analysis to bounded decisions and verifiable execution feedback. The current evidence supports simplified-model evaluation and prototype execution; real-road effectiveness remains unverified.

Index Terms—Traffic signal control, decision trees, embedded systems, FPGA, execution feedback, spec-driven development.
