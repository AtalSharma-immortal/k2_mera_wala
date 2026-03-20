import base64

from ecdsa import BadSignatureError, SECP256k1, SigningKey, VerifyingKey


class CryptoService:
    @staticmethod
    def generate_wallet() -> tuple[str, str]:
        signing_key = SigningKey.generate(curve=SECP256k1)
        private_key = signing_key.to_string().hex()
        public_key = signing_key.verifying_key.to_string().hex()
        return public_key, private_key

    @staticmethod
    def sign_payload(private_key_hex: str, payload_hash: str) -> str:
        signing_key = SigningKey.from_string(bytes.fromhex(private_key_hex), curve=SECP256k1)
        signature = signing_key.sign(payload_hash.encode("utf-8"))
        return base64.b64encode(signature).decode("utf-8")

    @staticmethod
    def verify_signature(public_key_hex: str, payload_hash: str, signature_b64: str) -> bool:
        try:
            vk = VerifyingKey.from_string(bytes.fromhex(public_key_hex), curve=SECP256k1)
            signature = base64.b64decode(signature_b64)
            return vk.verify(signature, payload_hash.encode("utf-8"))
        except (ValueError, BadSignatureError):
            return False
