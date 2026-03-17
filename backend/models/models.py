from dataclasses import dataclass
from typing import Optional


@dataclass
class DriveAccount:
    id: int
    account_index: int
    email: Optional[str]
    refresh_token: Optional[str]
    access_token: Optional[str]
    token_expiry: Optional[str]   # stored as ISO-8601 TEXT in D1
    is_connected: bool

    @classmethod
    def from_row(cls, row: dict) -> "DriveAccount":
        return cls(
            id=row["id"],
            account_index=row["account_index"],
            email=row.get("email"),
            refresh_token=row.get("refresh_token"),
            access_token=row.get("access_token"),
            token_expiry=row.get("token_expiry"),
            is_connected=bool(row["is_connected"]),
        )


@dataclass
class File:
    id: int
    file_name: str
    drive_file_id: str
    account_index: int
    size: int
    mime_type: Optional[str]
    thumbnail_link: Optional[str]
    parent_drive_file_id: Optional[str]
    created_at: str   # stored as ISO-8601 TEXT in D1

    @classmethod
    def from_row(cls, row: dict) -> "File":
        return cls(
            id=row["id"],
            file_name=row["file_name"],
            drive_file_id=row["drive_file_id"],
            account_index=row["account_index"],
            size=row.get("size") or 0,
            mime_type=row.get("mime_type"),
            thumbnail_link=row.get("thumbnail_link"),
            parent_drive_file_id=row.get("parent_drive_file_id"),
            created_at=row.get("created_at", ""),
        )


@dataclass
class Profile:
    id: int
    display_name: Optional[str]
    bio: Optional[str]
    avatar_drive_file_id: Optional[str]
    avatar_account_index: Optional[int]

    @classmethod
    def from_row(cls, row: dict) -> "Profile":
        return cls(
            id=row["id"],
            display_name=row.get("display_name"),
            bio=row.get("bio"),
            avatar_drive_file_id=row.get("avatar_drive_file_id"),
            avatar_account_index=row.get("avatar_account_index"),
        )


@dataclass
class AppConfig:
    key: str
    value: str
