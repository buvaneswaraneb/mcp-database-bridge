import os
import re
import shutil
import sqlite3
import tempfile
import threading
from contextlib import contextmanager
from pathlib import Path

from fastapi import FastAPI, File, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from client.api.chat_service import run_chat
from client.api.groq_provider import GroqProvider, ProviderError
from mcp.src import server as mcp_server


ROOT_DIR = Path(__file__).resolve().parents[2]
SAMPLE_DB = ROOT_DIR / "mcp" / "sample_data" / "sample.db"
FRONTEND_DIR = ROOT_DIR / "client" / "frontend"
MAX_UPLOAD_BYTES = int(os.environ.get("MAX_UPLOAD_BYTES", 10 * 1024 * 1024))
HOSTED_DB_DIR = Path(os.environ.get("HOSTED_DB_DIR", Path(tempfile.gettempdir()) / "db-bridge-databases"))
MODEL_IDS = [
    item.strip()
    for item in os.environ.get(
        "GROQ_MODELS",
        "llama-3.3-70b-versatile,llama-3.1-8b-instant,openai/gpt-oss-120b",
    ).split(",")
    if item.strip()
]

HOSTED_DB_DIR.mkdir(parents=True, exist_ok=True)
MCP_DIRECTORY_LOCK = threading.RLock()
mcp_server.init_sample_db()

app = FastAPI(title="DB/BRIDGE Hosted Client", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in os.environ.get("ALLOWED_ORIGINS", "*").split(",")
        if origin.strip()
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Message(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    content: str = Field(min_length=1, max_length=20000)


class ChatRequest(BaseModel):
    model: str
    database: str | None = None
    messages: list[Message] = Field(min_length=1, max_length=40)


def safe_database_name(name: str) -> str:
    clean = Path(name).name
    if clean != name or "/" in name or "\\" in name or not clean.lower().endswith((".db", ".sqlite")):
        raise HTTPException(status_code=400, detail="Invalid SQLite database name.")
    return clean


def safe_session_id(session_id: str | None) -> str:
    if not session_id:
        raise HTTPException(status_code=400, detail="X-Session-ID is required for database access.")
    if not re.fullmatch(r"[A-Za-z0-9_-]{8,80}", session_id):
        raise HTTPException(status_code=400, detail="Invalid anonymous session identifier.")
    return session_id


def session_directory(session_id: str | None) -> Path:
    directory = HOSTED_DB_DIR / safe_session_id(session_id)
    directory.mkdir(parents=True, exist_ok=True)
    sample = directory / "sample.db"
    if SAMPLE_DB.exists() and not sample.exists():
        shutil.copy2(SAMPLE_DB, sample)
    return directory


@contextmanager
def use_mcp_directory(directory: Path):
    with MCP_DIRECTORY_LOCK:
        previous = mcp_server.DB_DIR
        mcp_server.DB_DIR = str(directory)
        try:
            yield
        finally:
            mcp_server.DB_DIR = previous


def database_payload(directory: Path, name: str) -> dict:
    path = directory / name
    return {
        "name": name,
        "size": path.stat().st_size,
        "sample": name == "sample.db",
        "temporary": True,
    }


@app.get("/api/health")
def health():
    return {"status": "ok", "groq_configured": bool(os.environ.get("GROQ_API_KEY"))}


@app.get("/api/models")
def models():
    return {"provider": "Groq", "models": [{"id": model, "label": model} for model in MODEL_IDS]}


@app.get("/api/databases")
def databases(x_session_id: str | None = Header(default=None)):
    directory = session_directory(x_session_id)
    with use_mcp_directory(directory):
        names = mcp_server.list_databases().get("databases", [])
    return [database_payload(directory, name) for name in names]


@app.get("/api/databases/{name}/metadata")
def database_metadata(name: str, x_session_id: str | None = Header(default=None)):
    directory = session_directory(x_session_id)
    with use_mcp_directory(directory):
        return mcp_server.get_database_metadata(safe_database_name(name))


@app.post("/api/databases/upload", status_code=201)
async def upload_database(file: UploadFile = File(...), x_session_id: str | None = Header(default=None)):
    name = safe_database_name(file.filename or "")
    directory = session_directory(x_session_id)
    destination = directory / name
    if destination.exists():
        raise HTTPException(status_code=409, detail=f"Database '{name}' already exists.")

    content = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"Database exceeds the {MAX_UPLOAD_BYTES // (1024 * 1024)} MB limit.")
    destination.write_bytes(content)

    try:
        connection = sqlite3.connect(f"file:{destination}?mode=ro", uri=True)
        result = connection.execute("PRAGMA integrity_check").fetchone()
        connection.close()
        if not result or result[0] != "ok":
            raise ValueError("SQLite integrity check failed.")
    except Exception as exc:
        destination.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="The uploaded file is not a valid SQLite database.") from exc

    return database_payload(directory, name)


@app.delete("/api/databases/{name}")
def delete_database(name: str, x_session_id: str | None = Header(default=None)):
    name = safe_database_name(name)
    if name == "sample.db":
        raise HTTPException(status_code=403, detail="The bundled sample database cannot be deleted.")
    path = session_directory(x_session_id) / name
    if not path.exists():
        raise HTTPException(status_code=404, detail="Database not found.")
    path.unlink()
    return {"message": f"Deleted {name}"}


@app.post("/api/chat")
def chat(request: ChatRequest, x_session_id: str | None = Header(default=None)):
    directory = session_directory(x_session_id)
    if request.model not in MODEL_IDS:
        raise HTTPException(status_code=400, detail="Unsupported model.")
    if request.database:
        database = safe_database_name(request.database)
        if not (directory / database).exists():
            raise HTTPException(status_code=404, detail="Selected database not found.")
    else:
        database = None

    try:
        with use_mcp_directory(directory):
            answer, activity = run_chat(
                GroqProvider(),
                request.model,
                [message.model_dump() for message in request.messages],
                database,
            )
    except ProviderError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return {"answer": answer, "activity": activity, "model": request.model, "database": database}


app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
