# Code/server/core/client_handler.py
from shared.protocol import Connection, MessageType

from server.core.auth_handler import AuthHandler
from server.core.key_handler import KeyHandler
from server.core.message_handler import MessageHandler
from server.core.user_handler import UserHandler


class ClientHandler:
    """
    Handles one connected client.

    Responsibilities:
        - Receive protocol messages
        - Route messages to the appropriate handler
        - Manage connection lifecycle
        - Clean up disconnected clients

    Client-specific operations are delegated to:
        - AuthHandler
        - KeyHandler
        - MessageHandler

    This class does NOT perform:
        - TLS configuration
        - TCP framing
        - ECDH
        - AES-GCM encryption/decryption
        - Plaintext message processing
    """

    def __init__(
        self,
        server,
        sock,
        addr,
    ):
        self.server = server
        self.sock = sock
        self.addr = addr

        self.connection = Connection(sock)

        # Username authenticated on this connection.
        self.current_user = None

        # --------------------------------------------------------------
        # SUB-HANDLERS
        # --------------------------------------------------------------

        self.auth_handler = AuthHandler(self)
        self.key_handler = KeyHandler(self)
        self.message_handler = MessageHandler(self)
        self.user_handler = UserHandler(self)

    # ==================================================================
    # MAIN HANDLER
    # ==================================================================

    def handle(self):
        """
        Handle this client until the connection closes.
        """

        print(
            f"[CONNECTED] Client connected "
            f"from {self.addr}"
        )

        try:
            while True:
                message = self.connection.recv()

                if message is None:
                    break

                message_type, payload = message

                self._route_message(
                    message_type,
                    payload,
                )

        except (
            ConnectionResetError,
            BrokenPipeError,
            OSError,
        ):
            pass

        except Exception as exc:
            print(
                f"[SERVER] Client handler error "
                f"for {self.addr}: {exc}"
            )

        finally:
            self._cleanup()

    # ==================================================================
    # MESSAGE ROUTING
    # ==================================================================

    def _route_message(
        self,
        message_type: MessageType,
        payload: dict,
    ):
        """
        Route an incoming protocol message
        to the appropriate handler.
        """

        if message_type == MessageType.REGISTER:
            self.auth_handler.handle_register(
                payload
            )

        elif message_type == MessageType.LOGIN:
            self.auth_handler.handle_login(
                payload
            )

        elif message_type == MessageType.UPLOAD_PUBLIC_KEY:
            self.key_handler.handle_upload_public_key(
                payload
            )

        elif message_type == MessageType.FETCH_PUBLIC_KEY:
            self.key_handler.handle_fetch_public_key(
                payload
            )

        elif message_type == MessageType.SEND_MSG:
            self.message_handler.handle_send_message(
                payload
            )
            
        elif message_type == MessageType.FETCH_USERS:
            self.user_handler.handle_fetch_users(
                payload
            )
            
        else:
            self.connection.send(
                MessageType.ERROR,
                {
                    "message": (
                        "Unsupported message type."
                    )
                },
            )

    # ==================================================================
    # AUTH REQUIRED
    # ==================================================================

    def send_auth_required(self):
        """
        Tell the client that authentication is required.
        """

        self.connection.send(
            MessageType.AUTH_FAIL,
            {
                "message": (
                    "Authentication required."
                )
            },
        )

    # ==================================================================
    # CLEANUP
    # ==================================================================

    def _cleanup(self):
        """
        Remove this client from the server's active
        connection table and close the connection.
        """

        if self.current_user:
            with self.server.lock:

                current = (
                    self.server.active_clients.get(
                        self.current_user
                    )
                )

                # Only remove this connection if it is
                # still the active connection for the user.
                if current is self.connection:
                    del self.server.active_clients[
                        self.current_user
                    ]

        try:
            self.connection.close()

        except OSError:
            pass

        print(
            f"[DISCONNECTED] "
            f"{self.current_user or self.addr}"
        )