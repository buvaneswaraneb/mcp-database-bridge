import os
import shutil
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Default directory for databases
DEFAULT_DB_DIR = Path(__file__).resolve().parents[1] / "sample_data"
DB_DIR = os.environ.get("DB_DIR", str(DEFAULT_DB_DIR))

# Ensure sample_data directory exists
os.makedirs(DB_DIR, exist_ok=True)

app = FastAPI(title="MCP Database Manager")

# CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class DatabaseResponse(BaseModel):
    name: str
    size: int

@app.get("/api/databases", response_model=list[DatabaseResponse])
def list_databases():
    """List all SQLite databases in the DB_DIR."""
    databases = []
    if os.path.isdir(DB_DIR):
        for f in os.listdir(DB_DIR):
            if f.endswith(".db") or f.endswith(".sqlite"):
                filepath = os.path.join(DB_DIR, f)
                size = os.path.getsize(filepath)
                databases.append(DatabaseResponse(name=f, size=size))
    return databases

@app.post("/api/databases/upload")
async def upload_database(file: UploadFile = File(...)):
    """Upload a new SQLite database."""
    if not (file.filename.endswith(".db") or file.filename.endswith(".sqlite")):
        raise HTTPException(status_code=400, detail="Only .db and .sqlite files are allowed.")
    
    file_path = os.path.join(DB_DIR, file.filename)
    
    # Check if exists
    if os.path.exists(file_path):
        raise HTTPException(status_code=409, detail=f"Database '{file.filename}' already exists.")

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return {"message": f"Successfully uploaded {file.filename}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/databases/{name}")
def delete_database(name: str):
    """Delete an existing SQLite database."""
    if not (name.endswith(".db") or name.endswith(".sqlite")):
        raise HTTPException(status_code=400, detail="Invalid filename.")
        
    file_path = os.path.join(DB_DIR, name)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Database not found.")
        
    try:
        os.remove(file_path)
        return {"message": f"Successfully deleted {name}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Serve static files for the frontend (fallback)
web_dir = Path(__file__).resolve().parents[1] / "web"
os.makedirs(web_dir, exist_ok=True)

# Mount the static directory
app.mount("/", StaticFiles(directory=str(web_dir), html=True), name="web")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.web:app", host="0.0.0.0", port=8000, reload=True)
