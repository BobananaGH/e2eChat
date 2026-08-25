# code/client/client.py
import os
import socket
import ssl
import json
import threading
from shared import protocol as p
from client.core.crypto import E2EECrypto

class E2EEClient:
    def __init__(self, host="127.0.0.1", port=5000, timeout=10.0):
        self.host = host
        self.port = port
        self.username = None
        self.crypto = E2EECrypto()
        self.peers = {}  # Stores session keys: target_username -> E2EECrypto instance
        self.on_message_received = None  # Callback for GUI (e.g. PySide6 signal)

        # 1. Establish TLS Transport Socket (Using your certs/server.crt)
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        cert_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "certs", "server.crt")
        )
        context.load_verify_locations(cert_path)
        
        # Self-signed cert workaround for local testing (localhost)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_REQUIRED

        raw_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        raw_sock.settimeout(timeout)
        raw_sock.connect((host, port))

        self.socket = context.wrap_socket(raw_sock, server_hostname=host)
        self.socket.settimeout(None)  # Remove timeout for long-lived listener thread
        
        self.conn = p.Connection(self.socket)

    def register_and_connect(self, username: str) -> bool:
        """Registers the user's DH Public Key with the relay server."""
        self.username = username
        pub_key_b64 = self.crypto.get_public_bytes_b64()
        
        payload = json.dumps({
            "type": "REGISTER",
            "payload": {
                "username": self.username,
                "pub_key": pub_key_b64
            }
        })
        self.conn.send_line(payload)
        
        # Start listener background thread
        threading.Thread(target=self._listen_loop, daemon=True).start()
        return True

    def initiate_key_exchange(self, target_username: str):
        """Requests the target peer's DH Public Key from the server."""
        payload = json.dumps({
            "type": "GET_PUBKEY",
            "payload": {"target": target_username}
        })
        self.conn.send_line(payload)

    def send_chat_message(self, target_username: str, plaintext: str) -> bool:
        """Encrypts message payload using AES-GCM and sends through server relay."""
        if target_username not in self.peers:
            print(f"[!] No shared key with {target_username}. Initiating handshake...")
            self.initiate_key_exchange(target_username)
            return False

        # End-to-End Encrypt payload
        encrypted_data = self.peers[target_username].encrypt_message(plaintext)
        
        relay_payload = json.dumps({
            "type": "MSG_RELAY",
            "payload": {
                "from": self.username,
                "to": target_username,
                "nonce": encrypted_data["nonce"],
                "ciphertext": encrypted_data["ciphertext"]
            }
        })
        self.conn.send_line(relay_payload)
        return True

    def _listen_loop(self):
        """Listens continuously for incoming server responses and messages."""
        while True:
            try:
                line = self.conn.recv_line()
                if not line:
                    break
                
                msg = json.loads(line)
                mtype = msg.get("type")
                payload = msg.get("payload", {})

                if mtype == "PUBKEY_RESP":
                    target = payload["target"]
                    peer_pub_key = payload["pub_key"]
                    
                    # Compute Shared Secret via DH & HKDF
                    peer_session = E2EECrypto()
                    peer_session.private_key = self.crypto.private_key
                    peer_session.generate_shared_key(peer_pub_key)
                    self.peers[target] = peer_session
                    print(f"[+] E2EE Shared Key established with '{target}'")

                elif mtype == "MSG_RECEIVE":
                    sender = payload["from"]
                    nonce = payload["nonce"]
                    ciphertext = payload["ciphertext"]

                    if sender in self.peers:
                        decrypted_text = self.peers[sender].decrypt_message(nonce, ciphertext)
                        if self.on_message_received:
                            self.on_message_received(sender, decrypted_text)
                        else:
                            print(f"\n[{sender} -> ME]: {decrypted_text}")

            except Exception as e:
                print(f"[-] Connection listener error: {e}")
                break

    def close(self):
        try:
            self.conn.close()
        finally:
            self.socket.close()