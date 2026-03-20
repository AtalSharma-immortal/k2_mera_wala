from datetime import datetime

from pydantic import BaseModel, Field


class TransferRequest(BaseModel):
    property_id: str = Field(min_length=1, max_length=120)
    to_public_key: str = Field(min_length=66)
    document_text: str = Field(min_length=1)
    tx_timestamp: datetime = Field(description="ISO-8601 UTC timestamp used in the signed payload")
    signature: str = Field(min_length=32)


class TransferResponse(BaseModel):
    property_id: str
    from_public_key: str
    to_public_key: str
    transaction_id: int
    block_index: int


class SignTransferRequest(BaseModel):
    property_id: str = Field(min_length=1, max_length=120)
    from_public_key: str = Field(min_length=66)
    to_public_key: str = Field(min_length=66)
    document_text: str = Field(min_length=1)
    media_hash: str = Field(min_length=64, max_length=64)
    tx_timestamp: datetime = Field(description="ISO-8601 UTC timestamp used in the signed payload")
    private_key: str = Field(min_length=64)


class SignTransferResponse(BaseModel):
    payload_hash: str
    signature: str
