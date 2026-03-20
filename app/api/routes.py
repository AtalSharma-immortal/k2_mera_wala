from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.blockchain.chain import BlockchainService
from app.core.config import get_settings
from app.core.database import get_db
from app.schemas.property import PropertyHistoryResponse, PropertyResponse
from app.schemas.transfer import TransferRequest, TransferResponse
from app.schemas.user import UserCreateRequest, UserCreateResponse
from app.services.property_service import PropertyService
from app.services.storage_service import StorageService
from app.services.user_service import UserService

router = APIRouter()
settings = get_settings()


def require_admin(x_admin_token: str = Header(default="")) -> None:
    if x_admin_token != settings.admin_token:
        raise HTTPException(status_code=403, detail="Admin token is invalid")


@router.post("/register_user", response_model=UserCreateResponse)
def register_user(payload: UserCreateRequest, db: Session = Depends(get_db)) -> UserCreateResponse:
    service = UserService(db)
    user, private_key = service.register_user(payload.name)
    return UserCreateResponse(name=user.name, public_key=user.public_key, private_key=private_key)


@router.post("/register_property")
async def register_property(
    property_id: str = Form(...),
    owner_public_key: str = Form(...),
    location: str = Form(...),
    description: str = Form(...),
    media: UploadFile = File(...),
    db: Session = Depends(get_db),
    _admin: None = Depends(require_admin),
):
    try:
        service = PropertyService(db)
        prop = await service.register_property(
            property_id=property_id,
            owner_public_key=owner_public_key,
            location=location,
            description=description,
            media=media,
        )
        return {"property_id": prop.property_id, "media_hash": prop.media_hash, "owner_public_key": prop.owner_public_key}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/transfer_property", response_model=TransferResponse)
def transfer_property(payload: TransferRequest, db: Session = Depends(get_db)) -> TransferResponse:
    try:
        service = PropertyService(db)
        tx = service.transfer_property(
            property_id=payload.property_id,
            to_public_key=payload.to_public_key,
            document_text=payload.document_text,
            tx_timestamp=payload.tx_timestamp.isoformat(),
            signature=payload.signature,
        )
        return TransferResponse(
            property_id=tx.property_id,
            from_public_key=tx.from_public_key,
            to_public_key=tx.to_public_key,
            transaction_id=tx.id,
            block_index=tx.block.index,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/property/{property_id}", response_model=PropertyResponse)
def get_property(property_id: str, db: Session = Depends(get_db)) -> PropertyResponse:
    service = PropertyService(db)
    storage = StorageService()
    prop = service.get_property(property_id)
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    return PropertyResponse(
        property_id=prop.property_id,
        owner_public_key=prop.owner_public_key,
        location=prop.location,
        description=prop.description,
        media_hash=prop.media_hash,
        media_integrity_ok=storage.verify_media(prop.media_path, prop.media_hash),
        created_at=prop.created_at,
    )


@router.get("/property/{property_id}/history", response_model=PropertyHistoryResponse)
def get_property_history(property_id: str, db: Session = Depends(get_db)) -> PropertyHistoryResponse:
    service = PropertyService(db)
    transactions = service.get_history(property_id)
    return PropertyHistoryResponse(
        property_id=property_id,
        transactions=[
            {
                "from_public_key": tx.from_public_key,
                "to_public_key": tx.to_public_key,
                "document_hash": tx.document_hash,
                "media_hash": tx.media_hash,
                "signature": tx.signature,
                "timestamp": tx.tx_timestamp.isoformat(),
                "block_index": tx.block.index,
            }
            for tx in transactions
        ],
    )


@router.get("/blockchain")
def get_blockchain(db: Session = Depends(get_db)):
    blockchain = BlockchainService(db)
    blockchain.ensure_genesis_block()
    chain = blockchain.get_chain()
    return {
        "valid": blockchain.validate_chain(),
        "length": len(chain),
        "chain": [
            {
                "index": block.index,
                "timestamp": block.timestamp.isoformat(),
                "previous_hash": block.previous_hash,
                "hash": block.hash,
                "validator_approvals": block.validator_approvals,
                "transactions": [
                    {
                        "property_id": tx.property_id,
                        "from_public_key": tx.from_public_key,
                        "to_public_key": tx.to_public_key,
                        "document_hash": tx.document_hash,
                        "media_hash": tx.media_hash,
                        "signature": tx.signature,
                        "timestamp": tx.tx_timestamp.isoformat(),
                    }
                    for tx in block.transactions
                ],
            }
            for block in chain
        ],
    }
