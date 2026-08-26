# Code/client/core/router.py
from shared.protocol import MessageType


class MessageRouter:
    """
    Routes incoming protocol messages to the appropriate
    client subsystem.

    Responsibilities:
        - Handle authentication responses
        - Handle public-key responses
        - Handle incoming encrypted messages
        - Handle generic server responses

    This class does NOT implement:
        - Authentication
        - ECDH
        - Encryption/decryption
        - Protocol framing
        - Socket communication
    """

    def __init__(self, client):
        self.client = client

    # ==================================================================
    # MAIN ROUTER
    # ==================================================================

    def handle(
        self,
        message_type: MessageType,
        payload: dict,
    ):
        """
        Route an incoming protocol message.
        """

        if message_type == MessageType.AUTH_SUCCESS:
            self._handle_auth_success(payload)

        elif message_type == MessageType.AUTH_FAIL:
            self._handle_auth_fail(payload)

        elif message_type == MessageType.PUBLIC_KEY_RESPONSE:
            self._handle_public_key_response(payload)

        elif message_type == MessageType.RELAY_MSG:
            self._handle_relay_message(payload)

        elif message_type == MessageType.SUCCESS:
            self._handle_success(payload)

        elif message_type == MessageType.ERROR:
            self._handle_error(payload)

        else:
            print(
                f"[CLIENT] Unhandled message type: "
                f"{message_type}"
            )

    # ==================================================================
    # AUTHENTICATION
    # ==================================================================

    def _handle_auth_success(self, payload: dict):
        """
        Handle successful authentication.

        Once authenticated, publish our public ECDH key.
        """

        self.client.authenticated = True

        print(
            f"[AUTH] "
            f"{payload.get(
                'message',
                'Authentication successful.',
            )}"
        )

        try:
            self.client.key_exchange.publish_public_key()

        except Exception as exc:
            print(
                f"[E2EE] Failed to publish public key: "
                f"{exc}"
            )

    def _handle_auth_fail(self, payload: dict):
        """
        Handle failed authentication.
        """

        self.client.authenticated = False

        print(
            f"[AUTH FAILED] "
            f"{payload.get(
                'message',
                'Authentication failed.',
            )}"
        )

    # ==================================================================
    # KEY EXCHANGE
    # ==================================================================

    def _handle_public_key_response(self, payload: dict):
        """
        Handle a public-key response from the server.
        """

        target_username = payload.get(
            "target_user"
        )

        public_key = payload.get(
            "public_key"
        )

        if not target_username or not public_key:
            print(
                "[E2EE] Invalid public-key response."
            )
            return

        try:
            self.client.key_exchange.handle_public_key(
                target_username,
                public_key,
            )

        except Exception as exc:
            print(
                f"[E2EE] Key exchange failed: "
                f"{exc}"
            )

    # ==================================================================
    # MESSAGING
    # ==================================================================

    def _handle_relay_message(self, payload: dict):
        """
        Handle an incoming encrypted chat message.
        """

        sender = payload.get("sender")

        encrypted_payload = payload.get(
            "encrypted_payload"
        )

        if not sender or not encrypted_payload:
            print(
                "[MESSAGE] Invalid relay message."
            )
            return

        try:
            self.client.messaging.handle_received(
                sender,
                encrypted_payload,
            )

        except Exception as exc:
            print(
                f"[E2EE] Message decryption failed: "
                f"{exc}"
            )

    # ==================================================================
    # SERVER RESPONSES
    # ==================================================================

    def _handle_success(self, payload: dict):
        """
        Handle a generic successful server response.
        """

        print(
            f"[SERVER] "
            f"{payload.get(
                'details',
                'Success',
            )}"
        )

    def _handle_error(self, payload: dict):
        """
        Handle a generic server error.
        """

        print(
            f"[SERVER ERROR] "
            f"{payload.get(
                'message',
                'Unknown error',
            )}"
        )