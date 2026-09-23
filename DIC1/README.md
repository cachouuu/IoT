# Sam Wei — Personal Website

IoT / DIC-1 個人網站。呈現自我介紹、技能、專案作品、課程作業入口與即時時鐘。

## 目前狀態

網站已於 2026-09-24 發布至 GitHub Pages，並確認公開頁面可正常開啟。

- [Live Website](https://cachouuu.github.io/IoT/)
- [GitHub Repository](https://github.com/cachouuu/IoT/tree/main/DIC1)

- 姓名沿用上學期 DRL 個人頁的 Sam Wei。
- 科系、聯絡方式與個人照片待本人補充；目前使用 SW 字母 Avatar。
- Python、DRL、PyTorch 依既有 DRL 作業內容列為課程實作。
- 依使用者指示，由 Codex Agent 協助設計、實作、測試與發布。

## 作業要求對應

| 要求 | 網頁位置／實作 |
| --- | --- |
| Profile | About：姓名、SW Avatar、自介、興趣；科系留白 |
| 至少 3 項 Skills | Python、DRL、PyTorch |
| 至少 1 個 Project | DRL 的 Deep Q-Network & Variants，附介紹、技術與連結 |
| JavaScript Live Clock | 頁面下方，HH:MM:SS，每秒更新 |
| Personal Design | 襯線字體、非對稱排版、靜物影像、細線與留白 |
| GitHub 與 Live Website | 已公開發布並開啟驗證 |

選用加分功能：早午晚問候、12H／24H 切換、自動時區、複製含時區的 timestamp、localStorage 記住時間格式、響應式排版、尊重減少動態效果設定。

## 檔案

```text
index.html                     頁面內容與結構
style.css                      電腦／平板／手機版面
app.js                         待補欄位、時鐘與偏好設定
assets/editorial-still-life.jpg 原創靜物影像
.nojekyll                      GitHub Pages 靜態檔案設定
README.md                      說明與發布方式
```

沒有套件安裝或編譯步驟，也不依賴外部字型 CDN。可直接打開 `index.html`；完整測試（含複製功能）建議使用本機 HTTP 預覽或 GitHub Pages 的 HTTPS 網址。

在此資料夾執行 `python3 -m http.server 8765`，再開啟 `http://localhost:8765/`。

## 補上個人資料

`app.js` 最上方 `PROFILE` 可以修改 About 區的姓名、科系、自介、興趣，以及頁尾聯絡文字。空字串代表保留現有文字或「待補充」。這些是網站的公開內容，不要填入不希望公開的資料。

```js
const PROFILE = {
  name: 'Sam Wei',
  department: '',
  bio: '',
  focus: '',
  contact: '',
};
```

如需更改顯示名字，首頁大標、頁面 title、meta description、Avatar、頁尾署名與相關無障礙標籤也要在 `index.html` 同步修改。若填入自介或照片，請同步更新 About 區的「待補資料」說明。

個人照片可放入 `assets/portrait.jpg`，將 `index.html` 中的 `.avatar` 元素換成對應圖片，提供描述性的 `alt`。目前筆記本影像僅為氣氛主視覺，不代表本人照片。

## AI 開發紀錄

依使用者明確指示，本次使用 Codex Agent 完成。工作包含：讀取作業原文、確認上學期已存在的姓名與作品、建立原創編輯式版面、生成靜物影像、實作即時時鐘及響應式排版、測試功能與 GitHub Pages 路徑。

## 發布至 GitHub Pages

此作業存放於 `IoT` 儲存庫的 `DIC1/`。共用 GitHub Actions 流程會將個人頁部署至網站根目錄，HW1 部署至 `/HW1/`。推送到 `main` 後會重新執行部署。

設定與操作見 [IoT 儲存庫說明](../README.md)。

## 視覺與內容來源

- 版面方向參考 [LEMAIRE 官網](https://www.lemaire.fr/) 的服裝、作品與影像編輯語彙；沒有複製其商標、照片或版型。
- 靜物影像：本次以 ImageGen 原創生成，沒有使用參考照片。內容為空白筆記本、深色織物、灰色石面與日光。
- 姓名與作品來源：[上學期個人頁](https://cachouuu.github.io/DRL/L1-PersonalPage/index.html)、[DRL repository](https://github.com/cachouuu/DRL)、[DQN 專案](https://github.com/cachouuu/DRL/tree/main/docs/HW3-DQN)。
- 作業原文：使用者提供的「DIC-1: Personal Page using antigravity and github」PDF。

## 驗證紀錄

程式邏輯檢查通過：午夜與正午 12H、24H 切換、跨年、儲存權限被封鎖、含 UTC offset 的 timestamp、剪貼簿成功／失敗提示、每秒更新；頁內錨點及本地資產存在。實際瀏覽器測試 320、390、768、1440px 皆無水平溢出；圖片載入、12H／24H 切換、偏好儲存、複製時間與 DRL 作品連結已確認正常。公開頁面已開啟確認。

## 作業導覽

此個人頁是課程作業的首頁（DIC1）。頂部導覽與 Coursework 區提供 [HW1 台灣天氣網站](https://cachouuu.github.io/IoT/HW1/) 的入口。學習方向包含 DFT、硬體安全、圖神經網路與無監督學習，與既有課程實作技能分開呈現。
