from sqlalchemy import select
from sqlalchemy.orm import Session

from app.blockchain.chain import BlockchainService
from app.models.blockchain import Transaction
from app.models.property import Property
from app.models.user import User
from app.services.storage_service import StorageService
from app.utils.hash_utils import sha256_hex


class PropertyService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.storage = StorageService()
        self.blockchain = BlockchainService(db)

    async def register_property(
        self,
        *,
        property_id: str,
        owner_public_key: str,
        location: str,
        description: str,
        media,
    ) -> Property:
        existing = self.db.scalar(select(Property).where(Property.property_id == property_id))
        if existing:
            raise ValueError("Property already exists")

        owner = self.db.scalar(select(User).where(User.public_key == owner_public_key))
        if not owner:
            raise ValueError("Owner public key is unknown")

        media_path, media_hash = await self.storage.save_media(property_id, media)
        prop = Property(
            property_id=property_id,
            owner_public_key=owner_public_key,
            location=location,
            description=description,
            media_path=media_path,
            media_hash=media_hash,
        )
        self.db.add(prop)
        self.db.commit()
        self.db.refresh(prop)

        document_hash = sha256_hex(f"{property_id}:{location}:{description}".encode("utf-8"))
        self.blockchain.ensure_genesis_block()
        self.blockchain.add_transaction(
            property_id=property_id,
            from_public_key="SYSTEM",
            to_public_key=owner_public_key,
            document_hash=document_hash,
            media_hash=media_hash,
            signature=None,
            verify_signature=False,
        )

        return prop

    def transfer_property(
        self,
        *,
        property_id: str,
        to_public_key: str,
        document_text: str,
        tx_timestamp: str,
        signature: str,
    ) -> Transaction:
        prop = self.db.scalar(select(Property).where(Property.property_id == property_id))
        if not prop:
            raise ValueError("Property not found")

        recipient = self.db.scalar(select(User).where(User.public_key == to_public_key))
        if not recipient:
            raise ValueError("Recipient public key is unknown")

        self.blockchain.ensure_genesis_block()
        tx = self.blockchain.add_transaction(
            property_id=property_id,
            from_public_key=prop.owner_public_key,
            to_public_key=to_public_key,
            document_hash=sha256_hex(document_text.encode("utf-8")),
            media_hash=prop.media_hash,
            signature=signature,
            verify_signature=True,
            tx_timestamp=tx_timestamp,
        )

        prop.owner_public_key = to_public_key
        self.db.add(prop)
        self.db.commit()
        return tx

    def get_property(self, property_id: str) -> Property | None:
        return self.db.scalar(select(Property).where(Property.property_id == property_id))

    def get_history(self, property_id: str) -> list[Transaction]:
        return list(
            self.db.scalars(
                select(Transaction)
                .where(Transaction.property_id == property_id)
                .order_by(Transaction.tx_timestamp.asc())
            ).all()
        )
