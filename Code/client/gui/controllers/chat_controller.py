# Code/client/gui/controllers/chat_controller.py
from PySide6.QtCore import QObject, Signal


class ChatController(QObject):
    """
    Coordinates the chat GUI with an existing, already-authenticated
    E2EEClient.

    Responsibilities:
        - Connect messaging/key-exchange callbacks to GUI signals
        - Handle chat selection
        - Request E2EE sessions
        - Send encrypted messages, queuing them if no session
          exists yet and flushing once one is established
        - Own per-conversation message history
        - Expose chat/E2EE state

    This class does NOT handle:
        - Authentication
        - Login or registration
        - Creating the E2EEClient
        - GUI layout
        - Qt widget construction
        - Encryption implementation
        - Socket implementation
        - Protocol framing
        - TLS

    The E2EEClient instance is created once by the application
    bootstrap and shared across the authentication and chat layers.
    """

    message_received = Signal(str, str)
    message_sent = Signal(str, str)
    chat_selected = Signal(str)
    messages_changed = Signal(list)
    e2ee_status_changed = Signal(str)
    error_occurred = Signal(str)

    def __init__(
        self,
        client,
        username: str = "",
        parent=None,
    ):
        super().__init__(parent)

        self.client = client
        self.username = username
        self.current_chat = None

        # Per-conversation message history, owned by the controller.
        #
        # {peer_username: [{"sender": str, "message": str, "outgoing": bool}]}
        self._history = {}

        # Plaintext messages typed before an E2EE session existed,
        # waiting to be sent once KeyExchange establishes one.
        #
        # {peer_username: [plaintext, ...]}
        self._pending_outgoing = {}

        self._setup_callbacks()

    # ==================================================================
    # CALLBACKS
    # ==================================================================

    def _setup_callbacks(self):
        """
        Connect E2EEClient messaging/key-exchange callbacks to
        controller signals.

        Messaging performs E2EE decryption before invoking its callback.
        KeyExchange notifies us once a session becomes available, so
        we can flush anything the user tried to send earlier.
        """

        self.client.messaging.on_message_received = (
            self._on_message_received
        )

        self.client.key_exchange.on_session_established = (
            self._on_session_established
        )

    # ==================================================================
    # HISTORY
    # ==================================================================

    def _history_for(self, username: str):
        """
        Return the message list for a conversation,
        creating it if it does not exist yet.
        """

        return self._history.setdefault(username, [])

    # ==================================================================
    # CHAT SELECTION
    # ==================================================================

    def select_chat(
        self,
        username: str,
    ):
        """
        Select a conversation.

        Emits the existing history for that conversation so the
        GUI can render it, and requests an E2EE session if one
        does not already exist.
        """

        username = username.strip()

        if not username:
            self.current_chat = None
            return

        if username == self.username:
            self.error_occurred.emit(
                "Cannot chat with yourself."
            )
            return

        self.current_chat = username

        self.chat_selected.emit(
            username
        )

        self.messages_changed.emit(
            self._history_for(username)
        )

        if self.client.key_exchange.has_session(
            username
        ):
            self.e2ee_status_changed.emit(
                "🔒 E2EE"
            )
            return

        self.request_e2ee_session(
            username
        )

    # ==================================================================
    # MESSAGING
    # ==================================================================

    def send_message(
        self,
        recipient: str,
        plaintext: str,
    ) -> bool:
        """
        Encrypt and send a message, and record it in history.

        If no E2EE session exists yet, the message is queued and
        will be sent automatically once one is established
        (see _on_session_established).

        Returns:
            True  - message was sent immediately.
            False - queued (no session yet) or sending failed.
        """

        recipient = recipient.strip()
        plaintext = plaintext.strip()

        if not recipient:
            self.error_occurred.emit(
                "Recipient cannot be empty."
            )
            return False

        if not plaintext:
            return False

        try:
            success = self.client.messaging.send(
                recipient,
                plaintext,
            )

        except Exception as exc:
            self.error_occurred.emit(
                f"Failed to send message: {exc}"
            )
            return False

        if not success:
            self._pending_outgoing.setdefault(
                recipient, []
            ).append(
                plaintext
            )

            self.e2ee_status_changed.emit(
                "🔒 Establishing E2EE..."
            )
            return False

        self._record_sent(
            recipient,
            plaintext,
        )

        self.e2ee_status_changed.emit(
            "🔒 E2EE"
        )

        return True

    def _record_sent(
        self,
        recipient: str,
        plaintext: str,
    ):
        """
        Record a successfully sent message in history and
        notify the GUI.
        """

        self._history_for(recipient).append({
            "sender": self.username,
            "message": plaintext,
            "outgoing": True,
        })

        self.message_sent.emit(
            recipient,
            plaintext,
        )

        if self.current_chat == recipient:
            self.messages_changed.emit(
                self._history_for(recipient)
            )

    # ==================================================================
    # INCOMING MESSAGES
    # ==================================================================

    def _on_message_received(
        self,
        sender: str,
        plaintext: str,
    ):
        """
        Called by Messaging after successful E2EE decryption.

        Records the message in history and, if the sender is the
        currently open conversation, refreshes the GUI's message list.
        """

        self._history_for(sender).append({
            "sender": sender,
            "message": plaintext,
            "outgoing": False,
        })

        self.message_received.emit(
            sender,
            plaintext,
        )

        if self.current_chat == sender:
            self.messages_changed.emit(
                self._history_for(sender)
            )

    # ==================================================================
    # E2EE STATE
    # ==================================================================

    def has_e2ee_session(
        self,
        username: str,
    ) -> bool:
        """
        Return whether an E2EE session exists
        with the specified user.
        """

        username = username.strip()

        if not username:
            return False

        return self.client.key_exchange.has_session(
            username
        )

    def request_e2ee_session(
        self,
        username: str,
    ):
        """
        Request a peer public key if an E2EE session
        does not already exist.
        """

        username = username.strip()

        if not username:
            return

        if username == self.username:
            self.error_occurred.emit(
                "Cannot establish an E2EE session with yourself."
            )
            return

        if self.has_e2ee_session(
            username
        ):
            self.e2ee_status_changed.emit(
                "🔒 E2EE"
            )
            return

        try:
            self.client.key_exchange.request_public_key(
                username
            )

            self.e2ee_status_changed.emit(
                "🔒 Establishing E2EE..."
            )

        except Exception as exc:
            self.e2ee_status_changed.emit(
                "🔒 E2EE unavailable"
            )

            self.error_occurred.emit(
                f"Key exchange failed: {exc}"
            )

    def _on_session_established(
        self,
        username: str,
    ):
        """
        Called by KeyExchange once a session with `username`
        becomes available. Flushes anything the user tried to
        send before the session existed.
        """

        if self.current_chat == username:
            self.e2ee_status_changed.emit(
                "🔒 E2EE"
            )

        pending = self._pending_outgoing.pop(
            username, []
        )

        for plaintext in pending:
            try:
                success = self.client.messaging.send(
                    username,
                    plaintext,
                )
            except Exception as exc:
                self.error_occurred.emit(
                    f"Failed to send queued message: {exc}"
                )
                continue

            if success:
                self._record_sent(
                    username,
                    plaintext,
                )

    # ==================================================================
    # STATE
    # ==================================================================

    def is_connected(self) -> bool:
        """
        Return whether the underlying E2EEClient currently
        has an active protocol connection.

        This is only a convenience state check. Connection
        lifecycle is owned by E2EEClient, not ChatController.
        """

        return getattr(
            self.client,
            "conn",
            None,
        ) is not None

    def current_username(self) -> str:
        """
        Return the authenticated username associated
        with this chat controller.
        """

        return self.username

    # ==================================================================
    # CLEANUP
    # ==================================================================

    def close(self):
        """
        Detach controller callbacks.

        The shared E2EEClient itself is NOT closed here because
        its lifetime belongs to the application bootstrap.
        """

        if getattr(
            self.client.messaging,
            "on_message_received",
            None,
        ) == self._on_message_received:
            self.client.messaging.on_message_received = None

        if getattr(
            self.client.key_exchange,
            "on_session_established",
            None,
        ) == self._on_session_established:
            self.client.key_exchange.on_session_established = None

        self.current_chat = None