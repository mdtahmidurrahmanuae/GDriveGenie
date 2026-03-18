from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import config
from routes import auth, accounts, files, admin, folders, shares
from routes import profile as profile_router
from services.pb_client import init_pb
from services.drive_service import sync_files_from_drives
from services.pb_client import PBClient


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Authenticate with PocketBase admin
    await init_pb()

    # Best-effort startup sync across all users
    try:
        bg_pb = PBClient()
        try:
            await sync_files_from_drives(bg_pb)
        finally:
            await bg_pb.aclose()
    except Exception as e:
        print(f"WARNING: Startup sync failed: {e}")

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
app.include_router(folders.router, prefix="/api")
app.include_router(shares.router, prefix="/api")
app.include_router(profile_router.router, prefix="/api")
app.include_router(admin.router, prefix="/api")


@app.get("/")
def root():
    return {"name": "GDriveGenie API", "status": "active"}


@app.get("/active")
def active():
    return {"status": "active"}
