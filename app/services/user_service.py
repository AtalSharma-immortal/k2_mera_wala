from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.utils.crypto import CryptoService


class UserService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def register_user(self, name: str) -> tuple[User, str]:
        public_key, private_key = CryptoService.generate_wallet()
        existing = self.db.scalar(select(User).where(User.public_key == public_key))
        if existing:
            raise ValueError("Generated key collision; retry registration")

        user = User(name=name, public_key=public_key)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user, private_key
