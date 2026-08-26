# Code/client/clientGui.py

import sys
import os

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QFrame,
    QScrollArea,
    QSizePolicy,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from client.client import E2EEClient


class MessageBubble(QFrame):
    """
    Visual representation of one chat message.
    """

    def __init__(
        self,
        sender: str,
        message: str,
        outgoing: bool = False,
        parent=None,
    ):
        super().__init__(parent)

        self.setObjectName(
            "outgoingMessage"
            if outgoing
            else "incomingMessage"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(3)

        sender_label = QLabel(sender)
        sender_label.setObjectName("messageSender")

        message_label = QLabel(message)
        message_label.setObjectName("messageText")
        message_label.setWordWrap(True)
        message_label.setTextInteractionFlags(
            Qt.TextSelectableByMouse
        )

        layout.addWidget(sender_label)
        layout.addWidget(message_label)

        self.setSizePolicy(
            QSizePolicy.Maximum,
            QSizePolicy.Minimum,
        )


class ChatWindow(QMainWindow):
    """
    Main E2EE chat GUI.

    Responsibilities:
        - Display users/chats
        - Display conversation history
        - Send messages through E2EEClient
        - Display incoming decrypted messages
        - Manage GUI state

    Encryption/networking remains inside the client/core layer.
    """

    def __init__(
        self,
        username: str = "",
        password: str = "",
    ):
        super().__init__()

        self.username = username
        self.password = password

        self.current_chat = None
        self.chat_history = {}

        self.client = E2EEClient()

        self.setWindowTitle("E2EEChat")
        self.setMinimumSize(900, 600)
        self.resize(1200, 750)

        self._build_ui()
        self._wire_signals()
        self._load_styles()
        self._setup_client_callbacks()

    # ==================================================================
    # UI BUILDING
    # ==================================================================

    def _build_ui(self):
        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)

        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # --------------------------------------------------------------
        # LEFT SIDEBAR
        # --------------------------------------------------------------

        self.sidebar = QWidget()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(280)

        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        # App header
        app_header = QWidget()
        app_header.setObjectName("appHeader")

        app_header_layout = QHBoxLayout(app_header)
        app_header_layout.setContentsMargins(
            20,
            18,
            20,
            18,
        )

        app_title = QLabel("E2EEChat")
        app_title.setObjectName("appTitle")

        app_header_layout.addWidget(app_title)
        app_header_layout.addStretch()

        sidebar_layout.addWidget(app_header)

        # Search
        search_container = QWidget()
        search_layout = QVBoxLayout(search_container)
        search_layout.setContentsMargins(
            14,
            8,
            14,
            12,
        )

        self.search_input = QLineEdit()
        self.search_input.setObjectName("searchInput")
        self.search_input.setPlaceholderText(
            "Search conversations..."
        )

        search_layout.addWidget(self.search_input)

        sidebar_layout.addWidget(search_container)

        # Direct messages label
        section_label = QLabel("DIRECT MESSAGES")
        section_label.setObjectName("sectionLabel")

        section_wrapper = QWidget()
        section_wrapper_layout = QHBoxLayout(
            section_wrapper
        )
        section_wrapper_layout.setContentsMargins(
            18,
            8,
            18,
            4,
        )

        section_wrapper_layout.addWidget(section_label)
        section_wrapper_layout.addStretch()

        sidebar_layout.addWidget(section_wrapper)

        # Chat list
        self.chat_list = QListWidget()
        self.chat_list.setObjectName("chatList")
        self.chat_list.setFrameShape(QFrame.NoFrame)

        sidebar_layout.addWidget(
            self.chat_list,
            stretch=1,
        )

        # Account panel
        self.account_panel = QWidget()
        self.account_panel.setObjectName("accountPanel")

        account_layout = QHBoxLayout(
            self.account_panel
        )
        account_layout.setContentsMargins(
            14,
            12,
            14,
            12,
        )

        self.account_status = QLabel()
        self.account_status.setObjectName(
            "accountStatus"
        )

        account_text_layout = QVBoxLayout()
        account_text_layout.setSpacing(1)

        self.account_name = QLabel(
            self.username or "User"
        )
        self.account_name.setObjectName(
            "accountName"
        )

        self.account_state = QLabel("Offline")
        self.account_state.setObjectName(
            "accountState"
        )

        account_text_layout.addWidget(
            self.account_name
        )
        account_text_layout.addWidget(
            self.account_state
        )

        account_layout.addWidget(
            self.account_status
        )
        account_layout.addLayout(
            account_text_layout
        )
        account_layout.addStretch()

        self.settings_button = QPushButton("⚙")
        self.settings_button.setObjectName(
            "settingsButton"
        )
        self.settings_button.setFixedSize(
            36,
            36,
        )

        account_layout.addWidget(
            self.settings_button
        )

        sidebar_layout.addWidget(
            self.account_panel
        )

        # --------------------------------------------------------------
        # RIGHT CHAT AREA
        # --------------------------------------------------------------

        self.chat_area = QWidget()
        self.chat_area.setObjectName("chatArea")

        chat_layout = QVBoxLayout(self.chat_area)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        chat_layout.setSpacing(0)

        # Chat header
        self.chat_header = QWidget()
        self.chat_header.setObjectName(
            "chatHeader"
        )

        header_layout = QHBoxLayout(
            self.chat_header
        )
        header_layout.setContentsMargins(
            22,
            14,
            22,
            14,
        )

        self.chat_avatar = QLabel("●")
        self.chat_avatar.setObjectName(
            "chatAvatar"
        )
        self.chat_avatar.setFixedWidth(25)

        header_text = QVBoxLayout()
        header_text.setSpacing(1)

        self.chat_username = QLabel(
            "Select a conversation"
        )
        self.chat_username.setObjectName(
            "chatUsername"
        )

        self.chat_status = QLabel("")
        self.chat_status.setObjectName(
            "chatStatus"
        )

        header_text.addWidget(
            self.chat_username
        )
        header_text.addWidget(
            self.chat_status
        )

        header_layout.addWidget(
            self.chat_avatar
        )
        header_layout.addLayout(
            header_text
        )
        header_layout.addStretch()

        self.e2ee_indicator = QLabel(
            "🔒 E2EE"
        )
        self.e2ee_indicator.setObjectName(
            "e2eeIndicator"
        )

        header_layout.addWidget(
            self.e2ee_indicator
        )

        self.chat_menu_button = QPushButton("⋮")
        self.chat_menu_button.setObjectName(
            "chatMenuButton"
        )
        self.chat_menu_button.setFixedSize(
            36,
            36,
        )

        header_layout.addWidget(
            self.chat_menu_button
        )

        chat_layout.addWidget(
            self.chat_header
        )

        # --------------------------------------------------------------
        # MESSAGE AREA
        # --------------------------------------------------------------

        self.message_scroll = QScrollArea()
        self.message_scroll.setObjectName(
            "messageScroll"
        )
        self.message_scroll.setWidgetResizable(
            True
        )
        self.message_scroll.setFrameShape(
            QFrame.NoFrame
        )

        self.message_container = QWidget()
        self.message_container.setObjectName(
            "messageContainer"
        )

        self.message_layout = QVBoxLayout(
            self.message_container
        )

        self.message_layout.setContentsMargins(
            24,
            20,
            24,
            20,
        )
        self.message_layout.setSpacing(10)

        self.message_layout.addStretch()

        self.message_scroll.setWidget(
            self.message_container
        )

        chat_layout.addWidget(
            self.message_scroll,
            stretch=1,
        )

        # --------------------------------------------------------------
        # MESSAGE INPUT
        # --------------------------------------------------------------

        input_container = QWidget()
        input_container.setObjectName(
            "inputContainer"
        )

        input_layout = QHBoxLayout(
            input_container
        )

        input_layout.setContentsMargins(
            18,
            12,
            18,
            16,
        )
        input_layout.setSpacing(8)

        self.attach_button = QPushButton("+")
        self.attach_button.setObjectName(
            "attachButton"
        )
        self.attach_button.setFixedSize(
            42,
            42,
        )

        self.message_input = QLineEdit()
        self.message_input.setObjectName(
            "messageInput"
        )
        self.message_input.setPlaceholderText(
            "Type a message..."
        )
        self.message_input.setMinimumHeight(
            42
        )

        self.send_button = QPushButton("➤")
        self.send_button.setObjectName(
            "sendButton"
        )
        self.send_button.setFixedSize(
            42,
            42,
        )
        self.send_button.setEnabled(False)

        input_layout.addWidget(
            self.attach_button
        )
        input_layout.addWidget(
            self.message_input,
            stretch=1,
        )
        input_layout.addWidget(
            self.send_button
        )

        chat_layout.addWidget(
            input_container
        )

        # --------------------------------------------------------------
        # ROOT
        # --------------------------------------------------------------

        root.addWidget(self.sidebar)
        root.addWidget(
            self.chat_area,
            stretch=1,
        )

    # ==================================================================
    # SIGNALS
    # ==================================================================

    def _wire_signals(self):
        self.chat_list.itemClicked.connect(
            self._on_chat_selected
        )

        self.message_input.textChanged.connect(
            self._on_message_text_changed
        )

        self.message_input.returnPressed.connect(
            self._send_message
        )

        self.send_button.clicked.connect(
            self._send_message
        )

    # ==================================================================
    # CLIENT CALLBACKS
    # ==================================================================

    def _setup_client_callbacks(self):
        """
        Connect the existing Messaging callback
        to the GUI.

        Messaging decrypts the message before
        this callback receives it.
        """

        self.client.messaging.on_message_received = (
            self._on_message_received
        )

    # ==================================================================
    # CHAT MANAGEMENT
    # ==================================================================

    def add_chat(
        self,
        username: str,
        status: str = "Online",
    ):
        """
        Add a user to the sidebar.
        """

        # Avoid duplicate entries.
        for index in range(
            self.chat_list.count()
        ):
            item = self.chat_list.item(index)

            if item.data(
                Qt.UserRole
            ) == username:
                return

        item = QListWidgetItem()

        item.setData(
            Qt.UserRole,
            username,
        )

        widget = QWidget()

        layout = QHBoxLayout(widget)
        layout.setContentsMargins(
            12,
            8,
            12,
            8,
        )
        layout.setSpacing(10)

        avatar = QLabel("●")
        avatar.setObjectName(
            "userStatus"
        )
        avatar.setFixedWidth(18)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(1)

        name = QLabel(username)
        name.setObjectName(
            "chatListName"
        )

        state = QLabel(status)
        state.setObjectName(
            "chatListStatus"
        )

        text_layout.addWidget(name)
        text_layout.addWidget(state)

        layout.addWidget(avatar)
        layout.addLayout(text_layout)
        layout.addStretch()

        item.setSizeHint(
            widget.sizeHint()
        )

        self.chat_list.addItem(item)
        self.chat_list.setItemWidget(
            item,
            widget,
        )

        self.chat_history.setdefault(
            username,
            [],
        )

    def _on_chat_selected(
        self,
        item: QListWidgetItem,
    ):
        username = item.data(
            Qt.UserRole
        )

        if not username:
            return

        self.current_chat = username

        self.chat_username.setText(
            username
        )
        self.chat_status.setText(
            "Online"
        )

        self.message_input.setPlaceholderText(
            f"Message {username}..."
        )

        self._refresh_messages()

        # If we do not already have a session,
        # request the peer public key.
        if not self.client.key_exchange.has_session(
            username
        ):
            try:
                self.client.key_exchange.request_public_key(
                    username
                )

                self.e2ee_indicator.setText(
                    "🔒 Establishing E2EE..."
                )

            except Exception as exc:
                print(
                    f"[GUI] Key exchange failed: {exc}"
                )

        else:
            self.e2ee_indicator.setText(
                "🔒 E2EE"
            )

    # ==================================================================
    # MESSAGE HANDLING
    # ==================================================================

    def _send_message(self):
        if not self.current_chat:
            return

        plaintext = (
            self.message_input.text().strip()
        )

        if not plaintext:
            return

        try:
            success = (
                self.client.messaging.send(
                    self.current_chat,
                    plaintext,
                )
            )

            if not success:
                self.e2ee_indicator.setText(
                    "🔒 Establishing E2EE..."
                )
                return

            self._add_message(
                sender=self.username,
                message=plaintext,
                outgoing=True,
            )

            self.message_input.clear()

            self.e2ee_indicator.setText(
                "🔒 E2EE"
            )

        except Exception as exc:
            print(
                f"[GUI] Failed to send message: "
                f"{exc}"
            )

    def _on_message_received(
        self,
        sender: str,
        plaintext: str,
    ):
        """
        Called by Messaging after successful
        E2EE decryption.
        """

        self._add_message(
            sender=sender,
            message=plaintext,
            outgoing=False,
        )

        if sender == self.current_chat:
            self.e2ee_indicator.setText(
                "🔒 E2EE"
            )

    def _add_message(
        self,
        sender: str,
        message: str,
        outgoing: bool = False,
    ):
        if not sender:
            return

        self.chat_history.setdefault(
            sender,
            [],
        )

        self.chat_history[sender].append(
            {
                "sender": sender,
                "message": message,
                "outgoing": outgoing,
            }
        )

        if sender == self.current_chat:
            self._refresh_messages()

    def _refresh_messages(self):
        # Remove existing widgets except the stretch.
        while self.message_layout.count() > 1:
            item = self.message_layout.takeAt(0)

            widget = item.widget()

            if widget:
                widget.deleteLater()

        if not self.current_chat:
            return

        messages = self.chat_history.get(
            self.current_chat,
            [],
        )

        for message_data in messages:
            bubble = MessageBubble(
                sender=message_data["sender"],
                message=message_data["message"],
                outgoing=message_data["outgoing"],
            )

            row = QWidget()

            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(
                0,
                0,
                0,
                0,
            )

            if message_data["outgoing"]:
                row_layout.addStretch()
                row_layout.addWidget(bubble)
            else:
                row_layout.addWidget(bubble)
                row_layout.addStretch()

            self.message_layout.insertWidget(
                self.message_layout.count() - 1,
                row,
            )

        self._scroll_to_bottom()

    def _scroll_to_bottom(self):
        scrollbar = (
            self.message_scroll.verticalScrollBar()
        )

        scrollbar.setValue(
            scrollbar.maximum()
        )

    # ==================================================================
    # INPUT STATE
    # ==================================================================

    def _on_message_text_changed(
        self,
        text: str,
    ):
        self.send_button.setEnabled(
            bool(
                text.strip()
                and self.current_chat
            )
        )

    # ==================================================================
    # STYLING
    # ==================================================================

    def _load_styles(self):
        qss_path = os.path.join(
            os.path.dirname(__file__),
            "clientGui.qss",
        )

        try:
            with open(
                qss_path,
                "r",
                encoding="utf-8",
            ) as file:
                self.setStyleSheet(
                    file.read()
                )

        except FileNotFoundError:
            print(
                f"[GUI] QSS file not found: "
                f"{qss_path}"
            )

        except Exception as exc:
            print(
                f"[GUI] Failed to load QSS: "
                f"{exc}"
            )

    # ==================================================================
    # WINDOW LIFECYCLE
    # ==================================================================

    def closeEvent(self, event):
        try:
            self.client.close()
        except Exception as exc:
            print(
                f"[GUI] Client close error: "
                f"{exc}"
            )

        event.accept()


# ======================================================================
# APPLICATION ENTRY POINT
# ======================================================================

def main():
    app = QApplication(sys.argv)

    app.setStyle("Fusion")

    window = ChatWindow()

    # Demo users for the initial UI.
    #
    # Remove these once your server/user-list
    # functionality is implemented.
    window.add_chat(
        "bob",
        "Online",
    )

    window.add_chat(
        "charlie",
        "Offline",
    )

    window.add_chat(
        "david",
        "Online",
    )

    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()