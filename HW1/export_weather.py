"""Export a validated, SQLite-backed weather snapshot for GitHub Pages."""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import sys
import tempfile

from weather import WeatherError, WeatherStore, demo_payload, fetch_forecast, parse_forecast


DATASET = "F-C0032-001"
TAIPEI = timezone(timedelta(hours=8))


def atomic_write_json(output: Path, snapshot: dict) -> None:
    """Keep the last good file intact until the complete replacement is ready."""
    # Serialize before touching the destination, rejecting non-JSON float values.
    content = json.dumps(snapshot, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=output.parent,
            prefix=f".{output.name}.", suffix=".tmp", delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            temporary.write(content)
            temporary.flush()
            os.fsync(temporary.fileno())
        # Pages artifacts must be readable by the hosting service.
        temporary_path.chmod(0o644)
        os.replace(temporary_path, output)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def export_snapshot(*, output: Path, db: Path, demo: bool = False) -> dict:
    """Fetch, validate, store, then publish; never fall back to synthetic data."""
    source = "demo" if demo else "cwa"
    if demo:
        payload = demo_payload()
    else:
        api_key = os.environ.get("CWA_API_KEY", "").strip()
        if not api_key:
            raise WeatherError("CWA_API_KEY is not configured.")
        payload = fetch_forecast(api_key)

    # Reject malformed payloads before creating database or output files.
    parse_forecast(payload)
    fetched_at = datetime.now(TAIPEI).isoformat(timespec="seconds")
    store = WeatherStore(db)
    store.save(payload, source=source, fetched_at=fetched_at)
    latest = store.latest(source)
    if not latest or not latest["rows"]:
        raise WeatherError("No saved weather rows are available.")
    snapshot = {
        "dataset": DATASET,
        "source": source,
        "fetched_at": latest["fetched_at"],
        "rows": latest["rows"],
        "history": store.history(limit=10),
    }
    atomic_write_json(Path(output), snapshot)
    return snapshot


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--demo", action="store_true",
        help="Export explicitly labeled synthetic data; this is not real weather.",
    )
    parser.add_argument("--output", type=Path, default=Path("docs/data/forecast.json"))
    parser.add_argument("--db", type=Path, default=Path("data/weather.db"))
    args = parser.parse_args(argv)
    if not args.demo and not os.environ.get("CWA_API_KEY", "").strip():
        print("未設定 CWA_API_KEY，未更新公開快照。示範資料請明確使用 --demo。", file=sys.stderr)
        return 1
    try:
        snapshot = export_snapshot(output=args.output, db=args.db, demo=args.demo)
    except Exception:
        # Never echo upstream exceptions: an HTTP error may contain credentials.
        print("匯出失敗；既有公開快照未變更。請檢查 API 設定、網路與檔案權限。", file=sys.stderr)
        return 1
    label = "合成示範資料（非真實天氣）" if args.demo else "中央氣象署預報"
    print(f"已匯出{label}，共 {len(snapshot['rows'])} 筆預報。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
