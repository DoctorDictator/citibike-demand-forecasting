from __future__ import annotations

import argparse
from pathlib import Path
import pandas as pd

from urbanflow.config import load_config, data_path
from urbanflow.data.citibike_trips import download_month
from urbanflow.data.gbfs import collect
from urbanflow.data.noaa import download_daily_weather
from urbanflow.data.nyc_events import download_events
from urbanflow.pipeline.build_hourly import run as build_hourly
from urbanflow.features.build import build_feature_table
from urbanflow.pipeline.train_baselines import run as train_baseline


def main() -> None:
    cfg = load_config()
    parser = argparse.ArgumentParser(prog="urbanflow")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("download-trips")
    p.add_argument("--month", required=True, help="YYYYMM")

    p = sub.add_parser("collect-gbfs")
    p.add_argument("--once", action="store_true")
    p.add_argument("--interval", type=int, default=cfg["citibike"]["gbfs_interval_seconds"])

    p = sub.add_parser("download-weather")
    p.add_argument("--start", required=True, help="YYYY-MM-DD")
    p.add_argument("--end", required=True, help="YYYY-MM-DD")

    p = sub.add_parser("download-events")
    p.add_argument("--start", required=True, help="YYYY-MM-DD")
    p.add_argument("--end", required=True, help="YYYY-MM-DD")

    p = sub.add_parser("build-hourly")
    p.add_argument("--trips-path", required=True)
    p.add_argument("--output", default="data/processed/station_hourly.parquet")

    p = sub.add_parser("build-features")
    p.add_argument("--hourly", default="data/processed/station_hourly.parquet")
    p.add_argument("--weather", default=None)
    p.add_argument("--events", default=None)
    p.add_argument("--output", default="data/processed/features.parquet")

    p = sub.add_parser("train-baseline")
    p.add_argument("--features", default="data/processed/features.parquet")

    args = parser.parse_args()
    root = Path(cfg["_project_root"])

    if args.cmd == "download-trips":
        path = download_month(args.month, root / "data/raw/trips", cfg["citibike"]["trip_url_template"])
        print(path)
    elif args.cmd == "collect-gbfs":
        collect(cfg["citibike"]["gbfs_root"], root / "data/raw/gbfs", args.interval, args.once)
    elif args.cmd == "download-weather":
        out = root / "data/raw/weather" / f"noaa_{args.start}_{args.end}.csv"
        print(download_daily_weather(cfg["weather"]["noaa_service"], cfg["weather"]["station_id"], args.start, args.end, out))
    elif args.cmd == "download-events":
        out = root / "data/raw/events" / f"nyc_events_{args.start}_{args.end}.csv"
        print(download_events(cfg["nyc_events"]["endpoint"], args.start, args.end, out))
    elif args.cmd == "build-hourly":
        build_hourly((root / args.trips_path).resolve(), (root / args.output).resolve())
    elif args.cmd == "build-features":
        hourly = pd.read_parquet((root / args.hourly).resolve())
        weather = (root / args.weather).resolve() if args.weather else None
        events = (root / args.events).resolve() if args.events else None
        df = build_feature_table(hourly, weather, events, cfg["features"]["lags"], cfg["features"]["rolling_windows"])
        out = (root / args.output).resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(out, index=False)
        print(f"built {len(df):,} feature rows -> {out}")
    elif args.cmd == "train-baseline":
        metrics = train_baseline((root / args.features).resolve(), root / "data/models", cfg["models"]["test_fraction"])
        print(metrics)


if __name__ == "__main__":
    main()
