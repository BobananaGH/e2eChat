# Code/client/core/key_exchange.py

from shared.protocol import MessageType

from client.core.crypto import E2EECrypto


class KeyExchange:
    """
    Handles the E2EE key-exchange workflow.

    E2EECrypto performs the actual ECDH/HKDF operations.
    This class manages which peer uses which derived session key.

    Session establishment is one-directional by nature: whichever
    side fetches a peer's public key first is the one that creates
    the session locally. The other side gets its own session
    independently, the first time it needs one for that peer -
    either because it also sends a message, or because it receives
    one first (see Messaging.handle_received, which now triggers a
    key fetch automatically on an unknown sender instead of failing).

    This class does NOT:
        - Buffer messages (that's Messaging's job)
        - Decide when to reactively fetch a key on receipt
    """

    def __init__(self, client):
        self.client = client

        # {username: E2EECrypto}
        self.peers = {}

        # Optional callback, set by ChatController.
        #
        # callback(username)
        #
        # Fired once a session with `username` becomes available,
        # whether we requested the key ourselves or Messaging
        # requested it reactively after an unknown sender's message.
        self.on_session_established = None

    def publish_public_key(self):
        """Upload our ECDH public key to the server."""

        self.client._send(
            MessageType.UPLOAD_PUBLIC_KEY,
            {
                "public_key":
                    self.client.crypto.get_public_bytes_b64()
            }
        )

    def request_public_key(
        self,
        target_username: str
    ):
        """Request a peer's ECDH public key."""

        target_username = target_username.strip()

        if not target_username:
            raise ValueError(
                "Target username cannot be empty."
            )

        if target_username == self.client.username:
            raise ValueError(
                "Cannot exchange a key with yourself."
            )

        self.client._send(
            MessageType.FETCH_PUBLIC_KEY,
            {
                "target_user": target_username
            }
        )

    def handle_public_key(
        self,
        target_username: str,
        public_key: str
    ):
        """
        Create a per-peer E2EE session and derive
        the shared AES key using ECDH.

        Also flushes any inbound messages Messaging buffered
        while waiting for this session, and notifies whoever
        is waiting to flush outbound messages.
        """

        session = E2EECrypto()

        # Use our existing identity private key.
        session.private_key = (
            self.client.crypto.private_key
        )

        session.public_key = (
            self.client.crypto.public_key
        )

        # ECDH → shared secret → HKDF → AES key
        session.generate_shared_key(
            public_key
        )

        self.peers[target_username] = session

        print(
            f"[E2EE] Shared key established "
            f"with '{target_username}'."
        )

        # Deliver any messages that arrived before this session existed.
        self.client.messaging.flush_pending(
            target_username
        )

        if self.on_session_established:
            self.on_session_established(
                target_username
            )

    def has_session(self, username: str) -> bool:
        return username in self.peers

    def get_session(self, username: str) -> E2EECrypto:
        session = self.peers.get(username)

        if session is None:
            raise ValueError(
                f"No E2EE session with '{username}'."
            )

        return session