from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import get_settings
from app.utils.hash_utils import sha256_file


class StorageService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.base_path = Path(self.settings.storage_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    async def save_media(self, property_id: str, media: UploadFile) -> tuple[str, str]:
        extension = Path(media.filename or "media.bin").suffix or ".bin"
        filename = f"{property_id}-{uuid4().hex}{extension}"
        target = self.base_path / filename

        content = await media.read()
        target.write_bytes(content)
        media_hash = sha256_file(target)
        return str(target), media_hash

    def verify_media(self, media_path: str, expected_hash: str) -> bool:
        path = Path(media_path)
        if not path.exists():
            return False
        return sha256_file(path) == expected_hash
