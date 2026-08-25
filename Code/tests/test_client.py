# code/tests/test_client.py
import sys
from pathlib import Path

# Ensures parent Code directory is in python path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import socket
import time
import threading
from shared.protocol import Protocol, MessageType

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8080

def create_client():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((SERVER_HOST, SERVER_PORT))
    return sock

def recv_packet(sock):
    header = sock.recv(Protocol.HEADER_SIZE)
    if not header:
        return None, None
    payload_len = Protocol.unpack_header(header)
    payload_bytes = sock.recv(payload_len)
    return Protocol.parse_payload(payload_bytes)

def run_test():
    print("--- 1. Connecting Alice and Bob ---")
    alice_sock = create_client()
    bob_sock = create_client()

    # --- Step 1: Login Alice ---
    alice_sock.sendall(Protocol.pack(MessageType.LOGIN, {"username": "alice"}))
    msg_type, payload = recv_packet(alice_sock)
    print(f"[Alice Login]: {msg_type.value} -> {payload}")

    # --- Step 2: Login Bob ---
    bob_sock.sendall(Protocol.pack(MessageType.LOGIN, {"username": "bob"}))
    msg_type, payload = recv_packet(bob_sock)
    print(f"[Bob Login]:   {msg_type.value} -> {payload}")

    print("\n--- 2. Testing Key Exchange ---")
    # Alice uploads key
    alice_key = "-----BEGIN PUBLIC KEY-----\nFAKE_ALICE_KEY\n-----END PUBLIC KEY-----"
    alice_sock.sendall(Protocol.pack(MessageType.UPLOAD_PUBLIC_KEY, {"public_key": alice_key}))
    msg_type, payload = recv_packet(alice_sock)
    print(f"[Alice Key Upload]: {payload}")

    # Start Bob's background listener now, handling all packet types safely
    def bob_listener():
        while True:
            try:
                msg_type, payload = recv_packet(bob_sock)
                if not msg_type:
                    break
                if msg_type == MessageType.PUBLIC_KEY_RESPONSE:
                    print(f"[Bob Fetch Key Response]: {payload.get('target_user')}'s key is '{payload.get('public_key')}'")
                elif msg_type == MessageType.RELAY_MSG:
                    print(f"[Bob Recv Direct Msg!]: From {payload['sender']}: {payload['encrypted_payload']}")
            except Exception:
                break

    threading.Thread(target=bob_listener, daemon=True).start()
    time.sleep(0.1)

    # Bob requests Alice's public key (bob_listener will receive & print response)
    bob_sock.sendall(Protocol.pack(MessageType.FETCH_PUBLIC_KEY, {"target_user": "alice"}))
    time.sleep(0.2)

    print("\n--- 3. Testing Message Relay ---")
    # Alice sends a message to Bob
    alice_sock.sendall(Protocol.pack(MessageType.SEND_MSG, {
        "recipient": "bob",
        "encrypted_payload": "EncryptedDataPayload123"
    }))

    time.sleep(0.5)

    # Cleanup
    alice_sock.close()
    bob_sock.close()
    print("\n--- Test Finished Successfully! ---")

if __name__ == "__main__":
    run_test()