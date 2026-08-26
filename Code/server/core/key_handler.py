# Code/server/core/key_handler.py
from shared.protocol import MessageType


class KeyHandler:
    """
    Handles E2EE public-key operations for one
    connected client.

    Responsibilities:
        - Store public ECDH keys
        - Fetch public ECDH keys

    The server never receives or stores private keys.

    This class does NOT:
        - Perform ECDH
        - Derive shared secrets
        - Encrypt messages
        - Decrypt messages
    """

    def __init__(self, client_handler):
        self.client_handler = client_handler

    @property
    def server(self):
        return self.client_handler.server

    @property
    def connection(self):
        return self.client_handler.connection

    @property
    def current_user(self):
        return self.client_handler.current_user

    # ==================================================================
    # PUBLIC KEY UPLOAD
    # ==================================================================

    def handle_upload_public_key(
        self,
        payload: dict,
    ):
        """
        Store the authenticated user's public ECDH key.
        """

        if not self.current_user:
            self.client_handler.send_auth_required()
            return

        public_key = payload.get(
            "public_key"
        )

        if not public_key:
            self.connection.send(
                MessageType.ERROR,
                {
                    "message": (
                        "Public key is required."
                    )
                },
            )
            return

        with self.server.lock:
            self.server.public_keys[
                self.current_user
            ] = public_key

        self.connection.send(
            MessageType.SUCCESS,
            {
                "details": "Key stored"
            },
        )

        print(
            f"[E2EE] Public key stored "
            f"for '{self.current_user}'."
        )

    # ==================================================================
    # PUBLIC KEY FETCH
    # ==================================================================

    def handle_fetch_public_key(
        self,
        payload: dict,
    ):
        """
        Return another user's public ECDH key.
        """

        if not self.current_user:
            self.client_handler.send_auth_required()
            return

        target_user = payload.get(
            "target_user"
        )

        if not target_user:
            self.connection.send(
                MessageType.ERROR,
                {
                    "message": (
                        "Target username is required."
                    )
                },
            )
            return

        with self.server.lock:
            public_key = (
                self.server.public_keys.get(
                    target_user
                )
            )

        if public_key:
            self.connection.send(
                MessageType.PUBLIC_KEY_RESPONSE,
                {
                    "target_user": target_user,
                    "public_key": public_key,
                },
            )

        else:
            self.connection.send(
                MessageType.ERROR,
                {
                    "message": (
                        "User or public key not found."
                    )
                },
            )