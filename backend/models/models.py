from dataclasses import dataclass
from typing import Optional


@dataclass
class DriveAccount:
    id: str            # PocketBase record ID
    user_id: str       # PocketBase user record ID
    account_index: int
    email: Optional[str]
    refresh_token: Optional[str]     # encrypted
    access_token: Optional[str]
    token_expiry: Optional[str]
    is_connected: bool

    @classmethod
    def from_pb(cls, row: dict) -> "DriveAccount":
        return cls(
            id=row["id"],
            user_id=row.get("user", ""),
            account_index=int(row.get("account_index", 0)),
            email=row.get("email"),
            refresh_token=row.get("refresh_token_encrypted"),
            access_token=row.get("access_token"),
            token_expiry=row.get("token_expiry"),
            is_connected=bool(row.get("is_connected", False)),
        )


@dataclass
class File:
    id: str            # PocketBase record ID
    user_id: str
    account_id: str    # PocketBase account record ID
    account_index: int # denormalized for convenience
    file_name: str
    drive_file_id: str
    size: int
    mime_type: Optional[str]
    thumbnail_link: Optional[str]
    parent_drive_file_id: Optional[str]
    drive_created_at: str

    @classmethod
    def from_pb(cls, row: dict, account_index: int = 0) -> "File":
        return cls(
            id=row["id"],
            user_id=row.get("user", ""),
            account_id=row.get("account", ""),
            account_index=account_index,
            file_name=row.get("file_name", ""),
            drive_file_id=row.get("drive_file_id", ""),
            size=int(row.get("size") or 0),
            mime_type=row.get("mime_type"),
            thumbnail_link=row.get("thumbnail_link"),
            parent_drive_file_id=row.get("parent_drive_file_id"),
            drive_created_at=row.get("drive_created_at", row.get("created", "")),
        )


@dataclass
class GDUser:
    id: str
    email: str
    display_name: Optional[str]
    bio: Optional[str]
    storage_limit_bytes: int
    storage_used_bytes: int
    is_super_admin: bool
    avatar_drive_file_id: Optional[str]
    avatar_account_id: Optional[str]

    @classmethod
    def from_pb(cls, row: dict) -> "GDUser":
        return cls(
            id=row["id"],
            email=row.get("email", ""),
            display_name=row.get("display_name"),
            bio=row.get("bio"),
            storage_limit_bytes=int(row.get("storage_limit_bytes") or 16106127360),
            storage_used_bytes=int(row.get("storage_used_bytes") or 0),
            is_super_admin=bool(row.get("is_super_admin", False)),
            avatar_drive_file_id=row.get("avatar_drive_file_id"),
            avatar_account_id=row.get("avatar_account_id"),
        )


@dataclass
class Folder:
    id: str
    user_id: str
    name: str
    parent_id: Optional[str]
    created: str

    @classmethod
    def from_pb(cls, row: dict) -> "Folder":
        return cls(
            id=row["id"],
            user_id=row.get("user", ""),
            name=row.get("name", ""),
            parent_id=row.get("parent") or None,
            created=row.get("created", ""),
        )


@dataclass
class Share:
    id: str
    folder_id: str
    created_by: str
    share_type: str     # "user" | "public" | "password"
    shared_with: Optional[str]
    password_hash: Optional[str]
    token: str
    expires_at: Optional[str]

    @classmethod
    def from_pb(cls, row: dict) -> "Share":
        return cls(
            id=row["id"],
            folder_id=row.get("folder", ""),
            created_by=row.get("created_by", ""),
            share_type=row.get("share_type", "public"),
            shared_with=row.get("shared_with") or None,
            password_hash=row.get("password_hash") or None,
            token=row.get("token", ""),
            expires_at=row.get("expires_at") or None,
        )
