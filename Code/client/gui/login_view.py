# Code/client/gui/login_view.py
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class LoginView(QWidget):
    """
    GUI for user authentication.

    Responsibilities:
        - Display username and password fields
        - Request login through AuthController
        - Request registration through AuthController
        - Display authentication errors
        - Notify the application when login succeeds

    This class does NOT handle:
        - Authentication logic
        - Credential validation
        - Networking
        - TLS
        - Encryption
        - Protocol framing
        - Creating E2EEClient
    """

    login_completed = Signal()

    def __init__(
        self,
        auth_controller,
        parent=None,
    ):
        super().__init__(parent)

        self.auth_controller = auth_controller

        self._build_ui()
        self._setup_connections()

    # ==================================================================
    # UI
    # ==================================================================

    def _build_ui(self):
        """
        Build the login interface.
        """

        self.setWindowTitle("E2EE Chat - Login")
        self.setMinimumWidth(400)

        main_layout = QVBoxLayout(self)

        main_layout.setContentsMargins(
            40,
            40,
            40,
            40,
        )

        main_layout.setSpacing(15)

        # --------------------------------------------------------------
        # TITLE
        # --------------------------------------------------------------

        title = QLabel("E2EE Chat")

        title.setObjectName("title")

        title.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        subtitle = QLabel(
            "End-to-End Encrypted Messaging"
        )

        subtitle.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        main_layout.addWidget(title)
        main_layout.addWidget(subtitle)

        # --------------------------------------------------------------
        # FORM
        # --------------------------------------------------------------

        form_frame = QFrame()

        form_layout = QVBoxLayout(
            form_frame
        )

        form_layout.setSpacing(10)

        username_label = QLabel(
            "Username"
        )

        self.username_input = QLineEdit()

        self.username_input.setPlaceholderText(
            "Enter username"
        )

        password_label = QLabel(
            "Password"
        )

        self.password_input = QLineEdit()

        self.password_input.setPlaceholderText(
            "Enter password"
        )

        self.password_input.setEchoMode(
            QLineEdit.EchoMode.Password
        )

        form_layout.addWidget(
            username_label
        )

        form_layout.addWidget(
            self.username_input
        )

        form_layout.addWidget(
            password_label
        )

        form_layout.addWidget(
            self.password_input
        )

        main_layout.addWidget(
            form_frame
        )

        # --------------------------------------------------------------
        # BUTTONS
        # --------------------------------------------------------------

        button_layout = QHBoxLayout()

        self.login_button = QPushButton(
            "Login"
        )

        self.register_button = QPushButton(
            "Register"
        )

        button_layout.addWidget(
            self.login_button
        )

        button_layout.addWidget(
            self.register_button
        )

        main_layout.addLayout(
            button_layout
        )

        # --------------------------------------------------------------
        # STATUS
        # --------------------------------------------------------------

        self.status_label = QLabel("")

        self.status_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.status_label.setWordWrap(True)

        main_layout.addWidget(
            self.status_label
        )

        main_layout.addStretch()

    # ==================================================================
    # CONNECTIONS
    # ==================================================================

    def _setup_connections(self):
        """
        Connect GUI events to controller actions.
        """

        self.login_button.clicked.connect(
            self._on_login_clicked
        )

        self.register_button.clicked.connect(
            self._on_register_clicked
        )

        self.password_input.returnPressed.connect(
            self._on_login_clicked
        )

        self.auth_controller.login_success.connect(
            self._on_login_success
        )

        self.auth_controller.login_failed.connect(
            self._on_login_failed
        )

        self.auth_controller.register_success.connect(
            self._on_register_success
        )

        self.auth_controller.register_failed.connect(
            self._on_register_failed
        )

    # ==================================================================
    # LOGIN
    # ==================================================================

    def _on_login_clicked(self):
        """
        Request login through AuthController.
        """

        username = self.username_input.text()
        password = self.password_input.text()

        if not username.strip() or not password:
            self._show_status(
                "Username and password are required."
            )
            return

        self._set_loading(True)

        self._show_status(
            "Logging in..."
        )

        self.auth_controller.login(
            username,
            password,
        )

    # ==================================================================
    # REGISTER
    # ==================================================================

    def _on_register_clicked(self):
        """
        Request registration through AuthController.
        """

        username = self.username_input.text()
        password = self.password_input.text()

        if not username.strip() or not password:
            self._show_status(
                "Username and password are required."
            )
            return

        self._set_loading(True)

        self._show_status(
            "Registering..."
        )

        self.auth_controller.register(
            username,
            password,
        )

    # ==================================================================
    # LOGIN RESULT
    # ==================================================================

    def _on_login_success(
        self,
        message: str,
    ):
        """
        Handle successful login.
        """

        self._set_loading(False)

        self._show_status(
            message
        )

        self.login_completed.emit()

    def _on_login_failed(
        self,
        message: str,
    ):
        """
        Handle failed login.
        """

        self._set_loading(False)

        self._show_status(
            message
        )

    # ==================================================================
    # REGISTER RESULT
    # ==================================================================

    def _on_register_success(
        self,
        message: str,
    ):
        """
        Handle successful registration.

        Registration also authenticates the connection on the
        server, so a successful registration is equivalent to
        completing authentication. The application can therefore
        proceed directly to ClientGUI without requiring
        a second login.
        """

        self._set_loading(False)

        self._show_status(
            message
        )

        self.login_completed.emit()

    def _on_register_failed(
        self,
        message: str,
    ):
        """
        Handle failed registration.
        """

        self._set_loading(False)

        self._show_status(
            message
        )

        QMessageBox.warning(
            self,
            "Registration Failed",
            message,
        )

    # ==================================================================
    # UI STATE
    # ==================================================================

    def _set_loading(
        self,
        loading: bool,
    ):
        """
        Enable or disable authentication controls.
        """

        self.username_input.setEnabled(
            not loading
        )

        self.password_input.setEnabled(
            not loading
        )

        self.login_button.setEnabled(
            not loading
        )

        self.register_button.setEnabled(
            not loading
        )

    def _show_status(
        self,
        message: str,
    ):
        """
        Display a status message.
        """

        self.status_label.setText(
            message
        )

    # ==================================================================
    # CLEANUP
    # ==================================================================

    def close(self):
        """
        Disconnect controller callbacks.

        The AuthController itself is not closed here.
        """

        try:
            self.auth_controller.login_success.disconnect(
                self._on_login_success
            )
        except (TypeError, RuntimeError):
            pass

        try:
            self.auth_controller.login_failed.disconnect(
                self._on_login_failed
            )
        except (TypeError, RuntimeError):
            pass

        try:
            self.auth_controller.register_success.disconnect(
                self._on_register_success
            )
        except (TypeError, RuntimeError):
            pass

        try:
            self.auth_controller.register_failed.disconnect(
                self._on_register_failed
            )
        except (TypeError, RuntimeError):
            pass