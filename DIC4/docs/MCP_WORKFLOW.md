# DIC4 MCP 使用紀錄與可重現示範

## 本次完成的用途

本專案使用 MCP 讓文件製作端讀取限定的研究材料：列出證據來源與雜湊、取得既有結果的稽核摘要，以及讀取原設計的架構與模型段落。這是論文撰寫與來源追溯流程；交通控制仍是原設計的 ARM 決策與 FPGA 執行。

本次另外實作並執行一個可攜的本機唯讀 MCP server。示範使用官方 Python SDK `mcp==1.29.0`、`FastMCP`、`stdio_client` 與 `ClientSession`，真實啟動獨立 server 程序，完成初始化、工具探索及三次工具呼叫。

這個示範不會寫入裝置、不會重新執行交通實驗，也不會操作 Overleaf、GitHub 或課程作業區。線上發布的完成與否應另查最終交付紀錄。

## 可重現執行

使用 Python 3.10 以上版本，在專案根目錄執行：

```bash
python -m pip install -r mcp/requirements.txt
python mcp/demo_client.py
```

client 會自動透過 stdio 啟動 `mcp/evidence_server.py`，呼叫其工具，執行結果核對，最後寫出 `evidence/current/mcp_run.json`。不需要帳號、API key、網路服務或開發板。安裝套件時需能取得指定版本；實際示範讀取的全部資料均隨專案提供。

若缺少指定的證據檔案或核對失敗，執行結果會是 `FAIL` 與非零結束碼，不會自動建立假的資料或成功紀錄。執行會更新該 JSON 的時間與紀錄。

## 工具及其讀取範圍

三個工具均無檔案路徑參數，並宣告 read-only、idempotent、non-destructive；server 的實作只讀取下列固定專案檔案。

| MCP 工具 | 實際用途 | 固定來源 |
|---|---|---|
| `list_evidence` | 回傳來源相對路徑、檔案大小與 SHA-256 | 當次稽核 JSON、封存設計、封存 54 筆主機紀錄 |
| `summarize_archived_results` | 讀取兩組歷史摘要、重疊限制與證據狀態 | `evidence/current/audit_results.json` |
| `read_architecture_excerpt` | 回傳原設計第 2、5 節逐字內容與行號 | `evidence/archive/dic3/source/DESIGN_original.md` |

工具清單的第三個固定來源為 `evidence/archive/dic3/evidence/firmware_validation_original.json`。client 使用此封存原始紀錄，獨立核對透過 MCP 收到的 18 組摘要；不是拿摘要與自己比較。

原設計段落保留了當時的「本輪」等措辭；其時間指向封存原文件，不能解讀成 DIC4 當次又做了一次板測。

## 本次實際觀測

| 項目 | 實際結果 |
|---|---|
| 執行完成時間 | 2026-11-25 15:37:50 UTC（臺灣 23:37:50） |
| SDK | `mcp 1.29.0` |
| Server 初始化名稱 | `traffic-assistant-evidence` |
| Server 回報版本 | `1.29.0` |
| 實際協商 protocol version | `2025-11-25` |
| 呼叫方法 | `initialize`、`tools/list`、`tools/call` × 3 |
| 結果 | **PASS，14／14 項核對通過** |

`mcp_run.json` 保留實際 SDK 回傳的初始化結果、工具定義、三次工具的文字與結構化結果、每次呼叫的時間、程式雜湊，以及核對項目。它是 client API 層的實際呼叫紀錄，並非完整傳輸封包擷取；SDK 自動送出的內部通知不另外偽造為封包紀錄。

### 核對的實質內容

client 從保留的 54 筆歷史主機紀錄選出 `fixed_balanced` 與 `tiny_tree_rules_fallback`，按 scenario／seed 配對後重新計算：

| 指標 | 從封存紀錄重算 | MCP 回傳摘要 |
|---|---:|---:|
| 配對數 | 18 | 18 |
| 固定配時總排隊車秒 | 399,954 | 399,954 |
| 決策樹加規則回退總排隊車秒 | 326,830 | 326,830 |
| 較差案例數 | 5 | 5 |
| 相對變化 `(model - fixed) / fixed × 100%` | -18.28310256% | -18.28310256% |

另外核對三個來源檔案的雜湊、回傳架構摘錄與保留檔案一致、工具 allowlist 與唯讀屬性，以及「沒有新增訓練／推論／交通模擬／板測」的證據標記。

這些結果驗證本次 MCP 證據讀取與摘要對應正確；並不重新證明歷史交通實驗的原始執行。6 組紀錄與 18 組中的單一 seed 子集相符，也不能當成 24 組互相獨立的樣本。

## 作業要求的對應

- **MCP：**本機 client/server 的真實初始化、探索與工具呼叫已完成，附可重跑程式及紀錄。
- **OpenSpec：**另由 `scripts/validate_openspec.py` 保存實際 CLI 結構驗證，與 MCP 示範分開。
- **Overleaf／GitHub：**本機工具呼叫不會產生這兩項線上連結；請依交付紀錄確認是否實際匯入或上傳。

課堂若要求指定的 Overleaf MCP server 或指定平台連線，仍需按該補充規則操作。本示範明確展示可重現的 MCP 使用，沒有把未執行的遠端整合寫成已完成。

## 技術來源

本次 API 使用方式以已安裝的 `mcp==1.29.0` 官方 SDK 公開類別與函式簽章為依據；程式中沒有自行拼造遠端服務 API。SDK 專案：<https://github.com/modelcontextprotocol/python-sdk>。
