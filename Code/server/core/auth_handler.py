# Code/server/core/auth_handler.py
from shared.auth import (
    AuthError,
    InvalidUsernameError,
    UserAlreadyExistsError,
)

from shared.protocol import MessageType


class AuthHandler:
    """
    Handles authentication-related requests for
    one connected client.

    Responsibilities:
        - Handle registration
        - Handle login
        - Authenticate credentials
        - Register authenticated connections

    This class does NOT:
        - Perform TLS
        - Perform ECDH
        - Encrypt/decrypt messages
        - Manage TCP framing
    """

    def __init__(self, client_handler):
        self.client_handler = client_handler

    @property
    def server(self):
        return self.client_handler.server

    @property
    def connection(self):
        return self.client_handler.connection

    # ==================================================================
    # REGISTER
    # ==================================================================

    def handle_register(
        self,
        payload: dict,
    ):
        """
        Register a new user through AuthManager.
        """

        username = payload.get("username")
        password = payload.get("password")

        if username is None or password is None:
            self.connection.send(
                MessageType.AUTH_FAIL,
                {
                    "message": (
                        "Username and password "
                        "are required."
                    )
                },
            )
            return

        try:
            self.server.auth_manager.register(
                username,
                password,
            )

        except UserAlreadyExistsError as exc:
            self.connection.send(
                MessageType.AUTH_FAIL,
                {
                    "message": str(exc)
                },
            )
            return

        except (
            InvalidUsernameError,
            ValueError,
        ) as exc:
            self.connection.send(
                MessageType.AUTH_FAIL,
                {
                    "message": str(exc)
                },
            )
            return

        except AuthError as exc:
            self.connection.send(
                MessageType.AUTH_FAIL,
                {
                    "message": str(exc)
                },
            )
            return

        self.client_handler.current_user = (
            self._authenticate_connection(
                username,
                password,
            )
        )

    # ==================================================================
    # LOGIN
    # ==================================================================

    def handle_login(
        self,
        payload: dict,
    ):
        """
        Authenticate an existing user.
        """

        username = payload.get("username")
        password = payload.get("password")

        if username is None or password is None:
            self.connection.send(
                MessageType.AUTH_FAIL,
                {
                    "message": (
                        "Username and password "
                        "are required."
                    )
                },
            )
            return

        self.client_handler.current_user = (
            self._authenticate_connection(
                username,
                password,
            )
        )

    # ==================================================================
    # AUTHENTICATE CONNECTION
    # ==================================================================

    def _authenticate_connection(
        self,
        username: str,
        password: str,
    ):
        """
        Verify credentials and register this
        connection as an active client.
        """

        if not self.server.auth_manager.authenticate(
            username,
            password,
        ):
            self.connection.send(
                MessageType.AUTH_FAIL,
                {
                    "message": (
                        "Invalid username or password."
                    )
                },
            )
            return None

        with self.server.lock:

            existing_connection = (
                self.server.active_clients.get(
                    username
                )
            )

            if existing_connection is not None:
                self.connection.send(
                    MessageType.AUTH_FAIL,
                    {
                        "message": (
                            "User is already logged in."
                        )
                    },
                )
                return None

            self.server.active_clients[
                username
            ] = self.connection

        self.connection.send(
            MessageType.AUTH_SUCCESS,
            {
                "message": (
                    f"Welcome {username}"
                )
            },
        )

        print(
            f"[AUTH] User '{username}' "
            f"authenticated."
        )

        return username