"""
API tests for the datasets module.
Tests file upload, preview, and validation.
"""
import io
import pytest
import pandas as pd


def test_upload_csv_success(client, auth_headers, sample_csv_bytes):
    """
    Valid CSV upload returns 201 with dataset info,
    cleaning report, and suggestions.
    """
    response = client.post(
        "/api/v1/datasets/upload",
        headers=auth_headers,
        files={"file": ("test_sales.csv", io.BytesIO(sample_csv_bytes), "text/csv")},
    )
    assert response.status_code == 201
    data = response.json()

    # Dataset info
    assert "dataset" in data
    assert data["dataset"]["row_count"] == 5
    assert data["dataset"]["col_count"] == 5
    assert data["dataset"]["file_type"] == "csv"

    # Cleaning report
    assert "cleaning_report" in data
    assert data["cleaning_report"]["total_issues"] > 0  # sample_csv has issues

    # Suggestions (may be empty if LLM mocked)
    assert "suggestions" in data


def test_upload_invalid_extension(client, auth_headers):
    """Uploading a .txt file should return 400."""
    response = client.post(
        "/api/v1/datasets/upload",
        headers=auth_headers,
        files={
            "file": ("data.txt", io.BytesIO(b"hello world"), "text/plain")
        },
    )
    assert response.status_code == 400
    assert response.json()["error_code"] == "INVALID_FILE"


def test_upload_without_auth(client, sample_csv_bytes):
    """Upload without auth token should return 403."""
    response = client.post(
        "/api/v1/datasets/upload",
        files={"file": ("test.csv", io.BytesIO(sample_csv_bytes), "text/csv")},
    )
    assert response.status_code in [401, 403]


def test_list_datasets_empty(client, auth_headers):
    """Fresh user has empty datasets list."""
    # Use a different user to avoid interference
    reg = client.post("/api/v1/auth/register", json={
        "email": "fresh@test.com",
        "full_name": "Fresh User",
        "password": "password123",
    })
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/v1/datasets/", headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_preview_after_upload(client, auth_headers, sample_csv_bytes):
    """Uploaded dataset can be previewed."""
    # Upload first
    upload_response = client.post(
        "/api/v1/datasets/upload",
        headers=auth_headers,
        files={"file": ("test.csv", io.BytesIO(sample_csv_bytes), "text/csv")},
    )
    dataset_id = upload_response.json()["dataset"]["id"]

    # Preview
    response = client.get(
        f"/api/v1/datasets/{dataset_id}/preview",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "columns" in data
    assert "rows" in data
    assert data["total_rows"] == 5
    assert len(data["rows"]) == 5  # all 5 rows (< 50 limit)


def test_get_preview_wrong_user(client, sample_csv_bytes):
    """Cannot preview another user's dataset."""
    # User A uploads
    reg_a = client.post("/api/v1/auth/register", json={
        "email": "usera@test.com", "full_name": "A", "password": "pass123"
    })
    headers_a = {"Authorization": f"Bearer {reg_a.json()['access_token']}"}
    upload = client.post(
        "/api/v1/datasets/upload",
        headers=headers_a,
        files={"file": ("test.csv", io.BytesIO(sample_csv_bytes), "text/csv")},
    )
    dataset_id = upload.json()["dataset"]["id"]

    # User B tries to access
    reg_b = client.post("/api/v1/auth/register", json={
        "email": "userb@test.com", "full_name": "B", "password": "pass123"
    })
    headers_b = {"Authorization": f"Bearer {reg_b.json()['access_token']}"}
    response = client.get(f"/api/v1/datasets/{dataset_id}/preview", headers=headers_b)
    assert response.status_code == 404


def test_delete_dataset(client, auth_headers, sample_csv_bytes):
    """Uploaded dataset can be deleted."""
    upload = client.post(
        "/api/v1/datasets/upload",
        headers=auth_headers,
        files={"file": ("del_test.csv", io.BytesIO(sample_csv_bytes), "text/csv")},
    )
    dataset_id = upload.json()["dataset"]["id"]

    delete_response = client.delete(
        f"/api/v1/datasets/{dataset_id}",
        headers=auth_headers,
    )
    assert delete_response.status_code == 204

    # Verify it's gone
    get_response = client.get(
        f"/api/v1/datasets/{dataset_id}",
        headers=auth_headers,
    )
    assert get_response.status_code == 404