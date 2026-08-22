"""End-to-end: upload sample file with no patient ID -> prompt for manual
association -> create new patient -> analysis completes -> dashboard data
returned -> PDF generates without error. (spec section 11)"""
import time
from pathlib import Path

FIXTURE = Path(__file__).parent / "fixtures" / "session_20260813_111730.csv"


def _wait_for_completion(client, headers, session_id, timeout_s=30):
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        resp = client.get(f"/sessions/{session_id}/status", headers=headers)
        assert resp.status_code == 200
        status = resp.json()["status"]
        if status in ("complete", "failed"):
            return status
        time.sleep(0.2)
    raise TimeoutError("Session processing did not complete in time")


def test_legacy_upload_then_associate_then_full_pipeline(client, auth_headers):
    with open(FIXTURE, "rb") as f:
        resp = client.post(
            "/sessions/upload",
            headers=auth_headers,
            files={"files": (FIXTURE.name, f, "text/csv")},
            data={"test_type": "10m walk"},
        )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["needs_association"] is True
    assert body["legacy_no_metadata"] is True
    session_id = body["session_id"]

    resp = client.post(
        f"/sessions/{session_id}/associate",
        headers=auth_headers,
        json={"new_patient": {"full_name": "E2E Test Patient", "study_id": "STU-E2E-1"}},
    )
    assert resp.status_code == 200, resp.text

    final_status = _wait_for_completion(client, auth_headers, session_id)
    assert final_status == "complete"

    resp = client.get(f"/sessions/{session_id}/analysis", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    analysis = resp.json()
    assert analysis["metrics"]["cadence_spm"]["status"] == "measured"
    assert analysis["metrics"]["speed_mps"]["status"] == "estimated"

    resp = client.get(f"/sessions/{session_id}/quality", headers=auth_headers)
    assert resp.status_code == 200
    assert 0 <= resp.json()["quality_score"] <= 100

    resp = client.post(f"/sessions/{session_id}/report", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    report_path = resp.json()["report_file_path"]
    assert Path(report_path).exists()
    assert Path(report_path).stat().st_size > 0
