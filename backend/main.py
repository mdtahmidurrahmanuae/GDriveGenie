from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import config
from config import load_config
from database import CREATE_TABLES_SQL, MIGRATION_SQL
from routes import auth, accounts, files
from routes import profile as profile_router
from services.d1_client import D1Client
from services.drive_service import sync_files_from_drives


@asynccontextmanager
async def lifespan(app: FastAPI):
    d1 = D1Client()
    try:
        # Create tables (idempotent)
        for sql in CREATE_TABLES_SQL:
            await d1.execute(sql)

        # Run migrations — ignore errors if column already exists
        for sql in MIGRATION_SQL:
            try:
                await d1.execute(sql)
            except Exception:
                pass

        # Load secrets from D1 into config module globals
        await load_config(d1)

        # Initial file sync (best-effort)
        try:
            await sync_files_from_drives(d1)
        except Exception:
            pass
    finally:
        await d1.aclose()

    yield


app = FastAPI(title="GDriveGenie API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[config.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(accounts.router, prefix="/api")
app.include_router(files.router, prefix="/api")
app.include_router(profile_router.router, prefix="/api")


@app.get("/active")
def active():
    return {"status": "active"}
