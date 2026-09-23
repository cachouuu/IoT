"""Taiwan's next 36 hours: a Streamlit view over CWA forecasts and SQLite history."""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timedelta
from html import escape
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

from weather import WeatherError, WeatherStore, demo_payload, fetch_forecast, parse_forecast


TAIPEI = ZoneInfo("Asia/Taipei")
REFRESH_INTERVAL = timedelta(minutes=30)
DB_PATH = Path(__file__).resolve().parent / "data" / "weather.db"
MODE_LABELS = {"demo": "示範資料", "cwa": "氣象署預報"}
CITY_ORDER = [
    "臺北市", "新北市", "基隆市", "桃園市", "新竹市", "新竹縣", "苗栗縣",
    "臺中市", "彰化縣", "南投縣", "雲林縣", "嘉義市", "嘉義縣", "臺南市",
    "高雄市", "屏東縣", "宜蘭縣", "花蓮縣", "臺東縣", "澎湖縣", "金門縣", "連江縣",
]

STYLES = """
<style>
  .stApp { background: #f5f3ec; font-size: 16px; }
  .block-container { max-width: 1200px; padding-top: 2.2rem; padding-bottom: 2.8rem; }
  [data-testid="stHeader"] { background: rgba(245,243,236,.94); }
  [data-testid="stSidebar"] { border-right: 1px solid #d9dccb; }
  h1, h2, h3 { color: #262b24; letter-spacing: -.035em; }
  h1 { font-family: Georgia, "Noto Serif TC", serif; font-weight: 500 !important; }
  h2 { font-size: 1.45rem !important; }
  [data-testid="stMetricValue"] { font-family: Georgia, serif; }
  [data-testid="stButton"] button { border-radius: 5px; }
  .masthead { display: flex; justify-content: space-between; align-items: center;
    padding-bottom: 18px; border-bottom: 1px solid #aeb5a0; margin-bottom: 24px; }
  .masthead span { font-size: 12px; letter-spacing: .16em; font-weight: 650; }
  .masthead a { font-size: 14px; color: #5b6545; text-decoration: none; }
  .eyebrow { color: #697348; font-size: 12px; letter-spacing: .15em;
    font-weight: 700; margin-bottom: 12px; }
  .intro { font-size: 16px; color: #66705e; margin-top: -9px; margin-bottom: 26px; }
  .hero { background: #e5e9d7; border: 1px solid #cbd2ba; border-radius: 8px;
    padding: 30px 32px; margin: 10px 0 25px; display: flex;
    justify-content: space-between; gap: 18px; align-items: center; }
  .hero h2 { font-size: 31px !important; font-weight: 500; margin: 0 0 8px; padding: 0; }
  .hero .description { color: #576344; font-size: 16px; }
  .hero .temperature { font-family: Georgia, serif; font-size: clamp(34px,4vw,55px);
    color: #34402b; line-height: 1.2; white-space: nowrap; }
  .hero .temperature span { font-family: sans-serif; font-size: 19px; }
  .hero .range-label { text-align: right; color: #66705e; font-size: 12px; margin-top: 7px; }
  .period-card { border-top: 3px solid #86916b; padding: 21px 21px 20px;
    background: #fffef8; border-radius: 0 0 6px 6px; min-height: 246px; }
  .period-card .period-label { font-size: 14px; color: #697348; letter-spacing: .1em; }
  .period-card .period-time { color: #797e71; font-size: 12px; margin: 7px 0 19px; }
  .period-card .weather { font-size: 20px; font-weight: 600; min-height: 32px; }
  .period-card .degrees { font-size: 29px; font-family: Georgia, serif; margin: 8px 0 18px; }
  .period-card .detail { padding-top: 12px; border-top: 1px solid #e6e8dc;
    color: #647050; font-size: 14px; display: flex; justify-content: space-between; gap: 8px; }
  .section-label { color: #788067; letter-spacing: .14em; font-size: 12px; margin-top: 29px; }
  .footer { border-top: 1px solid #ccd1c0; padding-top: 18px; margin-top: 35px;
    color: #78816d; font-size: 12px; letter-spacing: .06em; }
  @media (max-width: 640px) {
    .block-container { padding-top: 1.3rem; }
    .hero { padding: 22px; flex-direction: column; align-items: flex-start; }
    .hero .range-label { text-align: left; }
    .masthead span { font-size: 12px; }
    .period-card { min-height: auto; margin-bottom: 10px; }
  }
</style>
"""


def local_time(value: str | datetime) -> datetime:
    """Treat legacy naive cache timestamps as Taiwan time; always return aware time."""
    parsed = value if isinstance(value, datetime) else datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=TAIPEI)
    return parsed.astimezone(TAIPEI)


