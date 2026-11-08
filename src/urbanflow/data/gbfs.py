from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import time
import requests
import pandas as pd


def _get_json(url: str, timeout: int = 30) -> dict:
    r = requests.get(url, timeout=timeout, headers={"User-Agent": "UrbanFlowAI/0.1"})
    r.raise_for_status()
    return r.json()


def discover_feeds(root_url: str, language: str = "en") -> dict[str, str]:
    payload = _get_json(root_url)
    data = payload.get("data", {})
    if "feeds" in data:
        feeds = data["feeds"]
    elif language in data and "feeds" in data[language]:
        feeds = data[language]["feeds"]
    else:
        first = next((v for v in data.values() if isinstance(v, dict) and "feeds" in v), None)
        if not first:
            raise ValueError("Unable to locate GBFS feed list")
        feeds = first["feeds"]
    return {item["name"]: item["url"] for item in feeds}


def _extract_records(payload: dict, key: str) -> list[dict]:
    data = payload.get("data", {})
    if key in data:
        return data[key]
    for value in data.values():
        if isinstance(value, dict) and key in value:
            return value[key]
    raise ValueError(f"GBFS response missing data.{key}")


def fetch_snapshot(root_url: str) -> pd.DataFrame:
    feeds = discover_feeds(root_url)
    missing = {"station_information", "station_status"} - set(feeds)
    if missing:
        raise ValueError(f"GBFS feed missing required endpoints: {sorted(missing)}")
    info_payload = _get_json(feeds["station_information"])
    status_payload = _get_json(feeds["station_status"])
    info = pd.DataFrame(_extract_records(info_payload, "stations"))
    status = pd.DataFrame(_extract_records(status_payload, "stations"))
    info["station_id"] = info["station_id"].astype("string")
    status["station_id"] = status["station_id"].astype("string")
    df = info.merge(status, on="station_id", how="inner", suffixes=("_info", "_status"))
    if "num_vehicles_available" not in df.columns and "num_bikes_available" in df.columns:
        df["num_vehicles_available"] = df["num_bikes_available"]
    if "num_docks_available" not in df.columns:
        df["num_docks_available"] = pd.NA
    if "capacity" in df.columns and "num_vehicles_available" in df.columns:
        cap = pd.to_numeric(df["capacity"], errors="coerce").replace(0, pd.NA)
        bikes = pd.to_numeric(df["num_vehicles_available"], errors="coerce")
        df["occupancy_ratio"] = bikes / cap
    df["collected_at_utc"] = datetime.now(timezone.utc)
    return df


def save_snapshot(df: pd.DataFrame, root: Path) -> Path:
    ts = pd.Timestamp(df["collected_at_utc"].iloc[0]).tz_convert("UTC")
    folder = root / ts.strftime("%Y-%m-%d")
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"gbfs_{ts.strftime('%Y%m%dT%H%M%SZ')}.parquet"
    df.to_parquet(path, index=False)
    return path


def collect(root_url: str, destination: Path, interval_seconds: int = 300, once: bool = False) -> None:
    while True:
        df = fetch_snapshot(root_url)
        path = save_snapshot(df, destination)
        print(f"saved {len(df):,} stations -> {path}")
        if once:
            return
        time.sleep(interval_seconds)
