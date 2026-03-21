from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.blockchain import Block, Transaction
from app.utils.crypto import CryptoService
from app.utils.hash_utils import sha256_json


@dataclass
class TxPayload:
    property_id: str
    from_public_key: str
    to_public_key: str
    document_hash: str
    media_hash: str
    timestamp: str


class PoAConsensus:
    def __init__(self) -> None:
        settings = get_settings()
        self.authorized_nodes = settings.authorized_node_list
        self.quorum = settings.poa_quorum

    def validate_block(self, block_hash: str) -> list[str]:
        """Simulate multi-node PoA approval deterministically from the hash."""
        approvals: list[str] = []
        for node in self.authorized_nodes:
            decision_seed = sha256_json({"node": node, "block_hash": block_hash})
            if int(decision_seed[-1], 16) % 2 == 0:
                approvals.append(node)
        if len(approvals) < self.quorum:
            approvals = self.authorized_nodes[: self.quorum]
        return approvals


class BlockchainService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.consensus = PoAConsensus()

    def ensure_genesis_block(self) -> None:
        exists = self.db.scalar(select(Block.id).where(Block.index == 0))
        if exists:
            return
        timestamp = datetime.utcnow()
        genesis_hash = sha256_json(
            {
                "index": 0,
                "timestamp": timestamp.isoformat(),
                "transactions": [],
                "previous_hash": "0" * 64,
            }
        )
        genesis = Block(
            index=0,
            timestamp=timestamp,
            previous_hash="0" * 64,
            hash=genesis_hash,
            validator_approvals=self.consensus.authorized_nodes,
        )
        self.db.add(genesis)
        self.db.commit()

    @staticmethod
    def transaction_payload_hash(tx: TxPayload) -> str:
        return sha256_json(asdict(tx))

    def add_transaction(
        self,
        *,
        property_id: str,
        from_public_key: str,
        to_public_key: str,
        document_hash: str,
        media_hash: str,
        signature: str | None,
        verify_signature: bool,
        tx_timestamp: str | None = None,
    ) -> Transaction:
        timestamp = datetime.fromisoformat(tx_timestamp) if tx_timestamp else datetime.utcnow()
        tx_payload = TxPayload(
            property_id=property_id,
            from_public_key=from_public_key,
            to_public_key=to_public_key,
            document_hash=document_hash,
            media_hash=media_hash,
            timestamp=timestamp.isoformat(),
        )
        payload_hash = self.transaction_payload_hash(tx_payload)

        if verify_signature:
            if not signature:
                raise ValueError("Signature is required for this transaction")
            if not CryptoService.verify_signature(from_public_key, payload_hash, signature):
                raise ValueError("Invalid transaction signature")

        latest_block = self.db.scalar(select(Block).order_by(Block.index.desc()).limit(1))
        if latest_block is None:
            raise ValueError("Genesis block missing")

        block_index = latest_block.index + 1
        block_payload: dict[str, Any] = {
            "index": block_index,
            "timestamp": timestamp.isoformat(),
            "transactions": [
                {
                    "property_id": property_id,
                    "from_public_key": from_public_key,
                    "to_public_key": to_public_key,
                    "document_hash": document_hash,
                    "media_hash": media_hash,
                    "signature": signature,
                    "payload_hash": payload_hash,
                }
            ],
            "previous_hash": latest_block.hash,
        }
        block_hash = sha256_json(block_payload)
        approvals = self.consensus.validate_block(block_hash)
        if len(approvals) < self.consensus.quorum:
            raise ValueError("PoA quorum not met")

        block = Block(
            index=block_index,
            timestamp=timestamp,
            previous_hash=latest_block.hash,
            hash=block_hash,
            validator_approvals=approvals,
        )
        tx = Transaction(
            property_id=property_id,
            from_public_key=from_public_key,
            to_public_key=to_public_key,
            document_hash=document_hash,
            media_hash=media_hash,
            signature=signature,
            tx_timestamp=timestamp,
            payload_hash=payload_hash,
        )
        block.transactions.append(tx)
        self.db.add(block)
        self.db.commit()
        self.db.refresh(tx)
        return tx

    def get_chain(self) -> list[Block]:
        return list(self.db.scalars(select(Block).order_by(Block.index.asc())).all())

    def validate_chain(self) -> bool:
        chain = self.get_chain()
        if not chain:
            return False

        for i, block in enumerate(chain):
            txs = [
                {
                    "property_id": tx.property_id,
                    "from_public_key": tx.from_public_key,
                    "to_public_key": tx.to_public_key,
                    "document_hash": tx.document_hash,
                    "media_hash": tx.media_hash,
                    "signature": tx.signature,
                    "payload_hash": tx.payload_hash,
                }
                for tx in block.transactions
            ]
            calculated = sha256_json(
                {
                    "index": block.index,
                    "timestamp": block.timestamp.isoformat(),
                    "transactions": txs,
                    "previous_hash": block.previous_hash,
                }
            )
            if calculated != block.hash:
                return False

            if i == 0:
                if block.previous_hash != "0" * 64:
                    return False
                continue

            previous = chain[i - 1]
            if block.previous_hash != previous.hash:
                return False

            if len(block.validator_approvals or []) < self.consensus.quorum:
                return False

            for tx in block.transactions:
                tx_payload = TxPayload(
                    property_id=tx.property_id,
                    from_public_key=tx.from_public_key,
                    to_public_key=tx.to_public_key,
                    document_hash=tx.document_hash,
                    media_hash=tx.media_hash,
                    timestamp=tx.tx_timestamp.isoformat(),
                )
                if self.transaction_payload_hash(tx_payload) != tx.payload_hash:
                    return False
                if tx.from_public_key != "SYSTEM":
                    if not tx.signature:
                        return False
                    if not CryptoService.verify_signature(tx.from_public_key, tx.payload_hash, tx.signature):
                        return False

        return True
