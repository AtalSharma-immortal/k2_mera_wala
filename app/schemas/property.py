from datetime import datetime

from pydantic import BaseModel


class PropertyResponse(BaseModel):
    property_id: str
    owner_public_key: str
    location: str
    description: str
    media_hash: str
    media_integrity_ok: bool
    created_at: datetime


class PropertyHistoryResponse(BaseModel):
    property_id: str
    transactions: list[dict]
