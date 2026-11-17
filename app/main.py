"""FastAPI 应用入口：根路径、静态页面、健康检查与账目接口。"""

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import BASE_DIR
from app.db import check_database
from app.routers import records

STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="expense-tracker")
app.include_router(records.router)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health():
    database = check_database()
    return {
        "status": "ok" if database == "ok" else "degraded",
        "service": "expense-tracker",
        "database": database,
    }