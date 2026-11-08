from pathlib import Path
import pandas as pd
from urbanflow.data.citibike_trips import read_csv, trips_to_station_hourly


def test_current_citibike_schema(tmp_path: Path):
    p = tmp_path / "rides.csv"
    pd.DataFrame({
        "ride_id": ["r1", "r2"],
        "rideable_type": ["classic_bike", "electric_bike"],
        "started_at": ["2026-01-01 08:05:00", "2026-01-01 08:25:00"],
        "ended_at": ["2026-01-01 08:15:00", "2026-01-01 09:05:00"],
        "start_station_name": ["A", "A"],
        "start_station_id": ["1", "1"],
        "end_station_name": ["B", "B"],
        "end_station_id": ["2", "2"],
        "start_lat": [40.7, 40.7], "start_lng": [-74.0, -74.0],
        "end_lat": [40.71, 40.71], "end_lng": [-73.99, -73.99],
        "member_casual": ["member", "casual"],
    }).to_csv(p, index=False)
    df = read_csv(p)
    assert len(df) == 2
    hourly = trips_to_station_hourly(tmp_path)
    assert hourly["departures"].sum() == 2
    assert hourly["arrivals"].sum() == 2
