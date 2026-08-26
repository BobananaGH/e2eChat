# Code/client/gui/dialogs/register_dialog.py
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
)
from PySide6.QtCore import Signal, Qt


class RegisterDialog(QDialog):
    """
    Registration dialog for the E2EE chat client.

    Responsibilities:
        - Collect username
        - Collect password
        - Confirm password
        - Emit registration request
        - Display registration errors

    This dialog does NOT handle:
        - Networking
        - Protocol messages
        - Authentication logic
        - Encryption
        - Key exchange
    """

    register_requested = Signal(str, str)
    login_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("E2EEChat — Register")
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

        self.title_label = QLabel(
            "Create an account"
        )
        self.title_label.setObjectName(
            "registerTitle"
        )

        self.subtitle_label = QLabel(
            "Create your E2EEChat account"
        )
        self.subtitle_label.setObjectName(
            "registerSubtitle"
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
            "Choose a username"
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
            "Choose a password"
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
        # Confirm password
        # --------------------------------------------------------------

        self.confirm_password_label = QLabel(
            "Confirm password"
        )

        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setObjectName(
            "confirmPasswordInput"
        )
        self.confirm_password_input.setPlaceholderText(
            "Re-enter your password"
        )
        self.confirm_password_input.setEchoMode(
            QLineEdit.Password
        )

        layout.addWidget(
            self.confirm_password_label
        )

        layout.addWidget(
            self.confirm_password_input
        )

        # --------------------------------------------------------------
        # Error
        # --------------------------------------------------------------

        self.error_label = QLabel("")
        self.error_label.setObjectName(
            "registerError"
        )
        self.error_label.setWordWrap(True)
        self.error_label.hide()

        layout.addWidget(
            self.error_label
        )

        # --------------------------------------------------------------
        # Register button
        # --------------------------------------------------------------

        self.register_button = QPushButton(
            "Create Account"
        )

        self.register_button.setObjectName(
            "registerButton"
        )

        self.register_button.setCursor(
            Qt.PointingHandCursor
        )

        self.register_button.setDefault(
            True
        )

        layout.addWidget(
            self.register_button
        )

        # --------------------------------------------------------------
        # Login
        # --------------------------------------------------------------

        login_layout = QHBoxLayout()

        login_label = QLabel(
            "Already have an account?"
        )

        self.login_button = QPushButton(
            "Login"
        )

        self.login_button.setObjectName(
            "loginButton"
        )

        self.login_button.setCursor(
            Qt.PointingHandCursor
        )

        login_layout.addWidget(
            login_label
        )

        login_layout.addWidget(
            self.login_button
        )

        login_layout.addStretch()

        layout.addLayout(
            login_layout
        )

    # ==================================================================
    # SIGNALS
    # ==================================================================

    def _wire_signals(self):
        self.register_button.clicked.connect(
            self._on_register_clicked
        )

        self.login_button.clicked.connect(
            self.login_requested.emit
        )

        self.confirm_password_input.returnPressed.connect(
            self._on_register_clicked
        )

    # ==================================================================
    # REGISTER
    # ==================================================================

    def _on_register_clicked(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()
        confirm_password = (
            self.confirm_password_input.text()
        )

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

        if not confirm_password:
            self.show_error(
                "Please confirm your password."
            )
            self.confirm_password_input.setFocus()
            return

        if password != confirm_password:
            self.show_error(
                "Passwords do not match."
            )
            self.confirm_password_input.setFocus()
            return

        self.clear_error()

        self.set_loading(True)

        self.register_requested.emit(
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
        self.username_input.setEnabled(
            not loading
        )

        self.password_input.setEnabled(
            not loading
        )

        self.confirm_password_input.setEnabled(
            not loading
        )

        self.register_button.setEnabled(
            not loading
        )

        self.login_button.setEnabled(
            not loading
        )

        self.register_button.setText(
            "Creating account..."
            if loading
            else "Create Account"
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

    def reset(self):
        self.clear_error()
        self.set_loading(False)

        self.password_input.clear()
        self.confirm_password_input.clear()