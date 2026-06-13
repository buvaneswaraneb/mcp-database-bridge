import io
import sqlite3

from fastapi.testclient import TestClient

from client.api.app import app


client = TestClient(app)
SESSION_HEADERS = {"X-Session-ID": "test-session-one"}


def sqlite_bytes(tmp_path):
    path = tmp_path / "upload.db"
    connection = sqlite3.connect(path)
    connection.execute("CREATE TABLE demo (id INTEGER PRIMARY KEY, name TEXT)")
    connection.execute("INSERT INTO demo (name) VALUES ('bridge')")
    connection.commit()
    connection.close()
    return path.read_bytes()


def test_health_and_models():
    health = client.get("/api/health")
    models = client.get("/api/models")

    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    assert models.status_code == 200
    assert models.json()["provider"] == "Groq"
    assert models.json()["models"]


def test_sample_database_is_available():
    response = client.get("/api/databases", headers=SESSION_HEADERS)

    assert response.status_code == 200
    assert any(database["name"] == "sample.db" for database in response.json())


def test_upload_and_delete_database(tmp_path):
    upload = client.post(
        "/api/databases/upload",
        headers=SESSION_HEADERS,
        files={"file": ("hosted-test.db", io.BytesIO(sqlite_bytes(tmp_path)), "application/octet-stream")},
    )

    assert upload.status_code == 201
    assert upload.json()["name"] == "hosted-test.db"

    metadata = client.get("/api/databases/hosted-test.db/metadata", headers=SESSION_HEADERS)
    assert metadata.status_code == 200
    assert metadata.json()["tables"][0]["table_name"] == "demo"

    deletion = client.delete("/api/databases/hosted-test.db", headers=SESSION_HEADERS)
    assert deletion.status_code == 200


def test_rejects_invalid_database_upload():
    response = client.post(
        "/api/databases/upload",
        headers=SESSION_HEADERS,
        files={"file": ("invalid.db", io.BytesIO(b"not sqlite"), "application/octet-stream")},
    )

    assert response.status_code == 400


def test_uploads_are_isolated_by_anonymous_session(tmp_path):
    upload = client.post(
        "/api/databases/upload",
        headers={"X-Session-ID": "isolated-session-one"},
        files={"file": ("private.db", io.BytesIO(sqlite_bytes(tmp_path)), "application/octet-stream")},
    )
    other_session = client.get("/api/databases", headers={"X-Session-ID": "isolated-session-two"})

    assert upload.status_code == 201
    assert "private.db" not in [database["name"] for database in other_session.json()]

    client.delete("/api/databases/private.db", headers={"X-Session-ID": "isolated-session-one"})


def test_chat_requires_configured_groq_key(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    response = client.post("/api/chat", headers=SESSION_HEADERS, json={
        "model": "llama-3.3-70b-versatile",
        "database": "sample.db",
        "messages": [{"role": "user", "content": "What tables exist?"}],
    })

    assert response.status_code == 503
    assert "GROQ_API_KEY" in response.json()["detail"]
