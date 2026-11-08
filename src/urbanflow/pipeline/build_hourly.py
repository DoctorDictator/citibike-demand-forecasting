from __future__ import annotations

from pathlib import Path
from urbanflow.data.citibike_trips import trips_to_station_hourly


def run(trips_path: Path, output_path: Path) -> Path:
    df = trips_to_station_hourly(trips_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)
    print(f"built {len(df):,} station-hour rows -> {output_path}")
    return output_path
