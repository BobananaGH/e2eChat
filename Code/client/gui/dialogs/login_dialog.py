# Code/client/gui/dialogs/login_dialog.py
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
)
from PySide6.QtCore import Signal, Qt


class LoginDialog(QDialog):
    """
    Login dialog for the E2EE chat client.

    Responsibilities:
        - Collect username
        - Collect password
        - Emit login request
        - Display authentication errors

    This dialog does NOT handle:
        - Networking
        - Protocol messages
        - Authentication logic
        - Encryption
        - Key exchange
    """

    login_requested = Signal(str, str)
    register_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("E2EEChat — Login")
        self.setMinimumWidth(360)

        self._build_ui()
        self._wire_signals()

    # ==================================================================
    # UI
    # ==================================================================

    def _build_ui(self):
        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            28,
            28,
            28,
            28,
        )

        layout.setSpacing(12)

        # --------------------------------------------------------------
        # Title
        # --------------------------------------------------------------

        self.title_label = QLabel("Welcome back")
        self.title_label.setObjectName(
            "loginTitle"
        )

        self.subtitle_label = QLabel(
            "Sign in to E2EEChat"
        )
        self.subtitle_label.setObjectName(
            "loginSubtitle"
        )

        layout.addWidget(
            self.title_label
        )

        layout.addWidget(
            self.subtitle_label
        )

        layout.addSpacing(12)

        # --------------------------------------------------------------
        # Username
        # --------------------------------------------------------------

        self.username_label = QLabel(
            "Username"
        )

        self.username_input = QLineEdit()
        self.username_input.setObjectName(
            "usernameInput"
        )
        self.username_input.setPlaceholderText(
            "Enter your username"
        )

        layout.addWidget(
            self.username_label
        )

        layout.addWidget(
            self.username_input
        )

        # --------------------------------------------------------------
        # Password
        # --------------------------------------------------------------

        self.password_label = QLabel(
            "Password"
        )

        self.password_input = QLineEdit()
        self.password_input.setObjectName(
            "passwordInput"
        )
        self.password_input.setPlaceholderText(
            "Enter your password"
        )
        self.password_input.setEchoMode(
            QLineEdit.Password
        )

        layout.addWidget(
            self.password_label
        )

        layout.addWidget(
            self.password_input
        )

        # --------------------------------------------------------------
        # Error
        # --------------------------------------------------------------

        self.error_label = QLabel("")
        self.error_label.setObjectName(
            "loginError"
        )
        self.error_label.setWordWrap(True)
        self.error_label.hide()

        layout.addWidget(
            self.error_label
        )

        # --------------------------------------------------------------
        # Login button
        # --------------------------------------------------------------

        self.login_button = QPushButton(
            "Login"
        )

        self.login_button.setObjectName(
            "loginButton"
        )

        self.login_button.setCursor(
            Qt.PointingHandCursor
        )

        self.login_button.setDefault(
            True
        )

        layout.addWidget(
            self.login_button
        )

        # --------------------------------------------------------------
        # Register
        # --------------------------------------------------------------

        register_layout = QHBoxLayout()

        register_label = QLabel(
            "Don't have an account?"
        )

        self.register_button = QPushButton(
            "Register"
        )

        self.register_button.setObjectName(
            "registerButton"
        )

        self.register_button.setCursor(
            Qt.PointingHandCursor
        )

        register_layout.addWidget(
            register_label
        )

        register_layout.addWidget(
            self.register_button
        )

        register_layout.addStretch()

        layout.addLayout(
            register_layout
        )

    # ==================================================================
    # SIGNALS
    # ==================================================================

    def _wire_signals(self):
        self.login_button.clicked.connect(
            self._on_login_clicked
        )

        self.register_button.clicked.connect(
            self.register_requested.emit
        )

        self.password_input.returnPressed.connect(
            self._on_login_clicked
        )

    # ==================================================================
    # LOGIN
    # ==================================================================

    def _on_login_clicked(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username:
            self.show_error(
                "Username is required."
            )
            self.username_input.setFocus()
            return

        if not password:
            self.show_error(
                "Password is required."
            )
            self.password_input.setFocus()
            return

        self.clear_error()

        self.set_loading(True)

        self.login_requested.emit(
            username,
            password,
        )

    # ==================================================================
    # STATE
    # ==================================================================

    def set_loading(
        self,
        loading: bool,
    ):
        """
        Enable/disable controls while authentication
        is being processed.
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

        self.login_button.setText(
            "Logging in..."
            if loading
            else "Login"
        )

    # ==================================================================
    # ERRORS
    # ==================================================================

    def show_error(
        self,
        message: str,
    ):
        self.error_label.setText(
            message
        )

        self.error_label.show()

        self.set_loading(False)

    def clear_error(self):
        self.error_label.clear()
        self.error_label.hide()

    # ==================================================================
    # PUBLIC API
    # ==================================================================

    def username(self) -> str:
        return self.username_input.text().strip()

    def password(self) -> str:
        return self.password_input.text()

    def clear_password(self):
        self.password_input.clear()

    def reset(self):
        """
        Reset the dialog to its initial state.
        """

        self.clear_error()
        self.set_loading(False)
        self.password_input.clear()