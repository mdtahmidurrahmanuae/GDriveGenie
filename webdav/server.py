"""
GDriveGenie WebDAV Server
=========================
Exposes a user's virtual folders + files via WebDAV.

Mount on Windows:  Map Network Drive → https://yourserver/webdav/
Mount on macOS:    Finder → Go → Connect to Server → https://yourserver/webdav/

Authentication: HTTP Basic Auth (GDriveGenie email + password).
Files stream directly from Google Drive — nothing is stored locally.

Environment variables:
  PB_URL               PocketBase URL (e.g. https://data.genericxinus.com)
  PB_ADMIN_EMAIL       PocketBase system admin email
  PB_ADMIN_PASSWORD    PocketBase system admin password
  ENCRYPTION_KEY       Fernet key (same as backend)
  WEBDAV_PORT          Port to listen on (default: 8080)
  CREDENTIALS_PATH     Path to Google credentials.json
"""

import io
import json
import logging
import os
import time

import httpx
from cheroot import wsgi
from cryptography.fernet import Fernet
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build as gbuild
from googleapiclient.http import MediaIoBaseDownload
from wsgidav import util
from wsgidav.dav_error import DAVError, HTTP_FORBIDDEN, HTTP_NOT_FOUND, HTTP_UNAUTHORIZED
from wsgidav.dav_provider import DAVCollection, DAVNonCollection, DAVProvider
from wsgidav.wsgidav_app import WsgiDAVApp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PB_URL = os.environ["PB_URL"].rstrip("/")
PB_ADMIN_EMAIL = os.environ["PB_ADMIN_EMAIL"]
PB_ADMIN_PASSWORD = os.environ["PB_ADMIN_PASSWORD"]
ENCRYPTION_KEY = os.environ["ENCRYPTION_KEY"]
CREDENTIALS_PATH = os.environ.get("CREDENTIALS_PATH", "/app/config/credentials.json")
WEBDAV_PORT = int(os.environ.get("WEBDAV_PORT", "8080"))
SCOPES = ["https://www.googleapis.com/auth/drive"]

_admin_token = ""
_fernet = Fernet(ENCRYPTION_KEY.encode())


# ---------------------------------------------------------------------------
# PocketBase helpers (synchronous — wsgidav is WSGI/sync)
# ---------------------------------------------------------------------------

def _pb_admin_auth():
    global _admin_token
    for ep in [
        f"{PB_URL}/api/collections/_superusers/auth-with-password",
        f"{PB_URL}/api/admins/auth-with-password",
    ]:
        r = httpx.post(ep, json={"identity": PB_ADMIN_EMAIL, "password": PB_ADMIN_PASSWORD}, timeout=20)
        if r.status_code == 200:
            _admin_token = r.json().get("token", "")
            if _admin_token:
                return
    raise RuntimeError("PocketBase admin auth failed")


def _pb_headers():
    return {"Authorization": _admin_token}


def _pb_get(path, params=None):
    r = httpx.get(f"{PB_URL}{path}", headers=_pb_headers(), params=params, timeout=20)
    if r.status_code == 401:
        _pb_admin_auth()
        r = httpx.get(f"{PB_URL}{path}", headers=_pb_headers(), params=params, timeout=20)
    r.raise_for_status()
    return r.json()


def _pb_list(collection, filter="", per_page=500):
    params = {"perPage": per_page}
    if filter:
        params["filter"] = filter
    data = _pb_get(f"/api/collections/{collection}/records", params)
    return data.get("items", [])


def _pb_auth_user(email, password):
    """Return user record or None."""
    r = httpx.post(
        f"{PB_URL}/api/collections/gdrive_users/auth-with-password",
        json={"identity": email, "password": password},
        timeout=20,
    )
    if r.status_code == 200:
        return r.json().get("record")
    return None


# ---------------------------------------------------------------------------
# Google Drive helpers
# ---------------------------------------------------------------------------

def _build_drive_service(refresh_token_encrypted: str):
    refresh_token = _fernet.decrypt(refresh_token_encrypted.encode()).decode()
    with open(CREDENTIALS_PATH) as f:
        creds_data = json.load(f)
    web = creds_data.get("web") or creds_data.get("installed")
    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=web["client_id"],
        client_secret=web["client_secret"],
        scopes=SCOPES,
    )
    return gbuild("drive", "v3", credentials=creds)


