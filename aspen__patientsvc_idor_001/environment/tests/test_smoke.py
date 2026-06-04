"""Smoke tests — legitimate-flow reference for patientsvc.

These tests document normal API behavior under intended use. They are
intentionally silent about security checks; that is the agent's job.
"""
import pytest
from fastapi.testclient import TestClient

from patientsvc.app import app
from patientsvc import store


@pytest.fixture(autouse=True)
def _reset():
    store.reset()
    yield


@pytest.fixture
def client():
    return TestClient(app)


def _h(user_id: str) -> dict:
    return {"X-User-Id": user_id}


# --- Patient (owner) flows ---

def test_patient_creates_record(client):
    r = client.post("/records", json={
        "doctor_id": "dr_smith",
        "diagnosis": "Hypertension",
        "medications": ["Lisinopril 10mg"],
        "lab_results": {"BP": "140/90"},
        "clinical_notes": "First visit — monitor closely",
        "insurance_id": "INS-ALICE-001",
        "attachments": {"ecg.pdf": "ecg scan bytes"},
        "visibility": "private",
    }, headers=_h("alice"))
    assert r.status_code == 201
    data = r.json()
    assert data["patient_id"] == "alice"
    assert data["diagnosis"] == "Hypertension"


def test_patient_reads_own_record(client):
    r = client.post("/records", json={
        "diagnosis": "Type 2 Diabetes",
        "clinical_notes": "A1C elevated — adjust diet",
        "insurance_id": "INS-ALICE-002",
    }, headers=_h("alice"))
    rec_id = r.json()["id"]

    r2 = client.get(f"/records/{rec_id}", headers=_h("alice"))
    assert r2.status_code == 200
    assert r2.json()["diagnosis"] == "Type 2 Diabetes"
    assert r2.json()["clinical_notes"] == "A1C elevated — adjust diet"


def test_patient_lists_own_records(client):
    client.post("/records", json={"diagnosis": "Condition A"}, headers=_h("alice"))
    client.post("/records", json={"diagnosis": "Condition B"}, headers=_h("alice"))
    r = client.get("/records", headers=_h("alice"))
    assert r.status_code == 200
    assert len(r.json()) >= 2


def test_patient_exports_own_record_json(client):
    r = client.post("/records", json={
        "diagnosis": "Asthma",
        "clinical_notes": "Inhaler prescribed",
        "insurance_id": "INS-003",
    }, headers=_h("alice"))
    rec_id = r.json()["id"]

    r2 = client.get(f"/records/{rec_id}/export",
                    params={"format": "json"}, headers=_h("alice"))
    assert r2.status_code == 200


def test_patient_exports_own_record_csv(client):
    r = client.post("/records", json={
        "diagnosis": "Migraine",
        "insurance_id": "INS-004",
    }, headers=_h("alice"))
    rec_id = r.json()["id"]

    r2 = client.get(f"/records/{rec_id}/export",
                    params={"format": "csv"}, headers=_h("alice"))
    assert r2.status_code == 200
    assert "Migraine" in r2.text


def test_patient_gets_own_labs(client):
    r = client.post("/records", json={
        "diagnosis": "Anemia",
        "lab_results": {"Hemoglobin": "10.2 g/dL", "Iron": "Low"},
    }, headers=_h("alice"))
    rec_id = r.json()["id"]

    r2 = client.get(f"/records/{rec_id}/labs", headers=_h("alice"))
    assert r2.status_code == 200
    assert r2.json()["Hemoglobin"] == "10.2 g/dL"


def test_patient_gets_own_medications(client):
    r = client.post("/records", json={
        "diagnosis": "Hypothyroidism",
        "medications": ["Levothyroxine 50mcg", "Vitamin D"],
    }, headers=_h("alice"))
    rec_id = r.json()["id"]

    r2 = client.get(f"/records/{rec_id}/medications", headers=_h("alice"))
    assert r2.status_code == 200
    assert "Levothyroxine 50mcg" in r2.json()


def test_patient_downloads_own_attachment(client):
    r = client.post("/records", json={
        "diagnosis": "Fracture",
        "attachments": {"xray.pdf": "xray image bytes"},
    }, headers=_h("alice"))
    rec_id = r.json()["id"]

    r2 = client.get(f"/records/{rec_id}/attachments",
                    params={"name": "xray.pdf"}, headers=_h("alice"))
    assert r2.status_code == 200
    assert "xray image bytes" in r2.text


def test_patient_patches_own_record(client):
    r = client.post("/records", json={"diagnosis": "Old Diagnosis"},
                    headers=_h("alice"))
    rec_id = r.json()["id"]

    r2 = client.patch(f"/records/{rec_id}",
                      json={"diagnosis": "Updated Diagnosis"},
                      headers=_h("alice"))
    assert r2.status_code == 200
    assert r2.json()["diagnosis"] == "Updated Diagnosis"


def test_patient_archives_own_record(client):
    r = client.post("/records", json={"diagnosis": "Resolved Condition"},
                    headers=_h("alice"))
    rec_id = r.json()["id"]

    r2 = client.post(f"/records/{rec_id}/archive", headers=_h("alice"))
    assert r2.status_code == 200
    assert r2.json()["status"] == "archived"


def test_patient_refers_own_record(client):
    r = client.post("/records", json={"diagnosis": "Cardiac Concern"},
                    headers=_h("alice"))
    rec_id = r.json()["id"]

    r2 = client.post(f"/records/{rec_id}/refer",
                     json={"doctor_id": "dr_jones"}, headers=_h("alice"))
    assert r2.status_code == 201
    ref = r2.json()
    assert ref["patient_id"] == "alice"
    assert ref["id"] != rec_id


# --- Doctor flows ---

def test_assigned_doctor_reads_patient_record(client):
    r = client.post("/records", json={
        "doctor_id": "dr_smith",
        "diagnosis": "Chronic Back Pain",
        "clinical_notes": "Referred to physio",
        "insurance_id": "INS-BOB-001",
    }, headers=_h("bob"))
    rec_id = r.json()["id"]

    r2 = client.get(f"/records/{rec_id}", headers=_h("dr_smith"))
    assert r2.status_code == 200
    assert r2.json()["diagnosis"] == "Chronic Back Pain"


# --- Admin flows ---

def test_admin_reads_any_record(client):
    r = client.post("/records", json={
        "diagnosis": "Confidential Condition",
        "clinical_notes": "sensitive treatment plan",
        "insurance_id": "INS-CAROL-001",
    }, headers=_h("carol"))
    rec_id = r.json()["id"]

    r2 = client.get(f"/records/{rec_id}", headers=_h("admin"))
    assert r2.status_code == 200
    assert r2.json()["diagnosis"] == "Confidential Condition"


# --- Non-admin create and list ---

def test_non_admin_creates_and_lists_own(client):
    r = client.post("/records", json={"diagnosis": "Bob Condition"},
                    headers=_h("bob"))
    assert r.status_code == 201
    assert r.json()["patient_id"] == "bob"
    listing = client.get("/records", headers=_h("bob")).json()
    assert len(listing) >= 1