def time_text(value: str | datetime) -> str:
    return local_time(value).strftime("%Y/%m/%d %H:%M")


def number(value: object, unit: str = "") -> str:
    return "—" if value is None or pd.isna(value) else f"{float(value):g}{unit}"


def html(value: object) -> str:
    return escape(str(value), quote=True)


def configured_key() -> str:
    """Read secrets without requiring a local secrets.toml on a demo installation."""
    env_key = os.environ.get("CWA_API_KEY", "").strip()
    if env_key:
        return env_key
    try:
        return str(st.secrets.get("CWA_API_KEY", "")).strip()
    except (FileNotFoundError, KeyError, st.errors.StreamlitSecretNotFoundError):
        return ""


def activate_demo() -> None:
    st.session_state["data_mode"] = "demo"


def open_store() -> WeatherStore | None:
    try:
        return WeatherStore(DB_PATH)
    except (OSError, sqlite3.Error, WeatherError):
        st.warning("暫時無法開啟本機歷史紀錄；這次查詢仍可使用，資料只保留於目前工作階段。")
        return None


def load_snapshot(
    source: str, api_key: str, refresh: bool, store: WeatherStore | None, now: datetime
) -> dict | None:
    """Refresh on demand/TTL; never put API keys into a cache or SQLite record."""
    snapshots = st.session_state.setdefault("snapshots", {})
    attempts = st.session_state.setdefault("last_attempt", {})
    snapshot = snapshots.get(source)

    if snapshot is None and store is not None:
        try:
            snapshot = store.latest(source=source)
        except (OSError, sqlite3.Error, WeatherError):
            st.warning("無法讀取本機快取，將嘗試重新取得資料。")
        if snapshot:
            snapshots[source] = snapshot

    if source == "cwa" and not api_key:
        st.info(
            "尚未設定 CWA API 授權碼。展開左側「資料設定」輸入授權碼，"
            "或設定 CWA_API_KEY 後按「更新資料」。也可以先使用示範資料。"
        )
        st.button("先看示範資料", on_click=activate_demo)
        if snapshot:
            st.warning(f"目前顯示先前儲存的氣象署快取，未連線更新。取得時間：{time_text(snapshot['fetched_at'])}（臺灣時間）。")
        return snapshot

    fresh = snapshot is not None and now - local_time(snapshot["fetched_at"]) < REFRESH_INTERVAL
    recently_attempted = source in attempts and now - local_time(attempts[source]) < REFRESH_INTERVAL
    if not refresh and (fresh or recently_attempted):
        return snapshot

    attempts[source] = now.isoformat()
    try:
        with st.spinner("正在取得氣象署預報…" if source == "cwa" else "正在準備示範資料…"):
            payload = fetch_forecast(api_key) if source == "cwa" else demo_payload(now=now)
            rows = parse_forecast(payload)
        snapshot = {"id": None, "source": source, "fetched_at": now.isoformat(), "rows": rows}
        if store is not None:
            try:
                snapshot["id"] = store.save(payload, source=source, fetched_at=now.isoformat())
            except (OSError, sqlite3.Error, WeatherError):
                st.warning("資料已取得，但暫時無法儲存本機歷史紀錄。")
        snapshots[source] = snapshot
        st.session_state.pop(f"fetch_error_{source}", None)
    except (WeatherError, OSError, ValueError):
        # Avoid displaying raw network exceptions, which can contain request credentials.
        st.session_state[f"fetch_error_{source}"] = True
    return snapshot


def period_label(row: dict, now: datetime) -> str:
    start = local_time(row["start"])
    end = local_time(row["end"])
    if end <= now:
        return "已結束時段"
    day = (start.date() - now.date()).days
    day_label = {0: "今天", 1: "明天", 2: "後天"}.get(day, start.strftime("%m/%d"))
    if day < 0 and end > now:
        day_label = "目前時段"
    return f"{day_label} · {'白天' if 6 <= start.hour < 18 else '夜間'}"


def period_card(row: dict, now: datetime) -> None:
    start, end = local_time(row["start"]), local_time(row["end"])
    temperature = f"{number(row.get('min_temp'))}–{number(row.get('max_temp'))}°"
    st.markdown(
        f'<div class="period-card"><div class="period-label">{html(period_label(row, now))}</div>'
        f'<div class="period-time">{html(start.strftime("%m/%d %H:%M"))} — {html(end.strftime("%m/%d %H:%M"))}</div>'
        f'<div class="weather">{html(row.get("weather") or "天氣資料未提供")}</div>'
        f'<div class="degrees">{html(temperature)} <small>C</small></div>'
        f'<div class="detail"><span>降雨機率 {html(number(row.get("rain_probability"), "%"))}</span>'
        f'<span>{html(row.get("comfort") or "舒適度未提供")}</span></div></div>',
        unsafe_allow_html=True,
    )


