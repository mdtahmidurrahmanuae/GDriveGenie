import os
from typing import Any

import httpx

_CF_ACCOUNT_ID = os.environ["CF_ACCOUNT_ID"]
_CF_D1_DATABASE_ID = os.environ["CF_D1_DATABASE_ID"]
_CF_API_TOKEN = os.environ["CF_API_TOKEN"]

_BASE = (
    f"https://api.cloudflare.com/client/v4/accounts/{_CF_ACCOUNT_ID}"
    f"/d1/database/{_CF_D1_DATABASE_ID}/query"
)
_HEADERS = {
    "Authorization": f"Bearer {_CF_API_TOKEN}",
    "Content-Type": "application/json",
}


class D1Client:
    """Thin async wrapper around the Cloudflare D1 HTTP REST API."""

    def __init__(self) -> None:
        self._client = httpx.AsyncClient(timeout=30.0)

    async def execute(self, sql: str, params: list[Any] | None = None) -> list[dict]:
        """Execute a single SQL statement. Returns list of result rows as dicts."""
        payload: dict[str, Any] = {"sql": sql}
        if params:
            payload["params"] = params
        resp = await self._client.post(_BASE, headers=_HEADERS, json=payload)
        resp.raise_for_status()
        data = resp.json()
        if not data.get("success"):
            raise RuntimeError(f"D1 query failed: {data.get('errors')}")
        results = data["result"]
        if not results or not results[0].get("success"):
            inner_errors = results[0].get("errors", []) if results else []
            raise RuntimeError(f"D1 statement failed: {inner_errors}")
        return results[0].get("results", [])

    async def execute_many(self, statements: list[dict]) -> None:
        """Send a batch of {sql, params} dicts in one HTTP round-trip."""
        resp = await self._client.post(_BASE, headers=_HEADERS, json=statements)
        resp.raise_for_status()
        data = resp.json()
        if not data.get("success"):
            raise RuntimeError(f"D1 batch failed: {data.get('errors')}")

    async def aclose(self) -> None:
        await self._client.aclose()


async def get_d1():
    """FastAPI dependency — one fresh D1Client per request."""
    client = D1Client()
    try:
        yield client
    finally:
        await client.aclose()
