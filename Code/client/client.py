# Code/client/client.py

import threading

from shared.protocol import Connection, MessageType

from client.core.crypto import E2EECrypto
from client.core.key_exchange import KeyExchange
from client.core.messaging import Messaging
from client.core.router import MessageRouter
from client.core.friends import FriendManager
from client.tls import TLSConnection


class E2EEClient:
    """
    High-level E2EE chat client.

    Responsibilities:
        - Establish the client TLS connection
        - Manage the protocol connection
        - Run the receiver thread
        - Track authentication state
        - Expose the public client API
        - Coordinate client core modules

    This class does NOT implement:
        - Password hashing/authentication
        - TLS implementation
        - Protocol framing
        - ECDH implementation
        - AES-GCM implementation
        - Message encryption/decryption
        - Incoming message routing
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 5000,
        timeout: float = 10.0,
    ):
        self.host = host
        self.port = port
        self.username = None
        self.authenticated = False
        self.on_auth_result = None
        self.running = False

        # --------------------------------------------------------------
        # E2EE CORE
        # --------------------------------------------------------------
        self.crypto = E2EECrypto()
        self.key_exchange = KeyExchange(self)
        self.messaging = Messaging(self)
        self.friends = FriendManager(self)
        # --------------------------------------------------------------
        # MESSAGE ROUTER
        # --------------------------------------------------------------
        self.router = MessageRouter(self)

        # --------------------------------------------------------------
        # TLS CONNECTION
        # --------------------------------------------------------------
        self.tls = TLSConnection(
            self.host,
            self.port,
            timeout,
        )

        # --------------------------------------------------------------
        # PROTOCOL CONNECTION
        # --------------------------------------------------------------
        self.conn = Connection(
            self.tls.socket
        )

        # --------------------------------------------------------------
        # RECEIVER THREAD
        # --------------------------------------------------------------
        self.running = True
        self._listener_thread = threading.Thread(
            target=self._listen_loop,
            daemon=True,
        )
        self._listener_thread.start()

    # ==================================================================
    # INTERNAL SEND
    # ==================================================================

    def _send(
        self,
        message_type: MessageType,
        payload: dict,
    ):
        """
        Send one protocol message.

        Used internally by client core modules.
        """

        if not self.running:
            raise RuntimeError(
                "Client is not connected."
            )

        self.conn.send(
            message_type,
            payload,
        )

    # ==================================================================
    # LISTENER
    # ==================================================================

    def _listen_loop(self):
        """
        Continuously receive messages from the server.

        Connection handles:
            - TCP framing
            - exact reads
            - protocol serialization
            - protocol parsing

        MessageRouter handles:
            - authentication responses
            - public-key responses
            - encrypted messages
            - server responses
        """

        while self.running:
            try:
                message = self.conn.recv()

                if message is None:
                    break

                message_type, payload = message

                self.router.handle(
                    message_type,
                    payload,
                )

            except (
                ConnectionResetError,
                BrokenPipeError,
                OSError,
            ) as exc:
                print(
                    f"[CLIENT] Listener socket error: "
                    f"{type(exc).__name__}: {exc}"
                )
                break

            except Exception as exc:
                print(
                    f"[CLIENT] Listener error: {exc}"
                )
                break

        self.running = False

        print("[CLIENT] Connection closed.")

    # ==================================================================
    # AUTHENTICATION
    # ==================================================================

    def register(
        self,
        username: str,
        password: str,
    ):
        """
        Request registration.

        Authentication is performed by the server.
        """

        username = username.strip()

        if not username:
            raise ValueError(
                "Username cannot be empty."
            )

        self.username = username

        self._send(
            MessageType.REGISTER,
            {
                "username": username,
                "password": password,
            },
        )

    def login(
        self,
        username: str,
        password: str,
    ):
        """
        Request login.

        Authentication is performed by the server.
        """

        username = username.strip()

        if not username:
            raise ValueError(
                "Username cannot be empty."
            )

        self.username = username

        self._send(
            MessageType.LOGIN,
            {
                "username": username,
                "password": password,
            },
        )

    # ==================================================================
    # KEY EXCHANGE
    # ==================================================================

    def initiate_key_exchange(
        self,
        target_username: str,
    ):
        """
        Request another user's public ECDH key.
        """

        if not self.authenticated:
            raise RuntimeError(
                "Authenticate before starting key exchange."
            )

        return self.key_exchange.request_public_key(
            target_username
        )

    # ==================================================================
    # MESSAGING
    # ==================================================================

    def send_chat_message(
        self,
        target_username: str,
        plaintext: str,
    ) -> bool:
        """
        Send an E2EE encrypted chat message.

        Messaging handles:
            - session lookup
            - encryption
            - key exchange initiation
            - SEND_MSG construction
        """

        if not self.authenticated:
            raise RuntimeError(
                "Authenticate before sending messages."
            )

        return self.messaging.send(
            target_username,
            plaintext,
        )

    # ==================================================================
    # CALLBACK
    # ==================================================================

    def set_message_callback(
        self,
        callback,
    ):
        """
        Set the callback invoked after a message is
        successfully decrypted.

        Callback signature:

            callback(sender, plaintext)
        """

        self.messaging.on_message_received = callback

    # ==================================================================
    # SHUTDOWN
    # ==================================================================

    def close(self):
        """
        Close the client connection.
        """

        if not self.running:
            return

        self.running = False

        try:
            self.conn.close()
        except OSError:
            pass

        print("[CLIENT] Closed.")