def render_forecast(snapshot: dict, city: str, now: datetime) -> None:
    city_rows = sorted((row for row in snapshot["rows"] if row["city"] == city), key=lambda r: r["start"])
    upcoming = [row for row in city_rows if local_time(row["end"]) > now]
    if not city_rows:
        st.warning("這份資料沒有此縣市的預報，請選擇其他縣市或更新資料。")
        return
    if not upcoming:
        st.warning("這份資料的預報時段均已結束，目前沒有有效的現在或未來預報。以下僅顯示歷史資料，請更新。")

    current = upcoming[0] if upcoming else city_rows[-1]
    display_rows = city_rows[:3]
    subtitle = "最近的預報時段" if upcoming else "最近一筆歷史時段 · 已過期"
    if snapshot["source"] == "demo":
        subtitle = "合成資料示範 · 非目前天氣"
    st.markdown(
        f'<div class="hero"><div><div class="eyebrow">{html(subtitle)}</div>'
        f'<h2>{html(city)}，{html(current.get("weather") or "天氣資料未提供")}</h2>'
        f'<div class="description">降雨機率 {html(number(current.get("rain_probability"), "%"))}'
        f' &nbsp; · &nbsp; {html(current.get("comfort") or "舒適度未提供")}</div></div>'
        f'<div><div class="temperature">{html(number(current.get("min_temp")))}–{html(number(current.get("max_temp")))}<span> °C</span></div>'
        '<div class="range-label">該預報時段的最低至最高溫度</div></div></div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="eyebrow">01 / FORECAST WINDOW</div>', unsafe_allow_html=True)
    st.subheader("未來 36 小時" if upcoming else "歷史預報時段")
    st.caption("每張卡片是一個預報區間；溫度為該區間的最低／最高溫，並非即時觀測值。")
    for column, row in zip(st.columns(len(display_rows)), display_rows):
        with column:
            period_card(row, now)

    st.markdown('<div class="section-label">02 / THE NEXT THREE PERIODS</div>', unsafe_allow_html=True)
    st.subheader("溫度與降雨機率")
    chart_data = pd.DataFrame([
        {
            "時段開始（臺灣時間）": local_time(row["start"]).strftime("%m/%d %H:%M"),
            "最低溫": row.get("min_temp"), "最高溫": row.get("max_temp"),
            "降雨機率": row.get("rain_probability"),
        }
        for row in display_rows
    ])
    temperature_chart, rain_chart = st.columns([1.35, 1])
    with temperature_chart:
        st.caption("溫度範圍 · °C")
        st.line_chart(
            chart_data, x="時段開始（臺灣時間）", y=["最低溫", "最高溫"],
            color=["#a8af87", "#56643a"], y_label="溫度（°C）", height=250,
        )
    with rain_chart:
        st.caption("各時段降雨機率 · %")
        st.bar_chart(
            chart_data, x="時段開始（臺灣時間）", y="降雨機率", color="#83936b",
            y_label="降雨機率（%）", height=250,
        )


def render_all_cities(rows: list[dict], now: datetime) -> None:
    st.markdown('<div class="section-label">03 / AROUND THE ISLAND</div>', unsafe_allow_html=True)
    st.subheader("縣市比較")
    periods = sorted({row["start"] for row in rows})
    first_upcoming = next((i for i, start in enumerate(periods) if any(
        r["start"] == start and local_time(r["end"]) > now for r in rows
    )), 0)
    period = st.selectbox("比較的預報時段（臺灣時間）", periods, index=first_upcoming, format_func=time_text)
    table = pd.DataFrame([
        {
            "縣市": row["city"], "天氣": row.get("weather"),
            "最低溫（°C）": row.get("min_temp"), "最高溫（°C）": row.get("max_temp"),
            "降雨機率（%）": row.get("rain_probability"), "舒適度": row.get("comfort"),
            "開始時間": time_text(row["start"]), "結束時間": time_text(row["end"]),
        }
        for row in rows if row["start"] == period
    ])
    st.caption("點選欄位名稱即可排序，快速比較各地溫度與降雨機率。缺值以空白顯示。")
    st.dataframe(
        table, hide_index=True, width="stretch", height=430,
        column_config={
            "最低溫（°C）": st.column_config.NumberColumn(format="%.0f °C"),
            "最高溫（°C）": st.column_config.NumberColumn(format="%.0f °C"),
            "降雨機率（%）": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%d%%"),
        },
    )


