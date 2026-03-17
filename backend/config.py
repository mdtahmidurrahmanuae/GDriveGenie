import os

CONFIG_DIR: str = os.getenv("CONFIG_DIR", os.path.join(os.path.dirname(os.path.dirname(__file__)), "config"))
FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
BACKEND_URL: str = os.getenv("BACKEND_URL", "http://localhost:8000")
JWT_ALGORITHM: str = "HS256"
JWT_EXPIRE_HOURS: int = 24

# Populated by load_config() during lifespan startup — empty until then
DASHBOARD_PIN_HASH: str = ""
JWT_SECRET: str = ""
ENCRYPTION_KEY: str = ""


async def load_config(d1) -> None:
    """
    Fetch secrets from D1 app_config table and populate this module's globals.
    Must be called in the FastAPI lifespan before any request is handled.
    """
    import config as _cfg

    async def _fetch(key: str) -> str:
        rows = await d1.execute("SELECT value FROM app_config WHERE key = ?", [key])
        if not rows:
            raise RuntimeError(
                f"Config key '{key}' missing from D1 app_config table. "
                "Run: python backend/scripts/generate_secrets.py"
            )
        return rows[0]["value"]

    _cfg.DASHBOARD_PIN_HASH = await _fetch("dashboard_pin_hash")
    _cfg.JWT_SECRET = await _fetch("jwt_secret")
    _cfg.ENCRYPTION_KEY = await _fetch("encryption_key")
