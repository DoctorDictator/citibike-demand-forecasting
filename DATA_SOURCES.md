# UrbanFlow AI — Data Sources and Exact Folder Names

## 1) Citi Bike historical trip data — primary historical source
Official page: https://citibikenyc.com/system-data
Archive used by the downloader: https://s3.amazonaws.com/tripdata/

### Automatic placement
Run:
```bash
urbanflow download-trips --month 202601
```
The code downloads:
```text
data/raw/trips/202601-citibike-tripdata.zip
```
and extracts CSV file(s) to:
```text
data/raw/trips/202601/
```
Do not rename the CSVs after extraction; the loader reads every `.csv` in that month folder.

### Manual placement
If you download a monthly ZIP yourself, put it under:
```text
data/raw/trips/
```
Recommended name:
```text
YYYYMM-citibike-tripdata.zip
```
You may also extract it to:
```text
data/raw/trips/YYYYMM/
```

Expected modern Citi Bike fields include:
`ride_id, rideable_type, started_at, ended_at, start_station_name, start_station_id, end_station_name, end_station_id, start_lat, start_lng, end_lat, end_lng, member_casual`.
The loader also supports the main older Citi Bike column names.

---

## 2) Citi Bike live GBFS — real-time station source
Official GBFS discovery URL:
https://gbfs.citibikenyc.com/gbfs/2.3/gbfs.json

The project discovers `station_information` and `station_status` dynamically from that root feed.

Run once:
```bash
urbanflow collect-gbfs --once
```
Run continuously every 5 minutes:
```bash
urbanflow collect-gbfs
```
Snapshots are written automatically to:
```text
data/raw/gbfs/YYYY-MM-DD/gbfs_YYYYMMDDTHHMMSSZ.parquet
```
Do not manually create a historical inventory file; this collector builds that archive for us.

---

## 3) NOAA/NCEI weather — historical weather enrichment
NCEI Access Data Service:
https://www.ncei.noaa.gov/access/services/data/v1
Documentation:
https://www.ncei.noaa.gov/access/search/documentation/data-service/

Starter station:
```text
USW00094728 = NY CITY CENTRAL PARK, NY US
```

Run:
```bash
urbanflow download-weather --start 2026-01-01 --end 2026-01-31
```
Output name:
```text
data/raw/weather/noaa_2026-01-01_2026-01-31.csv
```
The starter uses NOAA daily summaries and joins them onto hourly mobility rows by date. A later milestone can swap/add hourly NOAA weather without changing the mobility pipeline.

---

## 4) NYC Open Data permitted events — event enrichment
Historical dataset page:
https://data.cityofnewyork.us/City-Government/NYC-Permitted-Event-Information-Historical/bkfu-528j/data
Socrata CSV endpoint used by code:
https://data.cityofnewyork.us/resource/bkfu-528j.csv

Run:
```bash
urbanflow download-events --start 2026-01-01 --end 2026-01-31
```
Output name:
```text
data/raw/events/nyc_events_2026-01-01_2026-01-31.csv
```

---

# Processed filenames used by the starter

After the monthly Citi Bike CSVs exist:
```bash
urbanflow build-hourly --trips-path data/raw/trips/202601
```
creates:
```text
data/processed/station_hourly.parquet
```

Then, with matching weather and event files:
```bash
urbanflow build-features \
  --hourly data/processed/station_hourly.parquet \
  --weather data/raw/weather/noaa_2026-01-01_2026-01-31.csv \
  --events data/raw/events/nyc_events_2026-01-01_2026-01-31.csv
```
creates:
```text
data/processed/features.parquet
```

Models are saved under:
```text
data/models/
```
