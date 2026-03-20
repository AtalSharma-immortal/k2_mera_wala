# Blockchain Property Registry System (FastAPI + SQLAlchemy)

A near-production-ready MVP backend for secure property registration and transfer, backed by a custom blockchain ledger with Proof-of-Authority (PoA) simulation.

## Key Capabilities

- ECDSA wallet generation per user (SECP256k1)
- Public-key identity model
- Admin-only property registration with media upload
- SHA-256 media hash anchoring on blockchain
- Signed property transfers with strict signature verification
- Custom block + transaction model with hash-linked immutability
- Chain integrity validation and tamper detection
- Simplified PoA consensus with authorized validators and quorum
- SQLAlchemy ORM persistence (local SQLite by default, with overrideable DB URL)

## Project Structure

```text
/app
  /api          # FastAPI route handlers
  /core         # App config and DB wiring
  /blockchain   # Chain + consensus logic
  /models       # SQLAlchemy ORM models
  /schemas      # Pydantic request/response schemas
  /services     # Domain business logic
  /utils        # Hashing and cryptography helpers
```

## Prerequisites

- Python 3.11+

## Setup

1. Install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Configure environment:

```bash
cp .env.example .env
# edit .env as needed
```

Local mode now stores DB + media under `./data/` automatically (`data/property_registry.db` and `data/storage/`).

If you want a different backend, set `DATABASE_URL` and `STORAGE_PATH` in `.env`.

3. Run API:

```bash
uvicorn app.main:app --reload
```

The app creates tables automatically on startup.

5. Open the web console:

```text
http://localhost:8000/
```

The frontend is served from `app/web` (`index.html`, `styles.css`, `app.js`).

## Security Model

- **User identity**: public key
- **Private key handling**: returned once at registration; not stored server-side
- **Transfer authorization**: only current owner can transfer, proven by ECDSA signature
- **Tamper detection**: each block hash links to previous block hash
- **Media integrity**: file SHA-256 stored in DB + blockchain; verified on retrieval
- **Admin gate**: `x-admin-token` required for property registration

## API Endpoints

### 1) Register User

`POST /register_user`

```json
{
  "name": "Alice"
}
```

Returns `public_key` and `private_key` (save private key securely).

---

### 2) Register Property (Admin)

`POST /register_property` (multipart/form-data)

Headers:

- `x-admin-token: <ADMIN_TOKEN>`

Form fields:

- `property_id`
- `owner_public_key`
- `location`
- `description`
- `media` (image/video)

---

### 3) Transfer Property

`POST /transfer_property`

Payload fields:

- `property_id`
- `to_public_key`
- `document_text`
- `tx_timestamp` (ISO-8601)
- `signature` (base64 ECDSA signature)

> Signature must be produced from this exact payload hash data:
> `property_id, from_public_key, to_public_key, document_hash, media_hash, timestamp`

---

### 4) Get Property

`GET /property/{id}`

Includes `media_integrity_ok` to confirm file hash validity.

---

### 5) Get Property History

`GET /property/{id}/history`

Returns blockchain-backed ownership transfer timeline.

---

### 6) Get Blockchain

`GET /blockchain`

Returns chain blocks and global chain validity result.

## Frontend (HTML/CSS/JS)

This repo now includes a usable operator dashboard:

- `app/web/index.html` – workflow UI for all required operations
- `app/web/styles.css` – responsive styling
- `app/web/app.js` – API client logic + browser-side transfer signing using secp256k1

It supports:

- Registering users and displaying generated key pairs
- Admin property registration with media upload
- Client-side transfer signing with owner private key before submitting to backend
- Property lookup, history view, and blockchain inspection

## Example cURL Workflow

### Register users

```bash
curl -X POST http://localhost:8000/register_user \
  -H "Content-Type: application/json" \
  -d '{"name":"Alice"}'

curl -X POST http://localhost:8000/register_user \
  -H "Content-Type: application/json" \
  -d '{"name":"Bob"}'
```

