"""Utility helpers for clients generating signatures compatible with transfer payload verification."""

from app.blockchain.chain import TxPayload
from app.utils.crypto import CryptoService
from app.utils.hash_utils import sha256_json


def build_transfer_payload_hash(
    *,
    property_id: str,
    from_public_key: str,
    to_public_key: str,
    document_hash: str,
    media_hash: str,
    timestamp: str,
) -> str:
    payload = TxPayload(
        property_id=property_id,
        from_public_key=from_public_key,
        to_public_key=to_public_key,
        document_hash=document_hash,
        media_hash=media_hash,
        timestamp=timestamp,
    )
    return sha256_json(payload.__dict__)


def sign_transfer_payload(private_key: str, payload_hash: str) -> str:
    return CryptoService.sign_payload(private_key, payload_hash)
