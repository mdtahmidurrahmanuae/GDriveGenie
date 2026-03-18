# Re-export PocketBase client as the canonical DB dependency.
# All routes import get_pb / PBClient from here.
from services.pb_client import PBClient, get_pb  # noqa: F401