### Register property with media (admin)

```bash
curl -X POST http://localhost:8000/register_property \
  -H "x-admin-token: change-me-admin-token" \
  -F "property_id=PROP-001" \
  -F "owner_public_key=<ALICE_PUBLIC_KEY>" \
  -F "location=221B Baker Street" \
  -F "description=Freehold unit" \
  -F "media=@/path/to/property.jpg"
```

### Build and sign transfer payload (Python client-side snippet)

```python
from datetime import datetime, timezone
from app.utils.hash_utils import sha256_hex
from app.utils.signing_helper import build_transfer_payload_hash, sign_transfer_payload

property_id = "PROP-001"
from_public_key = "<ALICE_PUBLIC_KEY>"
to_public_key = "<BOB_PUBLIC_KEY>"
media_hash = "<CURRENT_PROPERTY_MEDIA_HASH>"
document_text = "Sale deed reference #2026-0001"
document_hash = sha256_hex(document_text.encode("utf-8"))
tx_timestamp = datetime.now(timezone.utc).isoformat()

payload_hash = build_transfer_payload_hash(
    property_id=property_id,
    from_public_key=from_public_key,
    to_public_key=to_public_key,
    document_hash=document_hash,
    media_hash=media_hash,
    timestamp=tx_timestamp,
)

signature = sign_transfer_payload("<ALICE_PRIVATE_KEY>", payload_hash)
print(tx_timestamp)
print(signature)
```

### Submit transfer

```bash
curl -X POST http://localhost:8000/transfer_property \
  -H "Content-Type: application/json" \
  -d '{
    "property_id":"PROP-001",
    "to_public_key":"<BOB_PUBLIC_KEY>",
    "document_text":"Sale deed reference #2026-0001",
    "tx_timestamp":"<TX_TIMESTAMP>",
    "signature":"<SIGNATURE_BASE64>"
  }'
```

## Notes for Production Hardening

- Move private-key generation to HSM or secure client wallet app
- Replace admin token with JWT + RBAC + audit trails
- Use object storage (S3/MinIO) with signed URLs
- Add migrations (Alembic), soft deletes, and richer ownership states
- Add per-node cryptographic attestations for PoA approvals
- Add asynchronous eventing, retries, and monitoring

## Persistence Notes (Local vs Vercel)

- **Local machine**: persistent by default using `./data/property_registry.db` and `./data/storage/`.
- **Vercel serverless**: `/tmp` is still ephemeral between cold starts/redeploys. For durable cloud persistence, configure an external DB/object storage via env vars.

## Deploy on Vercel

This repository is now prepared for Vercel serverless deployment:

- `api/index.py` exports the FastAPI `app` for `@vercel/python`
- `vercel.json` routes all requests to the FastAPI app

### 1) Push to GitHub

Push this repo/branch to GitHub.

### 2) Create Vercel project

- In Vercel, click **Add New Project**
- Import your GitHub repo
- Framework preset: **Other**
- Root directory: repo root

### 3) Configure environment variables in Vercel

Set these for production:

- `DATABASE_URL` (managed Postgres URL, e.g. Neon/Supabase/RDS)
- `ADMIN_TOKEN`
- `AUTHORIZED_NODES`
- `POA_QUORUM`

- If `DATABASE_URL` is not set on Vercel, the app now auto-falls back to:

- `sqlite:////tmp/property_registry.db`

This prevents startup crashes (`FUNCTION_INVOCATION_FAILED`) and is useful for quick demos.
For real deployments, use managed Postgres because `/tmp` storage is ephemeral.

- `STORAGE_PATH=/tmp/storage`


> Important: Vercel file storage is ephemeral. Use `/tmp` only for temporary files.  
> For production media durability, replace local disk storage with S3/MinIO.

### 4) Deploy

Trigger deploy from Vercel UI (or `vercel --prod` CLI).

After deployment:

- API and web console are served from the same base URL
- `/` opens the frontend console
- endpoints such as `/register_user` and `/blockchain` are available directly
