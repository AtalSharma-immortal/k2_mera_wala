from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Block(Base):
    __tablename__ = "blocks"

    id: Mapped[int] = mapped_column(primary_key=True)
    index: Mapped[int] = mapped_column(Integer, unique=True, nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    previous_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    validator_approvals: Mapped[list[str]] = mapped_column(JSON, default=list)

    transactions = relationship("Transaction", back_populates="block", cascade="all, delete-orphan")


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    property_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    from_public_key: Mapped[str] = mapped_column(String(200), nullable=False)
    to_public_key: Mapped[str] = mapped_column(String(200), nullable=False)
    document_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    media_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    signature: Mapped[str | None] = mapped_column(Text, nullable=True)
    tx_timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    block_id: Mapped[int] = mapped_column(ForeignKey("blocks.id"), nullable=False)

    block = relationship("Block", back_populates="transactions")
