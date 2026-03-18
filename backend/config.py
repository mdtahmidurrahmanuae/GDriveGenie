import os

CONFIG_DIR: str = os.getenv("CONFIG_DIR", os.path.join(os.path.dirname(os.path.dirname(__file__)), "config"))
FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
BACKEND_URL: str = os.getenv("BACKEND_URL", "http://localhost:8000")

# PocketBase
PB_URL: str = os.getenv("PB_URL", "https://data.genericxinus.com")

# JWT — loaded from env var (set in .env or docker-compose)
JWT_ALGORITHM: str = "HS256"
JWT_EXPIRE_HOURS: int = 24 * 7  # 7 days

JWT_SECRET: str = os.environ.get("JWT_SECRET", "")
ENCRYPTION_KEY: str = os.environ.get("ENCRYPTION_KEY", "")
