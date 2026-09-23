"""CWA 36-hour forecast parsing, explicit synthetic data, and local snapshots.

No API keys are written to SQLite. All forecast timestamps use Asia/Taipei.
"""

from __future__ import annotations

import json
import math
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from http.client import HTTPException
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener
from zoneinfo import ZoneInfo


TAIPEI = ZoneInfo("Asia/Taipei")
CWA_URL = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001?format=JSON"
MAX_RESPONSE_BYTES = 5 * 1024 * 1024
MAX_SNAPSHOTS_PER_SOURCE = 100
CITIES = (
    "臺北市", "新北市", "桃園市", "臺中市", "臺南市", "高雄市",
    "基隆市", "新竹市", "嘉義市", "新竹縣", "苗栗縣", "彰化縣",
    "南投縣", "雲林縣", "嘉義縣", "屏東縣", "宜蘭縣", "花蓮縣",
    "臺東縣", "澎湖縣", "金門縣", "連江縣",
)
_ELEMENTS = {"Wx", "PoP", "MinT", "MaxT", "CI"}
_COLUMNS = (
    "city", "start", "end", "weather", "weather_code", "min_temp",
    "max_temp", "rain_probability", "comfort",
)


class WeatherError(Exception):
    """A safe, user-facing forecast or storage error."""