def _stream_drive_file(refresh_token_encrypted: str, drive_file_id: str) -> bytes:
    service = _build_drive_service(refresh_token_encrypted)
    request = service.files().get_media(fileId=drive_file_id)
    buf = io.BytesIO()
    downloader = MediaIoBaseDownload(buf, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    buf.seek(0)
    return buf.read()


# ---------------------------------------------------------------------------
# DAV Provider
# ---------------------------------------------------------------------------

class GDriveGenieProvider(DAVProvider):

    def get_resource_inst(self, path, environ):
        user_id = environ.get("gd.user_id")
        if not user_id:
            return None

        parts = [p for p in path.strip("/").split("/") if p]

        if len(parts) == 0:
            return RootCollection("/", environ, user_id)

        if len(parts) == 1:
            folder_name = parts[0]
            folders = _pb_list("gdrive_folders", filter=f'user="{user_id}" && name="{folder_name}" && parent=""')
            if not folders:
                return None
            return VirtualFolderCollection(path, environ, user_id, folders[0])

        if len(parts) == 2:
            folder_name, file_name = parts
            folders = _pb_list("gdrive_folders", filter=f'user="{user_id}" && name="{folder_name}" && parent=""')
            if not folders:
                return None
            folder_id = folders[0]["id"]
            # Find the file in this folder
            mappings = _pb_list("gdrive_folder_files", filter=f'folder="{folder_id}"')
            for m in mappings:
                file_rows = _pb_list("gdrive_files", filter=f'id="{m["file"]}"')
                if file_rows and file_rows[0].get("file_name") == file_name:
                    return DriveFileResource(path, environ, file_rows[0])

        return None


class RootCollection(DAVCollection):

    def __init__(self, path, environ, user_id):
        super().__init__(path, environ)
        self.user_id = user_id

    def get_member_names(self):
        folders = _pb_list("gdrive_folders", filter=f'user="{self.user_id}" && parent=""')
        return [f["name"] for f in folders]

    def get_member(self, name):
        folders = _pb_list("gdrive_folders", filter=f'user="{self.user_id}" && name="{name}" && parent=""')
        if not folders:
            return None
        path = self.path.rstrip("/") + "/" + name
        return VirtualFolderCollection(path, self.environ, self.user_id, folders[0])


class VirtualFolderCollection(DAVCollection):

    def __init__(self, path, environ, user_id, folder_rec):
        super().__init__(path, environ)
        self.user_id = user_id
        self.folder_rec = folder_rec
        self.folder_id = folder_rec["id"]

    def get_member_names(self):
        mappings = _pb_list("gdrive_folder_files", filter=f'folder="{self.folder_id}"')
        names = []
        for m in mappings:
            file_rows = _pb_list("gdrive_files", filter=f'id="{m["file"]}"')
            if file_rows:
                names.append(file_rows[0].get("file_name", m["file"]))
        return names

    def get_member(self, name):
        mappings = _pb_list("gdrive_folder_files", filter=f'folder="{self.folder_id}"')
        for m in mappings:
            file_rows = _pb_list("gdrive_files", filter=f'id="{m["file"]}"')
            if file_rows and file_rows[0].get("file_name") == name:
                path = self.path.rstrip("/") + "/" + name
                return DriveFileResource(path, self.environ, file_rows[0])
        return None


class DriveFileResource(DAVNonCollection):

    def __init__(self, path, environ, file_rec):
        super().__init__(path, environ)
        self.file_rec = file_rec

    def get_content_length(self):
        return int(self.file_rec.get("size") or 0)

    def get_content_type(self):
        return self.file_rec.get("mime_type") or "application/octet-stream"

    def get_content(self):
        # Look up account for this file
        acc_rows = _pb_list("gdrive_accounts", filter=f'id="{self.file_rec["account"]}"')
        if not acc_rows or not acc_rows[0].get("is_connected"):
            raise DAVError(HTTP_NOT_FOUND, "Account not connected")
        acc = acc_rows[0]
        data = _stream_drive_file(acc["refresh_token_encrypted"], self.file_rec["drive_file_id"])
        return io.BytesIO(data)

    def support_ranges(self):
        return False


# ---------------------------------------------------------------------------
# Domain controller (HTTP Basic Auth → PocketBase)
# ---------------------------------------------------------------------------

class PBDomainController:
    def __init__(self, realm):
        self.realm = realm

    def get_domain_realm(self, path_info, environ):
        return self.realm

    def require_authentication(self, realm, environ):
        return True

    def is_share_anonymous(self, realm, environ):
        return False

    def basic_auth_user(self, realm, user_name, password, environ):
        rec = _pb_auth_user(user_name, password)
        if rec:
            environ["gd.user_id"] = rec["id"]
            return True
        return False

    def supports_http_digest_auth_algorithm(self, algorithm):
        return False

    def digest_auth_user(self, realm, user_name, environ):
        return None


# ---------------------------------------------------------------------------
# Boot
# ---------------------------------------------------------------------------

def main():
    logger.info("Authenticating with PocketBase...")
    _pb_admin_auth()
    logger.info("PocketBase admin ready.")

    config = {
        "provider_mapping": {"/": GDriveGenieProvider()},
        "http_authenticator": {
            "domain_controller": PBDomainController("GDriveGenie"),
            "accept_basic": True,
            "accept_digest": False,
            "default_to_digest": False,
        },
        "verbose": 1,
        "logging": {"enable_loggers": []},
        "property_manager": True,
        "lock_storage": True,
    }

    app = WsgiDAVApp(config)
    server = wsgi.Server(("0.0.0.0", WEBDAV_PORT), app)
    logger.info("WebDAV server running on port %d", WEBDAV_PORT)
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()


if __name__ == "__main__":
    main()
