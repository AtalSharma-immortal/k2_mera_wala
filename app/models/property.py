from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Property(Base):
    __tablename__ = "properties"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    property_id: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    owner_public_key: Mapped[str] = mapped_column(ForeignKey("users.public_key"), nullable=False, index=True)
    location: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    media_path: Mapped[str] = mapped_column(String(512), nullable=False)
    media_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    owner = relationship("User", primaryjoin="Property.owner_public_key==User.public_key", lazy="joined")
