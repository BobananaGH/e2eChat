# Code/client/gui/controllers/auth_controller.py

from PySide6.QtCore import QObject, Signal


class AuthController(QObject):
    """
    Coordinates authentication actions for the client GUI.

    Responsibilities:
        - Request login
        - Request registration
        - Receive authentication results from E2EEClient
        - Emit GUI-friendly authentication signals, distinguishing
          which action (login vs register) they resulted from
        - Track the username currently being authenticated

    This class does NOT handle:
        - Credential validation
        - User storage
        - Authentication logic
        - TLS
        - Encryption
        - Protocol framing
        - Socket communication
        - Creating the E2EEClient
        - Client connection lifecycle

    The E2EEClient instance is created once by the
    application bootstrap and shared across the
    authentication and chat layers.

    Note: the server authenticates a connection as part of
    REGISTER itself (registering also logs you in), so a
    successful registration and a successful login arrive over
    the wire as the exact same AUTH_SUCCESS message. This
    controller tracks which action is pending so it can still
    emit the signal that matches what the GUI actually asked for.
    """

    login_success = Signal(str)
    login_failed = Signal(str)

    register_success = Signal(str)
    register_failed = Signal(str)

    authentication_changed = Signal(bool)

    def __init__(
        self,
        client,
        parent=None,
    ):
        super().__init__(parent)

        self.client = client
        self.username = ""

        # "login" or "register" - whichever action is currently
        # awaiting a server response. Needed because AUTH_SUCCESS/
        # AUTH_FAIL don't distinguish the two on the wire.
        self._pending_action = None

        # Receive authentication results from
        # E2EEClient / MessageRouter.
        self.client.on_auth_result = (
            self._on_auth_result
        )

    # ==================================================================
    # LOGIN
    # ==================================================================

    def login(
        self,
        username: str,
        password: str,
    ):
        """
        Request login through the shared E2EEClient.

        The server response is handled asynchronously
        by MessageRouter and forwarded through
        E2EEClient.on_auth_result.
        """

        username = username.strip()

        if not username or not password:
            self.login_failed.emit(
                "Username and password are required."
            )
            return

        self.username = username
        self._pending_action = "login"

        try:
            self.client.login(
                username,
                password,
            )

        except Exception as exc:
            self._pending_action = None
            self.login_failed.emit(
                str(exc)
            )

    # ==================================================================
    # REGISTER
    # ==================================================================

    def register(
        self,
        username: str,
        password: str,
    ):
        """
        Request registration through the shared E2EEClient.

        Registration is asynchronous. The server response is
        received by E2EEClient and routed by MessageRouter.

        The server authenticates the connection as part of
        registering, so a successful response here means the
        account was created AND the session is authenticated -
        no separate login call is needed afterwards.
        """

        username = username.strip()

        if not username or not password:
            self.register_failed.emit(
                "Username and password are required."
            )
            return

        self.username = username
        self._pending_action = "register"

        try:
            self.client.register(
                username,
                password,
            )

        except Exception as exc:
            self._pending_action = None
            self.register_failed.emit(
                str(exc)
            )

    # ==================================================================
    # AUTHENTICATION RESULT
    # ==================================================================

    def _on_auth_result(
        self,
        success: bool,
        message: str,
    ):
        """
        Receive authentication results from E2EEClient.

        This callback is invoked by MessageRouter through
        E2EEClient.on_auth_result, on the client's listener
        thread, so GUI code is reached only through Qt signals.
        """

        action = self._pending_action
        self._pending_action = None

        self.authentication_changed.emit(
            success
        )

        if action == "register":
            if success:
                self.register_success.emit(message)
            else:
                self.register_failed.emit(message)
        else:
            if success:
                self.login_success.emit(message)
            else:
                self.login_failed.emit(message)

    # ==================================================================
    # STATE
    # ==================================================================

    def set_username(
        self,
        username: str,
    ):
        """
        Store the username currently being authenticated.
        """

        self.username = username.strip()

    def current_username(self) -> str:
        """
        Return the username associated with this
        authentication controller.
        """

        return (
            getattr(
                self.client,
                "username",
                None,
            )
            or self.username
        )

    def is_authenticated(self) -> bool:
        """
        Return whether the shared E2EEClient
        is currently authenticated.
        """

        return bool(
            getattr(
                self.client,
                "authenticated",
                False,
            )
        )

    # ==================================================================
    # LOGOUT
    # ==================================================================

    def logout(self):
        """
        Clear local authentication state.

        The current protocol has no LOGOUT message,
        so this only resets local authentication state.

        The shared E2EEClient connection itself is NOT
        closed here.
        """

        self.client.authenticated = False
        self.username = ""

        self.authentication_changed.emit(
            False
        )

    # ==================================================================
    # CLEANUP
    # ==================================================================

    def close(self):
        """
        Detach this controller from the shared E2EEClient.

        The E2EEClient itself is NOT closed here because
        its lifetime belongs to the application bootstrap.
        """

        callback = getattr(
            self.client,
            "on_auth_result",
            None,
        )

        if callback == self._on_auth_result:
            self.client.on_auth_result = None