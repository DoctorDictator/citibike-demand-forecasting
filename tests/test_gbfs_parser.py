import urbanflow.data.gbfs as gbfs


def test_discovery_and_snapshot(monkeypatch):
    root = {
        "data": {"en": {"feeds": [
            {"name": "station_information", "url": "info"},
            {"name": "station_status", "url": "status"},
        ]}}
    }
    info = {"data": {"stations": [{"station_id": "1", "name": "A", "lat": 40.7, "lon": -74.0, "capacity": 20}]}}
    status = {"data": {"stations": [{"station_id": "1", "num_vehicles_available": 5, "num_docks_available": 15}]}}

    def fake_get(url, timeout=30):
        return {"root": root, "info": info, "status": status}[url]

    monkeypatch.setattr(gbfs, "_get_json", fake_get)
    feeds = gbfs.discover_feeds("root")
    assert feeds["station_status"] == "status"
    snap = gbfs.fetch_snapshot("root")
    assert len(snap) == 1
    assert float(snap.loc[0, "occupancy_ratio"]) == 0.25
