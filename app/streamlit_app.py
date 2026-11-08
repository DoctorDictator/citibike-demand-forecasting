from __future__ import annotations

from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
GBFS_DIR = ROOT / "data" / "raw" / "gbfs"
HOURLY = ROOT / "data" / "processed" / "station_hourly.parquet"

st.set_page_config(page_title="UrbanFlow AI", layout="wide")
st.title("UrbanFlow AI — Initial Mobility Dashboard")

snapshot_files = sorted(GBFS_DIR.rglob("*.parquet"))
if snapshot_files:
    latest = pd.read_parquet(snapshot_files[-1])
    c1, c2, c3 = st.columns(3)
    c1.metric("Stations in latest snapshot", f"{len(latest):,}")
    if "num_vehicles_available" in latest:
        c2.metric("Bikes/vehicles available", f"{pd.to_numeric(latest['num_vehicles_available'], errors='coerce').sum():,.0f}")
    if "num_docks_available" in latest:
        c3.metric("Docks available", f"{pd.to_numeric(latest['num_docks_available'], errors='coerce').sum():,.0f}")
    if {"lat", "lon", "occupancy_ratio"}.issubset(latest.columns):
        map_df = latest.dropna(subset=["lat", "lon", "occupancy_ratio"]).copy()
        fig = px.scatter_mapbox(map_df, lat="lat", lon="lon", color="occupancy_ratio", hover_name="name" if "name" in map_df.columns else None,
                                zoom=10, height=600, mapbox_style="open-street-map")
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No live snapshots yet. Run: urbanflow collect-gbfs --once")

if HOURLY.exists():
    hourly = pd.read_parquet(HOURLY)
    city = hourly.groupby("timestamp", as_index=False)[["departures", "arrivals"]].sum()
    st.subheader("Historical city-wide trips")
    st.line_chart(city.set_index("timestamp"))
else:
    st.info("No historical hourly table yet. Download a month and run build-hourly.")
