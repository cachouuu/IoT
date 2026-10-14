# DIC2 可重用迴歸工作流程

第二題依作業要求直接套用本工作流程。唯一需要變更的輸入是資料來源與目標欄位。

| CRISP-DM 步驟 | 共用實作 | 50 Startups | Boston Housing |
| --- | --- | --- | --- |
| 1. Business understanding | 明確定義目標與單位 | Profit，USD | MEDV，歷史千美元 |
| 2. Data understanding | `load_dataset`、缺失與重複檢查 | 50 列，State 類別 | 506 列，13 數值特徵 |
| 3. Data preparation | `prepare`，先 80/20 切分再編碼 | State 丟棄參考類別 | 原始數值欄位 |
| 4. Modeling | `choose_paths`，五方法，k=1…p | p=5 | p=13 |
| 5. Evaluation | `fit_record`，以訓練 CV 選定、測試只評估 | 40 訓練 / 10 測試 | 404 訓練 / 102 測試 |
| 6. Delivery | CSV / JSON / Notebook / 網站 | 第一選單項目 | 第二選單項目 |

```
load_dataset(key)
  → train_test_split(seed=0, test_size=0.2)
  → prepare(training categories / training medians)
  → choose_paths(5-fold training CV, seed=42)
  → freeze(method, subset, k)
  → fit_record(training OLS, holdout metrics)
  → export(CSV, JSON, website results)
```

使用：`python project/regression_workflow.py --dataset boston`。

避免資料洩漏：不能先看 test RMSE 再選方法、k 或亂數種子。每個子集的 CV 是選擇準則，含選擇偏差；獨立評估使用保留測試資料。係數檢定為探索性推論。

瀏覽器加分流程：CSV → 選數值目標 → 訓練集前處理 → 五方法子集 → CV 選定 → OLS / test 評估 → 同一展示介面。瀏覽器亂數演算法與參數網格較小，與 Python 固定種子不保證產生相同切分。
