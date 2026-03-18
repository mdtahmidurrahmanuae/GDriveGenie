"""Async PocketBase REST client (admin-token based)."""

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_PB_URL: str = ""          # set by init_pb() at startup
_admin_token: str = ""     # refreshed automatically on 401


async def init_pb() -> None:
    """Fetch admin token from PocketBase. Call once at app startup."""
    global _PB_URL, _admin_token
    _PB_URL = os.environ["PB_URL"].rstrip("/")
    email = os.environ["PB_ADMIN_EMAIL"]
    password = os.environ["PB_ADMIN_PASSWORD"]
    _admin_token = await _fetch_admin_token(email, password)
    logger.info("PocketBase admin authenticated at %s", _PB_URL)


async def _fetch_admin_token(email: str, password: str) -> str:
    endpoints = [
        f"{_PB_URL}/api/collections/_superusers/auth-with-password",
        f"{_PB_URL}/api/admins/auth-with-password",
    ]
    async with httpx.AsyncClient(timeout=30.0) as c:
        for ep in endpoints:
            try:
                r = await c.post(ep, json={"identity": email, "password": password})
                if r.status_code == 200:
                    token = r.json().get("token", "")
                    if token:
                        return token
            except Exception:
                continue
    raise RuntimeError(
        "Could not authenticate with PocketBase. "
        "Check PB_ADMIN_EMAIL and PB_ADMIN_PASSWORD env vars."
    )


class PBClient:
    """One async PocketBase client per request (FastAPI dependency)."""

    def __init__(self) -> None:
        self._client = httpx.AsyncClient(timeout=30.0)

    def _headers(self) -> dict:
        return {"Authorization": _admin_token}

    async def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        global _admin_token
        r = await self._client.request(
            method, f"{_PB_URL}{path}", headers=self._headers(), **kwargs
        )
        if r.status_code == 401:
            # Token expired — refresh and retry once
            email = os.environ["PB_ADMIN_EMAIL"]
            password = os.environ["PB_ADMIN_PASSWORD"]
            _admin_token = await _fetch_admin_token(email, password)
            r = await self._client.request(
                method, f"{_PB_URL}{path}", headers=self._headers(), **kwargs
            )
        return r

    # ------------------------------------------------------------------
    # Record CRUD
    # ------------------------------------------------------------------

    async def list_records(
        self,
        collection: str,
        filter: str = "",
        sort: str = "",
        page: int = 1,
        per_page: int = 500,
        expand: str = "",
    ) -> list[dict]:
        params: dict[str, Any] = {"page": page, "perPage": per_page}
        if filter:
            params["filter"] = filter
        if sort:
            params["sort"] = sort
        if expand:
            params["expand"] = expand
        r = await self._request("GET", f"/api/collections/{collection}/records", params=params)
        r.raise_for_status()
        return r.json().get("items", [])

    async def get_record(self, collection: str, id: str) -> dict:
        r = await self._request("GET", f"/api/collections/{collection}/records/{id}")
        r.raise_for_status()
        return r.json()

    async def create_record(self, collection: str, data: dict) -> dict:
        r = await self._request(
            "POST", f"/api/collections/{collection}/records", json=data
        )
        if r.status_code not in (200, 204):
            raise _pb_error(r)
        return r.json()

    async def update_record(self, collection: str, id: str, data: dict) -> dict:
        r = await self._request(
            "PATCH", f"/api/collections/{collection}/records/{id}", json=data
        )
        if r.status_code not in (200, 204):
            raise _pb_error(r)
        return r.json()

    async def delete_record(self, collection: str, id: str) -> None:
        r = await self._request(
            "DELETE", f"/api/collections/{collection}/records/{id}"
        )
        if r.status_code not in (200, 204):
            raise _pb_error(r)

    async def count_records(self, collection: str, filter: str = "") -> int:
        """Return total record count matching filter."""
        params: dict[str, Any] = {"page": 1, "perPage": 1}
        if filter:
            params["filter"] = filter
        r = await self._request("GET", f"/api/collections/{collection}/records", params=params)
        r.raise_for_status()
        return r.json().get("totalItems", 0)

    # ------------------------------------------------------------------
    # Auth helpers
    # ------------------------------------------------------------------

    async def auth_user(self, email: str, password: str) -> dict:
        """Authenticate a gdrive_users user. Returns {token, record}."""
        r = await self._client.post(
            f"{_PB_URL}/api/collections/gdrive_users/auth-with-password",
            json={"identity": email, "password": password},
        )
        if r.status_code != 200:
            raise _pb_error(r)
        return r.json()

    # ------------------------------------------------------------------

    async def aclose(self) -> None:
        await self._client.aclose()


def _pb_error(r: httpx.Response) -> Exception:
    try:
        msg = r.json().get("message", r.text)
    except Exception:
        msg = r.text
    return RuntimeError(f"PocketBase error {r.status_code}: {msg}")


async def get_pb():
    """FastAPI dependency — yields one PBClient per request."""
    client = PBClient()
    try:
        yield client
    finally:
        await client.aclose()
