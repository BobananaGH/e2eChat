# code/client/core/crypto.py
import os
import base64
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

class E2EECrypto:
    def __init__(self):
        self.private_key = ec.generate_private_key(ec.SECP256R1())
        self.public_key = self.private_key.public_key()
        self.shared_aes_key = None

    def get_public_bytes_b64(self) -> str:
        pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return base64.b64encode(pem).decode('utf-8')

    def generate_shared_key(self, peer_pub_b64: str):
        pem_data = base64.b64decode(peer_pub_b64)
        peer_public_key = serialization.load_pem_public_key(pem_data)
        raw_shared_secret = self.private_key.exchange(ec.ECDH(), peer_public_key)
        
        self.shared_aes_key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=b'e2ee-handshake',
        ).derive(raw_shared_secret)

    def encrypt_message(self, plaintext: str) -> dict:
        if not self.shared_aes_key:
            raise ValueError("Shared key not established.")
        aesgcm = AESGCM(self.shared_aes_key)
        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(nonce, plaintext.encode('utf-8'), None)
        return {
            "nonce": base64.b64encode(nonce).decode('utf-8'),
            "ciphertext": base64.b64encode(ciphertext).decode('utf-8')
        }

    def decrypt_message(self, nonce_b64: str, ciphertext_b64: str) -> str:
        if not self.shared_aes_key:
            raise ValueError("Shared key not established.")
        aesgcm = AESGCM(self.shared_aes_key)
        nonce = base64.b64decode(nonce_b64)
        ciphertext = base64.b64decode(ciphertext_b64)
        return aesgcm.decrypt(nonce, ciphertext, None).decode('utf-8')