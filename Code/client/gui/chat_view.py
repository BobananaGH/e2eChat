# Code/client/gui/chat_view.py
from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QFrame,
)
from PySide6.QtCore import Qt, Signal


class ChatMessageWidget(QFrame):
    """
    Pure UI representation of one chat message.

    Does not send, receive, encrypt, or decrypt anything.
    """

    def __init__(
        self,
        sender: str,
        message: str,
        timestamp: str = "",
        outgoing: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.setObjectName(
            "outgoingMessage"
            if outgoing
            else "incomingMessage"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 7, 10, 7)
        layout.setSpacing(3)

        if not outgoing:
            sender_label = QLabel(sender)
            sender_label.setObjectName("messageSender")
            layout.addWidget(sender_label)

        message_label = QLabel(message)
        message_label.setObjectName("messageText")
        message_label.setWordWrap(True)
        message_label.setTextInteractionFlags(
            Qt.TextSelectableByMouse
        )
        layout.addWidget(message_label)

        if timestamp:
            time_label = QLabel(timestamp)
            time_label.setObjectName("messageTimestamp")
            time_label.setAlignment(
                Qt.AlignRight | Qt.AlignVCenter
            )
            layout.addWidget(time_label)


class ChatView(QWidget):
    """
    Pure UI for displaying and composing a conversation.

    Responsibilities
    ----------------
    - Display active conversation
    - Display message history
    - Display incoming/outgoing messages
    - Handle message input
    - Emit send requests
    - Emit attachment requests
    - Emit typing/input changes
    - Scroll to the latest message

    Does NOT
    --------
    - Send network messages
    - Encrypt or decrypt messages
    - Fetch conversation history
    - Manage threads
    - Manage E2EEClient
    """

    send_requested = Signal(str)
    attachment_requested = Signal()
    typing_changed = Signal(str)

    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._active_user: str | None = None
        self._messages: list[dict] = []

        self._build_ui()

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._build_header(root)
        self._build_messages(root)
        self._build_input(root)

    def _build_header(self, root: QVBoxLayout) -> None:
        self.header = QFrame()
        self.header.setObjectName("chatHeader")

        layout = QHBoxLayout(self.header)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)

        self.avatar_label = QLabel("●")
        self.avatar_label.setObjectName("chatAvatar")
        self.avatar_label.setFixedSize(34, 34)
        self.avatar_label.setAlignment(Qt.AlignCenter)

        user_layout = QVBoxLayout()
        user_layout.setContentsMargins(0, 0, 0, 0)
        user_layout.setSpacing(1)

        self.name_label = QLabel("Select a conversation")
        self.name_label.setObjectName("chatUsername")

        self.status_label = QLabel("")
        self.status_label.setObjectName("chatStatus")

        user_layout.addWidget(self.name_label)
        user_layout.addWidget(self.status_label)

        layout.addWidget(self.avatar_label)
        layout.addLayout(user_layout)
        layout.addStretch()

        root.addWidget(self.header)

    def _build_messages(self, root: QVBoxLayout) -> None:
        self.scroll = QScrollArea()
        self.scroll.setObjectName("chatScroll")
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QScrollArea.NoFrame)

        self.container = QWidget()
        self.container.setObjectName("messageContainer")
        self.container.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Preferred,
        )

        self.message_layout = QVBoxLayout(self.container)
        self.message_layout.setContentsMargins(
            16,
            16,
            16,
            16,
        )
        self.message_layout.setSpacing(8)
        self.message_layout.setAlignment(Qt.AlignTop)

        self.empty_label = QLabel(
            "Select a conversation to start chatting."
        )
        self.empty_label.setObjectName("chatEmpty")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setWordWrap(True)

        self.message_layout.addWidget(self.empty_label)

        self.scroll.setWidget(self.container)

        root.addWidget(self.scroll, 1)

    def _build_input(self, root: QVBoxLayout) -> None:
        self.input_frame = QFrame()
        self.input_frame.setObjectName("chatInputFrame")

        layout = QHBoxLayout(self.input_frame)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        self.attachment_btn = QPushButton("＋")
        self.attachment_btn.setObjectName("attachmentBtn")
        self.attachment_btn.setFixedSize(34, 34)
        self.attachment_btn.setCursor(
            Qt.PointingHandCursor
        )

        self.message_input = QLineEdit()
        self.message_input.setObjectName("messageInput")
        self.message_input.setPlaceholderText(
            "Message..."
        )
        self.message_input.setMinimumHeight(34)

        self.send_btn = QPushButton("Send")
        self.send_btn.setObjectName("sendBtn")
        self.send_btn.setFixedHeight(34)
        self.send_btn.setCursor(
            Qt.PointingHandCursor
        )

        layout.addWidget(self.attachment_btn)
        layout.addWidget(self.message_input, 1)
        layout.addWidget(self.send_btn)

        self.attachment_btn.clicked.connect(
            self.attachment_requested.emit
        )

        self.send_btn.clicked.connect(
            self._on_send_clicked
        )

        self.message_input.returnPressed.connect(
            self._on_send_clicked
        )

        self.message_input.textChanged.connect(
            self._on_text_changed
        )

        root.addWidget(self.input_frame)

    # ------------------------------------------------------------------
    # Conversation
    # ------------------------------------------------------------------

    def set_conversation(
        self,
        username: str,
        status: str = "",
    ) -> None:
        """
        Switch the visible conversation.

        The controller provides the user and existing messages
        separately.
        """

        self._active_user = username

        self.name_label.setText(username)
        self.status_label.setText(status)

        self.clear_messages()

        self.message_input.setEnabled(True)
        self.send_btn.setEnabled(True)
        self.attachment_btn.setEnabled(True)

        self.message_input.setPlaceholderText(
            f"Message {username}..."
        )

    def clear_conversation(self) -> None:
        """Clear the active conversation and return to empty state."""

        self._active_user = None

        self.name_label.setText(
            "Select a conversation"
        )
        self.status_label.setText("")

        self.clear_messages()

        self.message_input.clear()
        self.message_input.setEnabled(False)
        self.send_btn.setEnabled(False)
        self.attachment_btn.setEnabled(False)

        self.message_input.setPlaceholderText(
            "Message..."
        )

    # ------------------------------------------------------------------
    # Messages
    # ------------------------------------------------------------------

    def add_message(
        self,
        sender: str,
        message: str,
        timestamp: str = "",
        outgoing: bool = False,
    ) -> None:
        """
        Add one message to the visible conversation.
        """

        if self.empty_label.isVisible():
            self.empty_label.hide()

        message_widget = ChatMessageWidget(
            sender=sender,
            message=message,
            timestamp=timestamp,
            outgoing=outgoing,
        )

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)

        if outgoing:
            row.addStretch()
            row.addWidget(
                message_widget,
                0,
                Qt.AlignRight,
            )
        else:
            row.addWidget(
                message_widget,
                0,
                Qt.AlignLeft,
            )
            row.addStretch()

        self.message_layout.addLayout(row)

        self._scroll_to_bottom()

    def add_incoming_message(
        self,
        sender: str,
        message: str,
        timestamp: str = "",
    ) -> None:
        """Render a received message."""

        self.add_message(
            sender=sender,
            message=message,
            timestamp=timestamp,
            outgoing=False,
        )

    def add_outgoing_message(
        self,
        message: str,
        timestamp: str = "",
    ) -> None:
        """Render a message sent by the local user."""

        self.add_message(
            sender="You",
            message=message,
            timestamp=timestamp,
            outgoing=True,
        )

    def clear_messages(self) -> None:
        """Remove all visible messages."""

        while self.message_layout.count():
            item = self.message_layout.takeAt(0)

            widget = item.widget()

            if widget is not None:
                widget.deleteLater()
                continue

            layout = item.layout()

            if layout is not None:
                self._clear_layout(layout)

        self.empty_label = QLabel(
            "No messages yet."
        )
        self.empty_label.setObjectName("chatEmpty")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setWordWrap(True)

        self.message_layout.addWidget(
            self.empty_label
        )

    def _clear_layout(self, layout) -> None:
        while layout.count():
            item = layout.takeAt(0)

            widget = item.widget()

            if widget is not None:
                widget.deleteLater()
                continue

            child_layout = item.layout()

            if child_layout is not None:
                self._clear_layout(child_layout)

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------

    def _on_send_clicked(self) -> None:
        text = self.message_input.text().strip()

        if not text:
            return

        if self._active_user is None:
            return

        self.send_requested.emit(text)
        self.message_input.clear()

    def _on_text_changed(self, text: str) -> None:
        self.typing_changed.emit(text)

    def set_input_enabled(self, enabled: bool) -> None:
        self.message_input.setEnabled(enabled)
        self.send_btn.setEnabled(enabled)
        self.attachment_btn.setEnabled(enabled)
        
    def set_status(self, status: str):
        self.status_label.setText(status)
    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def _scroll_to_bottom(self) -> None:
        scrollbar = self.scroll.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def active_user(self) -> str | None:
        return self._active_user

    def focus_input(self) -> None:
        self.message_input.setFocus()
    