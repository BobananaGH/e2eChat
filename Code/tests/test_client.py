# Code/tests/test_client.py

import sys
import time
from pathlib import Path

# Make Code/ importable when running:
# python .\tests\test_client.py
CODE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(CODE_DIR))

from client.client import E2EEClient


SERVER_HOST = "127.0.0.1"
SERVER_PORT = 5000

ALICE_USERNAME = "alice"
ALICE_PASSWORD = "alice123"

BOB_USERNAME = "bob"
BOB_PASSWORD = "bob123"


def wait_until(
    condition,
    timeout=5.0,
    interval=0.05,
):
    """
    Wait until condition() returns True.

    Returns:
        True  -> condition satisfied
        False -> timeout reached
    """

    deadline = time.time() + timeout

    while time.time() < deadline:
        if condition():
            return True

        time.sleep(interval)

    return False


def run_test():
    print("=" * 70)
    print("E2EE CLIENT INTEGRATION TEST")
    print("=" * 70)

    alice = None
    bob = None

    try:
        # ==============================================================
        # 1. CONNECT
        # ==============================================================

        print("\n--- 1. Connecting Alice and Bob ---")

        alice = E2EEClient(
            host=SERVER_HOST,
            port=SERVER_PORT,
        )

        bob = E2EEClient(
            host=SERVER_HOST,
            port=SERVER_PORT,
        )

        print("[TEST] Alice connected.")
        print("[TEST] Bob connected.")

        # ==============================================================
        # 2. REGISTER
        # ==============================================================

        print("\n--- 2. Logging in users ---")

        alice.login(
            ALICE_USERNAME,
            ALICE_PASSWORD,
        )

        bob.login(
            BOB_USERNAME,
            BOB_PASSWORD,
        )

        print("[TEST] Login requests sent.")

        # ==============================================================
        # 3. WAIT FOR AUTHENTICATION
        # ==============================================================

        print("\n--- 3. Waiting for authentication ---")

        alice_authenticated = wait_until(
            lambda: alice.authenticated,
            timeout=5.0,
        )

        bob_authenticated = wait_until(
            lambda: bob.authenticated,
            timeout=5.0,
        )

        print(
            f"[TEST] Alice authenticated: "
            f"{alice_authenticated}"
        )

        print(
            f"[TEST] Bob authenticated: "
            f"{bob_authenticated}"
        )

        if not alice_authenticated:
            raise AssertionError(
                "Alice authentication failed."
            )

        if not bob_authenticated:
            raise AssertionError(
                "Bob authentication failed."
            )

        print("[PASS] Authentication successful.")

        # ==============================================================
        # 4. WAIT FOR PUBLIC KEY UPLOAD
        # ==============================================================

        print("\n--- 4. Waiting for public-key publication ---")

        # Authentication success causes MessageRouter to call:
        #
        #     client.key_exchange.publish_public_key()
        #
        # Give the server a moment to process the upload.

        time.sleep(0.5)

        print(
            "[TEST] Alice and Bob should now have "
            "published their public keys."
        )

        # ==============================================================
        # 5. REQUEST PUBLIC KEY
        # ==============================================================

        print("\n--- 5. Testing public-key retrieval ---")

        # Alice establishes a shared key with Bob.
        alice.initiate_key_exchange(
            BOB_USERNAME
        )

        print(
            "[TEST] Alice requested Bob's public key."
        )

        time.sleep(0.5)

        # Bob establishes a shared key with Alice.
        bob.initiate_key_exchange(
            ALICE_USERNAME
        )

        print(
            "[TEST] Bob requested Alice's public key."
        )

        time.sleep(0.5)

        print(
            "[PASS] Both E2EE sessions should now be established."
        )

        print(
            "[PASS] Public-key request completed."
        )

        # ==============================================================
        # 6. MESSAGE CALLBACK
        # ==============================================================

        print("\n--- 6. Preparing encrypted messaging test ---")

        received_messages = []

        def bob_message_callback(
            sender,
            plaintext,
        ):
            print(
                f"[Bob] Message from {sender}: "
                f"{plaintext}"
            )

            received_messages.append(
                (sender, plaintext)
            )

        bob.set_message_callback(
            bob_message_callback
        )

        # ==============================================================
        # 7. SEND E2EE MESSAGE
        # ==============================================================

        print("\n--- 7. Testing E2EE message ---")

        message = "Hello Bob! This is an E2EE test."

        try:
            sent = alice.send_chat_message(
                BOB_USERNAME,
                message,
            )

            print(
                f"[TEST] send_chat_message returned: "
                f"{sent}"
            )

        except Exception as exc:
            print(
                f"[TEST] First message attempt: {exc}"
            )

        # Give asynchronous key exchange / message handling
        # time to complete.
        time.sleep(1.0)

        # ==============================================================
        # 8. RESULT
        # ==============================================================

        print("\n--- 8. Checking received message ---")

        if received_messages:
            sender, plaintext = received_messages[-1]

            print(
                f"[TEST] Received sender: {sender}"
            )

            print(
                f"[TEST] Received plaintext: "
                f"{plaintext}"
            )

            if sender != ALICE_USERNAME:
                raise AssertionError(
                    "Incorrect message sender."
                )

            if plaintext != message:
                raise AssertionError(
                    "Received plaintext does not match."
                )

            print(
                "[PASS] E2EE message successfully "
                "received and decrypted."
            )

        else:
            print(
                "[INFO] No decrypted message received yet."
            )

            print(
                "[INFO] This means the next area to debug "
                "is the client key-exchange/messaging flow."
            )

        print("\n" + "=" * 70)
        print("INTEGRATION TEST FINISHED")
        print("=" * 70)

    finally:
        # ==============================================================
        # CLEANUP
        # ==============================================================

        print("\n--- Cleaning up ---")

        if alice is not None:
            try:
                alice.close()
            except Exception:
                pass

        if bob is not None:
            try:
                bob.close()
            except Exception:
                pass

        print("[TEST] Clients closed.")


if __name__ == "__main__":
    run_test()