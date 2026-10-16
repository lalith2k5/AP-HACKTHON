"""Tests for spec 14.2 extra endpoints (stores/trends/audit/pipeline/ingest)."""
import os

from fastapi.testclient import TestClient

from storesignal.api import app

API_KEY = os.environ.get("STORESIGNAL_API_KEY", "demo-key-storesignal")
HEADERS = {"x-api-key": API_KEY}
client = TestClient(app)


def _ok(r):
    assert r.status_code == 200, f"{r.status_code}: {r.text[:200]}"
    return r.json()


def test_openapi_contains_all_spec_paths():
    spec = app.openapi()["paths"]
    for p in [
        "/api/v1/stores", "/api/v1/stores/{store_id}", "/api/v1/trends",
        "/api/v1/audit", "/api/v1/pipeline/run", "/api/v1/pipeline/{run_id}",
        "/api/v1/ingest", "/api/v1/ingest/{job_id}",
        "/api/v1/evaluation/run", "/api/v1/evaluation/{run_id}",
        "/api/v1/replay", "/api/v1/briefs/{region_id}", "/api/v1/jobs/{job_id}",
    ]:
        assert p in spec, f"missing spec path: {p}"


def test_stores_list():
    body = _ok(client.get("/api/v1/stores", headers=HEADERS))
    assert isinstance(body["stores"], list) and body["count"] >= 1
    for k in ["store_id", "region_id", "incident_count", "alert_count", "has_denominator"]:
        assert k in body["stores"][0]


def test_stores_detail_roundtrip():
    sid = _ok(client.get("/api/v1/stores", headers=HEADERS))["stores"][0]["store_id"]
    body = _ok(client.get(f"/api/v1/stores/{sid}", headers=HEADERS))
    assert body["store"]["store_id"] == sid
    assert isinstance(body["incidents"], list)


def test_stores_detail_unknown_404():
    assert client.get("/api/v1/stores/NOPE-999", headers=HEADERS).status_code == 404


def test_trends_shape():
    body = _ok(client.get("/api/v1/trends", headers=HEADERS))
    assert isinstance(body["series"], list) and "anomalies" in body


def test_trends_filter_region():
    body = _ok(client.get("/api/v1/trends?region_id=DEL", headers=HEADERS))
    assert body["filters"]["region_id"] == "DEL"


def test_audit_shape():
    body = _ok(client.get("/api/v1/audit", headers=HEADERS))
    assert isinstance(body["events"], list)


def test_replay_get_unknown_404():
    r = client.get("/api/v1/replay/INC-DOES-NOT-EXIST", headers=HEADERS)
    assert r.status_code in (404, 503)


def test_jobs_unknown_404():
    assert client.get("/api/v1/jobs/not-a-job", headers=HEADERS).status_code == 404


def test_pipeline_run_accepts():
    r = client.post("/api/v1/pipeline/run", json={}, headers=HEADERS)
    body = r.json()
    assert r.status_code == 200 and body["status"] == "accepted"
    assert body["run_id"].startswith("pipeline-")
    st = _ok(client.get(f"/api/v1/pipeline/{body['run_id']}", headers=HEADERS))
    assert st["kind"] == "pipeline"


def test_ingest_requires_path_or_rows():
    assert client.post("/api/v1/ingest", json={}, headers=HEADERS).status_code == 422


def test_ingest_accepts_path():
    r = client.post("/api/v1/ingest", json={"path": "data/raw/nonexistent.csv"}, headers=HEADERS)
    assert r.status_code == 200 and r.json()["import_id"].startswith("ingest-")


def test_evaluation_run_accepts():
    r = client.post("/api/v1/evaluation/run", json={}, headers=HEADERS)
    assert r.status_code == 200 and r.json()["status"] == "accepted"
