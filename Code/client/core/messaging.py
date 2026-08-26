# Code/client/core/messaging.py

from shared.protocol import MessageType


class Messaging:
    """
    Handles E2EE chat messages.

    Encryption and decryption are performed by E2EECrypto.
    This class handles the messaging workflow and protocol.

    Session establishment is one-sided: whoever fetches a peer's
    public key first gets a session immediately. A message can
    therefore arrive from a peer we have no session with yet -
    the normal case the first time anyone messages us. Rather than
    fail, that message is buffered here and automatically decrypted
    once KeyExchange reactively fetches the sender's key and a
    session is established (see flush_pending, called from
    KeyExchange.handle_public_key).
    """

    def __init__(self, client):
        self.client = client

        # Optional callback used by the GUI.
        #
        # callback(sender, plaintext)
        self.on_message_received = None

        # Encrypted messages received from a peer we don't yet
        # have a session with.
        #
        # {sender: [encrypted_payload, ...]}
        self._pending = {}

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

        If no session exists with the sender yet - the normal case
        for the first message from someone who messaged us before
        we messaged them - the message is buffered and the sender's
        public key is requested. KeyExchange calls flush_pending
        once that session is ready.
        """

        if not self.client.key_exchange.has_session(
            sender
        ):
            print(
                f"[E2EE] No session with '{sender}' yet - "
                f"buffering message and requesting their key."
            )

            self._pending.setdefault(
                sender, []
            ).append(
                encrypted_payload
            )

            try:
                self.client.key_exchange.request_public_key(
                    sender
                )
            except Exception as exc:
                print(
                    f"[E2EE] Failed to request key for "
                    f"'{sender}': {exc}"
                )

            return

        self._decrypt_and_deliver(
            sender,
            encrypted_payload,
        )

    def flush_pending(
        self,
        username: str,
    ):
        """
        Decrypt and deliver any messages that were buffered
        while waiting for a session with `username`.

        Called by KeyExchange once that session is established.
        """

        pending = self._pending.pop(
            username, []
        )

        for encrypted_payload in pending:
            try:
                self._decrypt_and_deliver(
                    username,
                    encrypted_payload,
                )
            except Exception as exc:
                print(
                    f"[E2EE] Failed to decrypt buffered "
                    f"message from '{username}': {exc}"
                )

    def _decrypt_and_deliver(
        self,
        sender: str,
        encrypted_payload: dict,
    ):
        """
        Decrypt one message using an existing session and
        hand the plaintext to the GUI/application.
        """

        session = (
            self.client.key_exchange.get_session(
                sender
            )
        )

        plaintext = session.decrypt_message(
            encrypted_payload["nonce"],
            encrypted_payload["ciphertext"],
        )

        if self.on_message_received:
            self.on_message_received(
                sender,
                plaintext,
            )
        else:
            print(
                f"\n[{sender} -> ME]: {plaintext}"
            )