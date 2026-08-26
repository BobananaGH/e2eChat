# Code/client/gui/dialogs/settings_dialog.py
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QCheckBox,
    QFrame,
)
from PySide6.QtCore import Signal, Qt


class SettingsDialog(QDialog):
    """
    Settings dialog for the E2EE chat client.

    Responsibilities:
        - Display account information
        - Display connection/security status
        - Provide GUI preferences

    This dialog does NOT handle:
        - Networking
        - Authentication
        - Encryption
        - Key exchange
        - Protocol communication
    """

    logout_requested = Signal()
    close_requested = Signal()

    def __init__(
        self,
        username: str = "",
        connected: bool = False,
        authenticated: bool = False,
        parent=None,
    ):
        super().__init__(parent)

        self.username = username
        self.connected = connected
        self.authenticated = authenticated

        self.setWindowTitle(
            "E2EEChat — Settings"
        )

        self.setMinimumWidth(380)

        self._build_ui()
        self._wire_signals()
        self._update_status()

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
            "Settings"
        )

        self.title_label.setObjectName(
            "settingsTitle"
        )

        layout.addWidget(
            self.title_label
        )

        # --------------------------------------------------------------
        # Account
        # --------------------------------------------------------------

        account_frame = QFrame()
        account_frame.setObjectName(
            "settingsSection"
        )

        account_layout = QVBoxLayout(
            account_frame
        )

        account_layout.setContentsMargins(
            16,
            14,
            16,
            14,
        )

        account_title = QLabel(
            "ACCOUNT"
        )

        account_title.setObjectName(
            "settingsSectionTitle"
        )

        account_layout.addWidget(
            account_title
        )

        self.username_label = QLabel(
            "Username: —"
        )

        self.username_label.setObjectName(
            "settingsUsername"
        )

        account_layout.addWidget(
            self.username_label
        )

        layout.addWidget(
            account_frame
        )

        # --------------------------------------------------------------
        # Security
        # --------------------------------------------------------------

        security_frame = QFrame()
        security_frame.setObjectName(
            "settingsSection"
        )

        security_layout = QVBoxLayout(
            security_frame
        )

        security_layout.setContentsMargins(
            16,
            14,
            16,
            14,
        )

        security_title = QLabel(
            "SECURITY"
        )

        security_title.setObjectName(
            "settingsSectionTitle"
        )

        security_layout.addWidget(
            security_title
        )

        self.e2ee_label = QLabel(
            "E2EE: Unknown"
        )

        self.e2ee_label.setObjectName(
            "settingsSecurityStatus"
        )

        security_layout.addWidget(
            self.e2ee_label
        )

        layout.addWidget(
            security_frame
        )

        # --------------------------------------------------------------
        # Preferences
        # --------------------------------------------------------------

        preferences_frame = QFrame()
        preferences_frame.setObjectName(
            "settingsSection"
        )

        preferences_layout = QVBoxLayout(
            preferences_frame
        )

        preferences_layout.setContentsMargins(
            16,
            14,
            16,
            14,
        )

        preferences_title = QLabel(
            "PREFERENCES"
        )

        preferences_title.setObjectName(
            "settingsSectionTitle"
        )

        preferences_layout.addWidget(
            preferences_title
        )

        self.notifications_checkbox = QCheckBox(
            "Enable notifications"
        )

        self.notifications_checkbox.setChecked(
            True
        )

        preferences_layout.addWidget(
            self.notifications_checkbox
        )

        self.enter_to_send_checkbox = QCheckBox(
            "Press Enter to send messages"
        )

        self.enter_to_send_checkbox.setChecked(
            True
        )

        preferences_layout.addWidget(
            self.enter_to_send_checkbox
        )

        layout.addWidget(
            preferences_frame
        )

        # --------------------------------------------------------------
        # Connection status
        # --------------------------------------------------------------

        self.connection_label = QLabel(
            "Connection: Offline"
        )

        self.connection_label.setObjectName(
            "settingsConnectionStatus"
        )

        layout.addWidget(
            self.connection_label
        )

        # --------------------------------------------------------------
        # Buttons
        # --------------------------------------------------------------

        button_layout = QHBoxLayout()

        self.logout_button = QPushButton(
            "Logout"
        )

        self.logout_button.setObjectName(
            "logoutButton"
        )

        self.logout_button.setCursor(
            Qt.PointingHandCursor
        )

        self.close_button = QPushButton(
            "Close"
        )

        self.close_button.setObjectName(
            "closeButton"
        )

        self.close_button.setCursor(
            Qt.PointingHandCursor
        )

        button_layout.addWidget(
            self.logout_button
        )

        button_layout.addStretch()

        button_layout.addWidget(
            self.close_button
        )

        layout.addLayout(
            button_layout
        )

    # ==================================================================
    # SIGNALS
    # ==================================================================

    def _wire_signals(self):
        self.logout_button.clicked.connect(
            self._on_logout_clicked
        )

        self.close_button.clicked.connect(
            self._on_close_clicked
        )

    # ==================================================================
    # ACTIONS
    # ==================================================================

    def _on_logout_clicked(self):
        self.logout_requested.emit()

    def _on_close_clicked(self):
        self.close_requested.emit()
        self.accept()

    # ==================================================================
    # STATUS
    # ==================================================================

    def _update_status(self):
        self.username_label.setText(
            f"Username: {self.username}"
            if self.username
            else "Username: —"
        )

        if self.connected:
            self.connection_label.setText(
                "Connection: Connected"
            )
        else:
            self.connection_label.setText(
                "Connection: Offline"
            )

        if self.authenticated:
            self.e2ee_label.setText(
                "E2EE: Authentication active"
            )
        else:
            self.e2ee_label.setText(
                "E2EE: Not authenticated"
            )

    def set_username(
        self,
        username: str,
    ):
        self.username = username.strip()
        self._update_status()

    def set_connection_status(
        self,
        connected: bool,
    ):
        self.connected = connected
        self._update_status()

    def set_authenticated(
        self,
        authenticated: bool,
    ):
        self.authenticated = authenticated
        self._update_status()

    # ==================================================================
    # PREFERENCES
    # ==================================================================

    def notifications_enabled(self) -> bool:
        return self.notifications_checkbox.isChecked()

    def enter_to_send_enabled(self) -> bool:
        return self.enter_to_send_checkbox.isChecked()

    def set_notifications_enabled(
        self,
        enabled: bool,
    ):
        self.notifications_checkbox.setChecked(
            enabled
        )

    def set_enter_to_send_enabled(
        self,
        enabled: bool,
    ):
        self.enter_to_send_checkbox.setChecked(
            enabled
        )