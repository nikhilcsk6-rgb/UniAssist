import io
import json
import os
from tests.conftest import app_client, auth, fake_llm, upload_sample  # noqa: F401

CSV = os.path.join(os.path.dirname(__file__), "..", "..", "sample_data", "benchmark", "sample_benchmark.csv")


def upload_bench(c, email="a@x.com", name="demo"):
    return c.post("/api/research/benchmark", headers=auth(c, email), content_type="multipart/form-data",
                  data={"dataset_name": name, "file": (io.BytesIO(open(CSV, "rb").read()), "b.csv")})


def test_benchmark_upload_admin_only(app_client):
    assert upload_bench(app_client, "s@x.com").status_code == 403
    r = upload_bench(app_client)
    assert r.status_code == 201 and r.json["rows"] == 14


def test_bad_csv_rejected(app_client):
    r = app_client.post("/api/research/benchmark", headers=auth(app_client, "a@x.com"), content_type="multipart/form-data",
                        data={"dataset_name": "x", "file": (io.BytesIO(b"foo,bar\n1,2\n"), "b.csv")})
    assert r.status_code == 400


def test_experiment_computes_metrics_from_real_pipeline(app_client, fake_llm):
    for f in ("admissions_and_fees.txt", "examination_policy.txt"):
        upload_sample(app_client, "a@x.com", f)
    upload_bench(app_client)

    def reply(system, prompt):
        if "impartial evaluator" in system:                     # judge call
            return json.dumps({"accuracy": 1, "relevance": 1, "hallucination": False}) if "60,000" in prompt \
                else json.dumps({"accuracy": 0, "relevance": 0.5, "hallucination": True})
        return "The MCA tuition fee is Rs. 60,000 per year [1]." if "SOURCES" in prompt else "I think it is 90,000."
    fake_llm.reply = reply
    h = auth(app_client, "a@x.com")
    r = app_client.post("/api/research/experiments", json={"name": "t", "dataset_name": "demo", "limit": 4}, headers=h)
    assert r.status_code == 201
    s = r.json["summary"]
    assert s["A_no_rag"]["n"] == 4 and s["B_rag"]["n"] == 4
    assert s["A_no_rag"]["hallucination_rate"] > s["B_rag"]["hallucination_rate"] or s["B_rag"]["abstention_rate"] > 0
    assert s["B_rag"]["retrieval_precision"] is not None and s["A_no_rag"]["retrieval_precision"] is None
    assert r.json["experiment"]["is_sample"] is False
    eid = r.json["experiment"]["id"]
    d = app_client.get(f"/api/research/experiments/{eid}", headers=h).json
    assert len(d["rows"]) == 8 and d["satisfaction"]["count"] == 0
    csv_r = app_client.get(f"/api/research/experiments/{eid}/export.csv", headers=h)
    assert csv_r.status_code == 200 and b"variant" in csv_r.data
    pdf_r = app_client.get(f"/api/research/experiments/{eid}/export.pdf", headers=h)
    assert pdf_r.data.startswith(b"%PDF")


def test_experiment_requires_admin_and_dataset(app_client):
    assert app_client.post("/api/research/experiments", json={"dataset_name": "demo"},
                           headers=auth(app_client, "f@x.com")).status_code == 403
    assert app_client.post("/api/research/experiments", json={"dataset_name": "nope"},
                           headers=auth(app_client, "a@x.com")).status_code == 404
