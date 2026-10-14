# DIC2：50 Startups / Boston Housing

魏柏勝 / 7114056191。主繳交題目採 **50 Startups**，第二題 **Boston Housing** 直接套用相同的 CRISP-DM 迴歸工作流程。由 Codex 協助分析、實作與驗證。

## 繳交

- `submission/7114056191_DIC2.zip`：完整繳交包，包含報告、已執行 Notebook、原始資料、程式、結果及加分網站。
- `output/pdf/7114056191_DIC2_report.pdf`：以 50 Startups 為主，附 Boston 與加分展示。
- `7114056191_DIC2.ipynb`：已實際執行並保存輸出的 Notebook。
- `submission/iLearning_submission.txt`：可貼到 iLearning 的繳交說明。

作業原文要求兩題都做，但可選一題上傳。PDF 第 3 頁的加分是兩題下拉選單（+1）及可任意載入 Dataset（+2）。文件內示範作者的 GitHub 設定步驟與「已推播」文字只是參考範例，不表示本儲存庫已發布。

## 加分網站

已發布：[DIC2 Regression Studio](https://cachouuu.github.io/IoT/DIC2/)。[個人首頁](https://cachouuu.github.io/IoT/) 的頂部導覽與 Coursework 區皆有入口，DIC2 頁首可返回首頁。

在本資料夾執行：

```sh
python -m http.server 8765 --directory site
```

開啟 `http://localhost:8765/`。

1. 下拉選單切換 **50 Startups / Boston Housing**，同步更新圖表、指標、特徵上限、係數與預測表單。
2. 點 **載入自訂資料**，可上傳 CSV 或輸入公開 CSV URL。
3. 點 **載入**、選數值目標、點 **開始分析**。瀏覽器 Web Worker 會實際重新訓練與評估，並加入「自訂資料」選項。
4. 比較五種方法，調整 k，查看訓練 CV / 測試誤差、係數、ANOVA、殘差，或下載測試預測 CSV。

老師的資料網址可直接貼入：

`https://raw.githubusercontent.com/Avik-Jain/100-Days-Of-ML-Code/master/datasets/50_Startups.csv`

本機範例：`site/startup.csv`、`site/boston.csv`、`site/custom_example.csv`。

自訂 CSV 支援數值和類別特徵；目標需為數值，至少 20 筆有效目標。空目標列排除，常數特徵移除；訓練中位數填補數值缺失，類別只由訓練集合編碼，未知測試類別使用全零參考編碼。空白值不誤認為數值 0。完全共線性的資料顯示可理解的錯誤，不假裝成功。

上限為 5 MB、5,000 列、16 個編碼特徵；瀏覽器窮舉搜尋最多 12 特徵、1,000 列，超限明確停用該方法。CSV URL 須允許 CORS；可改以上傳檔案使用。自訂分析需 HTTP / HTTPS，不能直接以 `file://` 執行 Worker。上傳 CSV 由瀏覽器處理，不傳送到伺服器。

## 重新執行兩題

Python 3.12 建議使用獨立環境：

```sh
python -m venv .venv
source .venv/bin/activate
python -m pip install -r project/requirements.txt
python project/regression_workflow.py --dataset all
```

第二題直接套用同一流程：

```sh
python project/regression_workflow.py --dataset boston
```

執行結果保存為 `output/*_results.json`、`*_metrics.csv`、`*_coefficients.csv`、`*_test_predictions.csv`，並更新網站的 `site/results.js`。數字沒有從老師範例硬編碼。

Python 內建分析採 `train_test_split(test_size=0.2, random_state=0)`；5-fold 訓練 CV 使用 `shuffle=True, random_state=42`。特徵與 k 由訓練 CV 決定，測試集只在候選與選定模型固定後評估。CV 分數是模型選擇依據，包含選擇偏差，不宣稱為無偏泛化估計。Lasso / Elastic Net 為標準化正則化係數**排序**，前 k 特徵最後重估 OLS；不能把表上的 OLS 係數誤稱為 Lasso 係數。

自訂資料使用 JavaScript 的固定種子洗牌與較小的正則化參數網格；其亂數演算法不同於 Python，載入相同檔案後的子集或分數可能不同，介面明確揭露。

## 本次真實結果

| 題目 | 訓練 / 測試 | 訓練 CV 選定 | Test RMSE | Test R² |
| --- | --- | --- | --- | --- |
| 50 Startups | 40 / 10 | Forward SFS，k=3 | 8,376.4505 USD | 0.9451 |
| Boston Housing | 404 / 102 | Lasso 排序 + OLS，k=11 | 5.7814 歷史千美元 | 0.5895 |

50 Startups 的 Lasso 排序 k=2 也重現老師示範：R&D Spend + Marketing Spend，Test RMSE 8,198.7972；此模型是候選，未以其測試分數回頭改選正式模型。完整 5 特徵 OLS Test RMSE 為 9,137.9902。

## 發布狀態

2026-10-14 已推送至 `cachouuu/IoT` 的 `main`，GitHub Pages [部署成功](https://github.com/cachouuu/IoT/actions/runs/38531009035)。公開網址為 [https://cachouuu.github.io/IoT/DIC2/](https://cachouuu.github.io/IoT/DIC2/)。

原有 `.github/workflows/deploy.yml` 已整合 DIC1 首頁、HW1 天氣與 `DIC2/site/`；後續網站更新推送至 `main` 即可自動部署。公開頁面已實際驗證首頁入口、返回首頁、Boston 切換、CSV 上傳與老師指定 URL 的重新分析，手機版面和時鐘也通過。部署紀錄見 `output/deployment.json`、`output/live_verification.json`。尚未代為上傳 iLearning。

## 查核

`project/verify_results.py`：重新核對切分、OLS、指標、係數、CI、ANOVA，以及資料來源雜湊。

`project/verify_engine.cjs`：CSV 格式與錯誤處理、已知線性資料、與 Python 同一子集的係數／推論數值比對。

`project/verify_site.cjs`：使用 Playwright 檢查桌面／手機、兩題切換、k、預測、CSV 上傳與 URL 加分流程。需另有 Playwright 與 Chrome，詳見檔案內註解。查核結果記錄於 `output/verification.json` 與 `output/browser_verification.json`。

報告、Notebook 與 ZIP 重建：

```sh
python project/build_deliverables.py
```

PDF 建檔使用 macOS 的 Arial Unicode 字型；其他平台需將 `build_deliverables.py` 的字型路徑換為可嵌入的中文字型。這不影響分析與網站的跨平台執行。

## 資料來源與限制

- [50 Startups / Avik Jain](https://github.com/Avik-Jain/100-Days-Of-ML-Code/blob/master/datasets/50_Startups.csv)：作業指定來源。
- [Boston 原始 CSV / scikit-learn 1.1.3](https://github.com/scikit-learn/scikit-learn/blob/1.1.3/sklearn/datasets/data/boston_house_prices.csv)：506 列、13 特徵；另保存去除首列尺寸資訊的 CSV 供網站使用。
- [Boston 資料說明](https://scikit-learn.org/1.1/modules/generated/sklearn.datasets.load_boston.html)：歷史資料、MEDV 上限與 B 欄位的設計爭議限制外推，僅供課堂練習。
- [老師的互動示範](https://huanchen1107.github.io/AIoT-DIC2-MultipleLR/)：功能與題目參考，網站與計算自行實作。

資料 SHA-256：`output/data_sha256.json`。傳統 p 值與區間為選擇後的探索性推論，不代表因果關係。
