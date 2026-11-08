from __future__ import annotations

from pathlib import Path
import requests
import pandas as pd


def download_events(endpoint: str, start_date: str, end_date: str, destination: Path, page_size: int = 50000) -> Path:
    """Download NYC permitted events for the requested period using Socrata CSV."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    offset = 0
    chunks: list[bytes] = []
    where = f"start_date_time >= '{start_date}T00:00:00' AND start_date_time < '{end_date}T23:59:59'"
    while True:
        params = {
            "$where": where,
            "$limit": page_size,
            "$offset": offset,
            "$order": "start_date_time",
        }
        r = requests.get(endpoint, params=params, timeout=120, headers={"User-Agent": "UrbanFlowAI/0.1"})
        r.raise_for_status()
        text = r.text
        lines = text.splitlines()
        if len(lines) <= 1:
            break
        if offset == 0:
            chunks.append(r.content.rstrip() + b"\n")
        else:
            body = "\n".join(lines[1:]).encode("utf-8")
            chunks.append(body.rstrip() + b"\n")
        rows = len(lines) - 1
        if rows < page_size:
            break
        offset += page_size
    destination.write_bytes(b"".join(chunks))
    return destination


def load_events(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, low_memory=False)
    for c in ["start_date_time", "end_date_time"]:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce")
    return df


def events_by_date(path: Path) -> pd.DataFrame:
    df = load_events(path)
    if "start_date_time" not in df.columns:
        raise ValueError("Events CSV must contain start_date_time")
    df["date"] = df["start_date_time"].dt.date
    daily = df.groupby("date").agg(
        event_count=("event_id", "nunique") if "event_id" in df.columns else ("start_date_time", "size"),
        event_types=("event_type", lambda s: s.nunique(dropna=True)) if "event_type" in df.columns else ("start_date_time", "size"),
    ).reset_index()
    daily["event_today"] = (daily["event_count"] > 0).astype(int)
    return daily