class _NoRedirect(HTTPRedirectHandler):
    """Do not forward an Authorization header to a redirected destination."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _datetime(value, *, allow_naive=False):
    try:
        result = value if isinstance(value, datetime) else datetime.fromisoformat(value)
    except (TypeError, ValueError):
        raise WeatherError("資料中的日期時間格式不正確。") from None
    if result.tzinfo is None or result.utcoffset() is None:
        if not allow_naive:
            raise WeatherError("儲存時間必須包含時區。")
        result = result.replace(tzinfo=TAIPEI)
    return result.astimezone(TAIPEI).replace(microsecond=0)


def _optional_text(value):
    if value is None or value in ("", "-", "--"):
        return None
    if not isinstance(value, (str, int, float)) or isinstance(value, bool):
        raise WeatherError("氣象欄位格式不正確。")
    return str(value).strip() or None


def _optional_number(value, *, probability=False):
    text = _optional_text(value)
    if text is None:
        return None
    try:
        number = float(text)
    except ValueError:
        raise WeatherError("氣象數值格式不正確。") from None
    if not math.isfinite(number) or (probability and not 0 <= number <= 100):
        raise WeatherError("氣象數值超出有效範圍。")
    return int(number) if number.is_integer() else number


def parse_forecast(payload: dict) -> list[dict]:
    """Join known weather elements by city AND exact start/end interval.

    The official API's naive times mean Taiwan local time. Missing weather
    elements or parameters become None; unknown elements are ignored.
    Structural errors and explicit API failures are never reported as data.
    """
    if not isinstance(payload, dict):
        raise WeatherError("氣象回應必須是 JSON 物件。")
    success = payload.get("success")
    if success is not True and success != "true":
        raise WeatherError("中央氣象署未回傳成功的資料。")
    records = payload.get("records")
    locations = records.get("location") if isinstance(records, dict) else None
    if not isinstance(locations, list) or not locations:
        raise WeatherError("氣象回應缺少縣市預報。")

    rows = []
    seen_cities = set()
    for location in locations:
        if not isinstance(location, dict):
            raise WeatherError("縣市預報格式不正確。")
        city = location.get("locationName")
        if not isinstance(city, str) or not city.strip():
            raise WeatherError("縣市名稱缺漏或重複。")
        city = city.strip()
        if city in seen_cities:
            raise WeatherError("縣市名稱缺漏或重複。")
        seen_cities.add(city)
        elements = location.get("weatherElement")
        if not isinstance(elements, list):
            raise WeatherError("縣市預報缺少氣象欄位。")
        intervals = {}
        seen_values = {}
        for element in elements:
            if not isinstance(element, dict):
                raise WeatherError("氣象欄位格式不正確。")
            name = element.get("elementName")
            if not isinstance(name, str):
                raise WeatherError("氣象欄位名稱格式不正確。")
            if name not in _ELEMENTS:
                continue
            times = element.get("time")
            if not isinstance(times, list):
                raise WeatherError("預報時段格式不正確。")
            for period in times:
                if not isinstance(period, dict):
                    raise WeatherError("預報時段格式不正確。")
                start = _datetime(period.get("startTime"), allow_naive=True)
                end = _datetime(period.get("endTime"), allow_naive=True)
                if end <= start:
                    raise WeatherError("預報結束時間必須晚於開始時間。")
                key = (start.isoformat(), end.isoformat())
                row = intervals.setdefault(key, dict.fromkeys(_COLUMNS))
                row.update(city=city, start=key[0], end=key[1])
                parameter = period.get("parameter")
                if parameter is None:
                    parameter = {}
                if not isinstance(parameter, dict):
                    raise WeatherError("氣象參數格式不正確。")
                value = parameter.get("parameterName")
                if name == "Wx":
                    fields = {
                        "weather": _optional_text(value),
                        "weather_code": _optional_text(parameter.get("parameterValue")),
                    }
                elif name == "CI":
                    fields = {"comfort": _optional_text(value)}
                else:
                    field = {"MinT": "min_temp", "MaxT": "max_temp", "PoP": "rain_probability"}[name]
                    fields = {field: _optional_number(value, probability=name == "PoP")}
                value_key = (name, key)
                if value_key in seen_values and seen_values[value_key] != fields:
                    raise WeatherError("同一預報時段出現互相矛盾的資料。")
                seen_values[value_key] = fields
                row.update(fields)
        if not intervals:
            raise WeatherError("縣市沒有可使用的預報時段。")
        for row in intervals.values():
            if row["min_temp"] is not None and row["max_temp"] is not None:
                if row["min_temp"] > row["max_temp"]:
                    raise WeatherError("最低溫高於最高溫，資料無法使用。")
        rows.extend(intervals.values())
    return sorted(rows, key=lambda row: (row["city"], row["start"], row["end"]))


def fetch_forecast(api_key: str) -> dict:
    """Fetch and validate CWA data without exposing the key in URLs/errors."""
    if not isinstance(api_key, str) or not api_key.strip():
        raise WeatherError("請先填入自己的中央氣象署 API 授權碼。")
    api_key = api_key.strip()
    if any(ord(character) < 32 or ord(character) > 126 for character in api_key):
        raise WeatherError("API 授權碼格式不正確，請重新確認。")
    request = Request(CWA_URL, headers={
        "Authorization": api_key,
        "Accept": "application/json",
        "User-Agent": "Taiwan-Weather-Coursework/1.0",
    })
    try:
        with build_opener(_NoRedirect()).open(request, timeout=20) as response:
            body = response.read(MAX_RESPONSE_BYTES + 1)
    except HTTPError as error:
        if error.code in (401, 403):
            raise WeatherError("中央氣象署拒絕授權，請確認 API 授權碼與使用權限。") from None
        if error.code == 429:
            raise WeatherError("中央氣象署要求暫緩請求，請稍後重試。") from None
        raise WeatherError("中央氣象署服務暫時無法提供資料，請稍後重試。") from None
    except (URLError, TimeoutError, OSError, HTTPException):
        raise WeatherError("無法連線中央氣象署，請檢查網路後重試。") from None
    if len(body) > MAX_RESPONSE_BYTES:
        raise WeatherError("氣象回應過大，請稍後重試。")
    try:
        payload = json.loads(body.decode("utf-8-sig"))
    except (UnicodeError, json.JSONDecodeError):
        raise WeatherError("中央氣象署回應不是有效的 JSON 資料。") from None
    parse_forecast(payload)
    return payload


def demo_payload(now=None) -> dict:
    """Generate clearly synthetic, deterministic 22-city / 3-period data.

    Synthetic 12-hour windows start at the current 06:00/18:00 boundary.
    They illustrate the data shape, not observed or predicted weather.
    """
    moment = _datetime(datetime.now(TAIPEI) if now is None else now, allow_naive=True)
    if moment.hour < 6:
        first = (moment - timedelta(days=1)).replace(hour=18, minute=0, second=0)
    else:
        first = moment.replace(hour=6 if moment.hour < 18 else 18, minute=0, second=0)
    weather_options = (("晴時多雲", "2"), ("多雲", "4"), ("多雲短暫雨", "8"))
    locations = []
    for index, city in enumerate(CITIES):
        elements = {name: [] for name in ("Wx", "PoP", "MinT", "MaxT", "CI")}
        for period_index in range(3):
            start = first + timedelta(hours=12 * period_index)
            end = start + timedelta(hours=12)
            description, code = weather_options[(index + period_index) % 3]
            low = 20 + index % 7 + period_index % 2
            values = {
                "Wx": {"parameterName": description, "parameterValue": code},
                "PoP": {"parameterName": str(((index + period_index) % 7) * 10), "parameterUnit": "百分比"},
                "MinT": {"parameterName": str(low), "parameterUnit": "C"},
                "MaxT": {"parameterName": str(low + 4 + index % 3), "parameterUnit": "C"},
                "CI": {"parameterName": "舒適至悶熱"},
            }
            for name, parameter in values.items():
                elements[name].append({
                    "startTime": start.strftime("%Y-%m-%d %H:%M:%S"),
                    "endTime": end.strftime("%Y-%m-%d %H:%M:%S"),
                    "parameter": parameter,
                })
        locations.append({"locationName": city, "weatherElement": [
            {"elementName": name, "time": periods} for name, periods in elements.items()
        ]})
    return {
        "success": "true",
        "result": {"resource_id": "DEMO-F-C0032-001", "fields": []},
        "records": {"datasetDescription": "合成示範資料，非真實天氣預報", "location": locations},
    }


class WeatherStore:
    """Short-lived SQLite connections with atomic, source-isolated snapshots."""

    def __init__(self, db_path):
        self.db_path = str(db_path)
        if self.db_path == ":memory:":
            raise WeatherError("請使用本機 SQLite 檔案路徑以保存歷史資料。")
        try:
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        except OSError:
            raise WeatherError("無法建立本機資料儲存目錄。") from None
        with self._connection() as connection:
            connection.execute("""CREATE TABLE IF NOT EXISTS weather_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL CHECK(source IN ('cwa', 'demo')),
                fetched_at TEXT NOT NULL,
                row_count INTEGER NOT NULL,
                payload_json TEXT NOT NULL
            )""")
            connection.execute("""CREATE TABLE IF NOT EXISTS weather_rows (
                snapshot_id INTEGER NOT NULL REFERENCES weather_snapshots(id) ON DELETE CASCADE,
                city TEXT NOT NULL, start TEXT NOT NULL, end TEXT NOT NULL,
                weather TEXT, weather_code TEXT, min_temp REAL, max_temp REAL,
                rain_probability REAL, comfort TEXT,
                PRIMARY KEY(snapshot_id, city, start, end)
            )""")
            connection.execute("CREATE INDEX IF NOT EXISTS weather_source_id ON weather_snapshots(source, id DESC)")

    @contextmanager
    def _connection(self):
        connection = None
        try:
            connection = sqlite3.connect(self.db_path, timeout=10)
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute("BEGIN")
            with connection:
                yield connection
        except sqlite3.Error:
            raise WeatherError("本機氣象資料庫無法讀寫，請確認檔案權限與可用空間。") from None
        finally:
            if connection is not None:
                connection.close()

    @staticmethod
    def _source(source):
        if source not in ("cwa", "demo"):
            raise WeatherError("資料來源必須是 cwa 或 demo。")
        return source

    def save(self, payload, source="cwa", fetched_at=None) -> int:
        source = self._source(source)
        rows = parse_forecast(payload)
        # Explicit markers prevent accidental synthetic-to-live relabeling.
        resource = payload.get("result", {})
        if source == "cwa" and isinstance(resource, dict):
            if str(resource.get("resource_id", "")).startswith("DEMO-"):
                raise WeatherError("合成示範資料不可儲存為中央氣象署即時資料。")
        timestamp = _datetime(datetime.now(TAIPEI) if fetched_at is None else fetched_at).isoformat()
        try:
            serialized = json.dumps(payload, ensure_ascii=False, allow_nan=False)
        except (TypeError, ValueError):
            raise WeatherError("氣象回應包含無法儲存的 JSON 資料。") from None
        with self._connection() as connection:
            cursor = connection.execute(
                "INSERT INTO weather_snapshots(source, fetched_at, row_count, payload_json) VALUES (?, ?, ?, ?)",
                (source, timestamp, len(rows), serialized),
            )
            snapshot_id = cursor.lastrowid
            connection.executemany(
                "INSERT INTO weather_rows(snapshot_id, city, start, end, weather, weather_code, min_temp, max_temp, rain_probability, comfort) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [(snapshot_id, *(row[column] for column in _COLUMNS)) for row in rows],
            )
            connection.execute(
                "DELETE FROM weather_snapshots WHERE source = ? AND id NOT IN (SELECT id FROM weather_snapshots WHERE source = ? ORDER BY id DESC LIMIT ?)",
                (source, source, MAX_SNAPSHOTS_PER_SOURCE),
            )
        return snapshot_id

    def latest(self, source="cwa") -> dict | None:
        source = self._source(source)
        with self._connection() as connection:
            snapshot = connection.execute(
                "SELECT id, source, fetched_at FROM weather_snapshots WHERE source = ? ORDER BY id DESC LIMIT 1", (source,),
            ).fetchone()
            if snapshot is None:
                return None
            result = dict(snapshot)
            result["rows"] = [dict(row) for row in connection.execute(
                "SELECT city, start, end, weather, weather_code, min_temp, max_temp, rain_probability, comfort FROM weather_rows WHERE snapshot_id = ? ORDER BY city, start, end",
                (snapshot["id"],),
            )]
        return result

    def history(self, limit=10) -> list[dict]:
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
            raise WeatherError("歷史筆數必須是正整數。")
        with self._connection() as connection:
            return [dict(row) for row in connection.execute(
                "SELECT id, source, fetched_at, row_count FROM weather_snapshots ORDER BY id DESC LIMIT ?", (limit,),
            )]
