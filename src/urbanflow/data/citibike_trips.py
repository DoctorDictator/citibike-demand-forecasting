from __future__ import annotations

from pathlib import Path
import io
import zipfile
import requests
import pandas as pd

CURRENT_COLUMNS = {
    "ride_id": "ride_id",
    "rideable_type": "rideable_type",
    "started_at": "started_at",
    "ended_at": "ended_at",
    "start_station_name": "start_station_name",
    "start_station_id": "start_station_id",
    "end_station_name": "end_station_name",
    "end_station_id": "end_station_id",
    "start_lat": "start_lat",
    "start_lng": "start_lng",
    "end_lat": "end_lat",
    "end_lng": "end_lng",
    "member_casual": "member_casual",
}

LEGACY_COLUMNS = {
    "starttime": "started_at",
    "stoptime": "ended_at",
    "start station id": "start_station_id",
    "start station name": "start_station_name",
    "start station latitude": "start_lat",
    "start station longitude": "start_lng",
    "end station id": "end_station_id",
    "end station name": "end_station_name",
    "end station latitude": "end_lat",
    "end station longitude": "end_lng",
    "usertype": "member_casual",
    "bikeid": "ride_id",
}

REQUIRED = {
    "started_at", "ended_at", "start_station_id", "end_station_id",
    "start_station_name", "end_station_name", "start_lat", "start_lng",
    "end_lat", "end_lng"
}


def download_month(month: str, destination: Path, url_template: str, timeout: int = 120) -> Path:
    if len(month) != 6 or not month.isdigit():
        raise ValueError("month must be YYYYMM, e.g. 202601")
    destination.mkdir(parents=True, exist_ok=True)
    url = url_template.format(month=month)
    zip_path = destination / f"{month}-citibike-tripdata.zip"
    if not zip_path.exists():
        with requests.get(url, stream=True, timeout=timeout) as r:
            r.raise_for_status()
            with zip_path.open("wb") as f:
                for chunk in r.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)
    extract_dir = destination / month
    extract_dir.mkdir(exist_ok=True)
    with zipfile.ZipFile(zip_path) as zf:
        csv_members = [m for m in zf.namelist() if m.lower().endswith(".csv")]
        if not csv_members:
            raise RuntimeError(f"No CSV files found inside {zip_path.name}")
        for member in csv_members:
            out = extract_dir / Path(member).name
            if not out.exists():
                with zf.open(member) as src, out.open("wb") as dst:
                    dst.write(src.read())
    return extract_dir


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    raw_map = {c: c.strip() for c in df.columns}
    df = df.rename(columns=raw_map)
    lower_lookup = {c.lower(): c for c in df.columns}
    rename: dict[str, str] = {}
    for low, original in lower_lookup.items():
        if low in CURRENT_COLUMNS:
            rename[original] = CURRENT_COLUMNS[low]
        elif low in LEGACY_COLUMNS:
            rename[original] = LEGACY_COLUMNS[low]
    df = df.rename(columns=rename)
    missing = REQUIRED - set(df.columns)
    if missing:
        raise ValueError(f"Unsupported Citi Bike schema. Missing columns: {sorted(missing)}")
    return df


def read_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, low_memory=False)
    df = _normalize_columns(df)
    for c in ["started_at", "ended_at"]:
        df[c] = pd.to_datetime(df[c], errors="coerce")
    for c in ["start_lat", "start_lng", "end_lat", "end_lng"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    for c in ["start_station_id", "end_station_id"]:
        df[c] = df[c].astype("string")
    df = df.dropna(subset=["started_at", "ended_at", "start_station_id", "end_station_id"])
    return df


def iter_trip_frames(path: Path):
    if path.is_file() and path.suffix.lower() == ".csv":
        yield read_csv(path)
        return
    if path.is_file() and path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as zf:
            for member in zf.namelist():
                if member.lower().endswith(".csv"):
                    with zf.open(member) as f:
                        df = pd.read_csv(io.BytesIO(f.read()), low_memory=False)
                    tmp = _normalize_columns(df)
                    tmp["started_at"] = pd.to_datetime(tmp["started_at"], errors="coerce")
                    tmp["ended_at"] = pd.to_datetime(tmp["ended_at"], errors="coerce")
                    yield tmp.dropna(subset=["started_at", "ended_at", "start_station_id", "end_station_id"])
        return
    if path.is_dir():
        files = sorted(path.rglob("*.csv"))
        if not files:
            raise FileNotFoundError(f"No CSV files found under {path}")
        for file in files:
            yield read_csv(file)
        return
    raise FileNotFoundError(path)


def trips_to_station_hourly(path: Path) -> pd.DataFrame:
    pieces: list[pd.DataFrame] = []
    for df in iter_trip_frames(path):
        dep = (
            df.assign(timestamp=df["started_at"].dt.floor("h"))
            .groupby(["timestamp", "start_station_id", "start_station_name"], dropna=False)
            .agg(departures=("start_station_id", "size"),
                 station_lat=("start_lat", "median"), station_lng=("start_lng", "median"))
            .reset_index()
            .rename(columns={"start_station_id": "station_id", "start_station_name": "station_name"})
        )
        arr = (
            df.assign(timestamp=df["ended_at"].dt.floor("h"))
            .groupby(["timestamp", "end_station_id", "end_station_name"], dropna=False)
            .agg(arrivals=("end_station_id", "size"),
                 end_lat=("end_lat", "median"), end_lng=("end_lng", "median"))
            .reset_index()
            .rename(columns={"end_station_id": "station_id", "end_station_name": "station_name"})
        )
        hourly = dep.merge(arr, on=["timestamp", "station_id", "station_name"], how="outer")
        hourly["departures"] = hourly["departures"].fillna(0).astype("int64")
        hourly["arrivals"] = hourly["arrivals"].fillna(0).astype("int64")
        hourly["station_lat"] = hourly["station_lat"].fillna(hourly.pop("end_lat"))
        hourly["station_lng"] = hourly["station_lng"].fillna(hourly.pop("end_lng"))
        hourly["net_flow"] = hourly["arrivals"] - hourly["departures"]
        hourly["total_trips"] = hourly["arrivals"] + hourly["departures"]
        pieces.append(hourly)
    if not pieces:
        raise RuntimeError("No trip rows were produced")
    out = pd.concat(pieces, ignore_index=True)
    out = (
        out.groupby(["timestamp", "station_id", "station_name"], as_index=False)
        .agg(departures=("departures", "sum"), arrivals=("arrivals", "sum"),
             net_flow=("net_flow", "sum"), total_trips=("total_trips", "sum"),
             station_lat=("station_lat", "median"), station_lng=("station_lng", "median"))
        .sort_values(["station_id", "timestamp"])
    )
    return out
