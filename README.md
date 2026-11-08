# UrbanFlow AI — Initial Codebase

Starter repository for a spatio-temporal predictive analytics project on NYC Citi Bike mobility.

## What works in this initial version

- Official Citi Bike monthly trip downloader and schema normalization.
- Trip-to-station-hour aggregation (departures, arrivals, net flow, total trips).
- Live Citi Bike GBFS discovery, station information/status merge, and timestamped snapshot archiving.
- NOAA/NCEI Central Park daily weather downloader.
- NYC Open Data permitted-event downloader with date filtering and pagination.
- Calendar, cyclic-time, lag, and rolling features.
- Initial statistical model modules for Logistic Regression, LDA, QDA, Poisson, Negative Binomial, Holt-Winters, and SARIMA.
- A baseline boosted count model using a chronological split.
- Initial Streamlit dashboard for latest station status and historical trip totals.
- Unit tests for Citi Bike schema handling and feature generation.

## 1. Setup

```bash
python -m venv .venv
```

Windows PowerShell:
```powershell
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:
```bash
source .venv/bin/activate
```

Install:
```bash
pip install -e ".[dev]"
```

Run tests:
```bash
pytest -q
```

## 2. Verify live Citi Bike feed immediately

```bash
urbanflow collect-gbfs --once
```

Expected output location:
```text
data/raw/gbfs/YYYY-MM-DD/gbfs_YYYYMMDDTHHMMSSZ.parquet
```

For continuous collection every five minutes:
```bash
urbanflow collect-gbfs
```

## 3. Download one historical month first

Start small while developing:
```bash
urbanflow download-trips --month 202601
```

Then build station-hour data:
```bash
urbanflow build-hourly --trips-path data/raw/trips/202601
```

## 4. Weather and events for the same dates

```bash
urbanflow download-weather --start 2026-01-01 --end 2026-01-31
urbanflow download-events --start 2026-01-01 --end 2026-01-31
```

Build features:
```bash
urbanflow build-features \
  --hourly data/processed/station_hourly.parquet \
  --weather data/raw/weather/noaa_2026-01-01_2026-01-31.csv \
  --events data/raw/events/nyc_events_2026-01-01_2026-01-31.csv
```

Train the initial chronological demand baseline:
```bash
urbanflow train-baseline
```

## 5. Dashboard

```bash
streamlit run app/streamlit_app.py
```

## Folder contract

```text
data/
├── raw/
│   ├── trips/      # Citi Bike monthly ZIPs / extracted CSVs
│   ├── gbfs/       # our timestamped live station snapshots
│   ├── weather/    # NOAA CSVs
│   └── events/     # NYC Open Data event CSVs
├── interim/
├── processed/      # station_hourly.parquet, features.parquet
└── models/         # trained model artifacts + metrics
```

See `DATA_SOURCES.md` for exact official source URLs, commands, filenames, and placement rules.
