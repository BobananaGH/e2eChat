# Code/client/core/messaging.py

from shared.protocol import MessageType


class Messaging:
    """
    Handles E2EE chat messages.

    Encryption and decryption are performed by E2EECrypto.
    This class handles the messaging workflow and protocol.
    """

    def __init__(self, client):
        self.client = client

        # Optional callback used by the GUI.
        #
        # callback(sender, plaintext)
        self.on_message_received = None

    def send(
        self,
        recipient: str,
        plaintext: str,
    ) -> bool:
        """
        Encrypt and send a message to a recipient.

        Returns:
            True  - message was encrypted and sent.
            False - no shared key exists yet.
        """

        recipient = recipient.strip()

        if not recipient:
            raise ValueError(
                "Recipient cannot be empty."
            )

        if not plaintext:
            raise ValueError(
                "Message cannot be empty."
            )

        # --------------------------------------------------------------
        # Make sure an E2EE session exists.
        # --------------------------------------------------------------

        if not self.client.key_exchange.has_session(
            recipient
        ):
            print(
                f"[E2EE] No shared key with "
                f"'{recipient}'."
            )

            self.client.key_exchange.request_public_key(
                recipient
            )

            return False

        # --------------------------------------------------------------
        # Encrypt locally.
        #
        # The server NEVER receives plaintext.
        # --------------------------------------------------------------

        session = (
            self.client.key_exchange.get_session(
                recipient
            )
        )

        encrypted_payload = (
            session.encrypt_message(plaintext)
        )

        # --------------------------------------------------------------
        # Send ciphertext through the server.
        # --------------------------------------------------------------

        self.client._send(
            MessageType.SEND_MSG,
            {
                "recipient": recipient,
                "encrypted_payload": encrypted_payload,
            },
        )

        return True

    def handle_received(
        self,
        sender: str,
        encrypted_payload: dict,
    ):
        """
        Decrypt an incoming E2EE message.
        """

        # --------------------------------------------------------------
        # Find the E2EE session for this sender.
        # --------------------------------------------------------------

        session = (
            self.client.key_exchange.get_session(
                sender
            )
        )

        # --------------------------------------------------------------
        # Decrypt locally.
        #
        # Only the recipient has the E2EE session key.
        # --------------------------------------------------------------

        plaintext = session.decrypt_message(
            encrypted_payload["nonce"],
            encrypted_payload["ciphertext"],
        )

        # --------------------------------------------------------------
        # Give plaintext to the GUI/application.
        # --------------------------------------------------------------

        if self.on_message_received:
            self.on_message_received(
                sender,
                plaintext,
            )
        else:
            print(
                f"\n[{sender} -> ME]: {plaintext}"
            )