def render_metadata(snapshot: dict, store: WeatherStore | None) -> None:
    with st.expander("資料來源、取得時間與歷史紀錄"):
        if snapshot["source"] == "demo":
            st.write("來源：程式產生的合成示範資料；不代表實際或目前天氣。")
        else:
            st.write("來源：交通部中央氣象署開放資料，F-C0032-001 一般天氣預報（今明 36 小時）。")
            st.link_button("開啟氣象署資料說明", "https://opendata.cwa.gov.tw/dataset/forecast/F-C0032-001")
        st.write(f"本次資料取得時間：{time_text(snapshot['fetched_at'])}（臺灣時間 UTC+8）")
        st.caption("取得時間是本程式下載／產生資料的時間，不是氣象署發布時間。重新操作頁面時，超過 30 分鐘才再次取得；也可手動更新。")
        st.caption("歷史紀錄儲存在執行程式的本機 SQLite 資料庫。API 授權碼不會寫入資料庫。")
        if store is not None:
            try:
                history = store.history(limit=10)
                if history:
                    st.dataframe(pd.DataFrame([
                        {"紀錄": item["id"], "來源": MODE_LABELS.get(item["source"], item["source"]),
                         "取得時間（臺灣時間）": time_text(item["fetched_at"]), "預報筆數": item["row_count"]}
                        for item in history
                    ]), hide_index=True, width="stretch")
                else:
                    st.caption("尚無已儲存的歷史紀錄。")
            except (OSError, sqlite3.Error, WeatherError):
                st.caption("暫時無法讀取歷史紀錄。")


def main() -> None:
    st.set_page_config(page_title="台灣天氣預報 · IoT HW1", page_icon="🌤", layout="wide", initial_sidebar_state="collapsed")
    st.markdown(STYLES, unsafe_allow_html=True)
    now = datetime.now(TAIPEI)
    key_from_config = configured_key()
    with st.sidebar:
        st.subheader("資料設定")
        if key_from_config:
            st.success("已從安全設定讀取 CWA 授權碼。")
            api_key = key_from_config
        else:
            api_key = st.text_input("CWA API 授權碼", type="password", help="授權碼僅用於目前工作階段的資料請求，不會寫入資料庫。", key="local_api_key").strip()
            st.caption("輸入後切換至「氣象署預報」，再按「更新資料」。")
        st.link_button("取得免費氣象資料授權碼", "https://opendata.cwa.gov.tw/user/authkey")
        st.caption("也支援環境變數 CWA_API_KEY 或 .streamlit/secrets.toml 的同名設定。")
        st.divider()
        st.write("IoT · Homework 01")
        st.caption("Python × Streamlit × CWA Open Data × SQLite")
        st.link_button("回到 Sam Wei 的個人首頁", "https://cachouuu.github.io/IoT/")

    st.markdown(
        '<div class="masthead"><span>SAM WEI / HW1</span>'
        '<a href="https://cachouuu.github.io/IoT/" target="_blank" rel="noopener noreferrer">↗ 個人首頁</a></div>'
        '<div class="eyebrow">TAIWAN WEATHER FORECAST · 01</div>', unsafe_allow_html=True,
    )
    st.title("台灣天氣預報")
    st.markdown('<p class="intro">查詢 22 個縣市今明 36 小時的天氣、溫度與降雨機率。</p>', unsafe_allow_html=True)

    city_column, mode_column, refresh_column = st.columns([1.1, 1.5, .65], vertical_alignment="bottom")
    with city_column:
        city = st.selectbox("選擇縣市", CITY_ORDER, key="selected_city")
    with mode_column:
        source = st.radio("資料模式", ["demo", "cwa"], format_func=MODE_LABELS.get, horizontal=True, key="data_mode")
    with refresh_column:
        refresh = st.button("更新資料", type="primary", width="stretch")

    if source == "demo":
        st.info("示範模式 · 所有數值均為合成資料，僅供操作展示，不代表目前天氣。")

    store = open_store()
    snapshot = load_snapshot(source, api_key, refresh, store, now)
    if st.session_state.get(f"fetch_error_{source}"):
        st.error("資料更新失敗。請檢查網路與 CWA 授權碼，再按「更新資料」重試。")
        if snapshot:
            st.warning(f"目前顯示先前取得的{MODE_LABELS[source]}快取，並非這次更新結果。原始取得時間：{time_text(snapshot['fetched_at'])}（臺灣時間）。")
    if snapshot and snapshot.get("rows"):
        st.caption(f"{MODE_LABELS[source]} · 取得於 {time_text(snapshot['fetched_at'])} · 臺灣時間 UTC+8")
        render_forecast(snapshot, city, now)
        render_all_cities(snapshot["rows"], now)
        render_metadata(snapshot, store)
    elif source == "cwa":
        st.warning("尚無可顯示的氣象署預報。完成授權碼設定並更新，或切換至示範資料體驗介面。")

    st.markdown('<div class="footer">SAM WEI / IOT HOMEWORK 01 &nbsp; · &nbsp; TAIWAN WEATHER FORECAST</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
