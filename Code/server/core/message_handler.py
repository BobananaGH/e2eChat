# Code/server/core/message_handler.py
from shared.protocol import MessageType


class MessageHandler:
    """
    Handles encrypted message relay for one
    connected client.

    Responsibilities:
        - Validate message relay requests
        - Find the recipient connection
        - Forward encrypted payloads

    The server NEVER:
        - Decrypts messages
        - Reads plaintext
        - Performs AES-GCM
        - Performs ECDH
        - Derives encryption keys

    The encrypted payload is treated as opaque data.
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
    # MESSAGE RELAY
    # ==================================================================

    def handle_send_message(
        self,
        payload: dict,
    ):
        """
        Relay an encrypted message to the recipient.

        The server NEVER decrypts the payload.
        """

        if not self.current_user:
            self.client_handler.send_auth_required()
            return

        recipient = payload.get(
            "recipient"
        )

        encrypted_payload = payload.get(
            "encrypted_payload"
        )

        if not recipient or not encrypted_payload:
            self.connection.send(
                MessageType.ERROR,
                {
                    "message": (
                        "Recipient and encrypted "
                        "payload are required."
                    )
                },
            )
            return

        with self.server.lock:
            recipient_connection = (
                self.server.active_clients.get(
                    recipient
                )
            )

        if recipient_connection is None:
            self.connection.send(
                MessageType.ERROR,
                {
                    "message": (
                        f"User {recipient} "
                        f"is offline."
                    )
                },
            )
            return

        # --------------------------------------------------------------
        # E2EE RELAY
        # --------------------------------------------------------------
        #
        # The server does NOT decrypt anything.
        #
        # It simply forwards:
        #
        #     sender
        #     encrypted_payload
        #
        # to the recipient.
        # --------------------------------------------------------------

        recipient_connection.send(
            MessageType.RELAY_MSG,
            {
                "sender": self.current_user,
                "encrypted_payload": encrypted_payload,
            },
        )