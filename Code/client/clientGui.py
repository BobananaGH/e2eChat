# Code/client/clientGui.py
import sys
import os

sys.path.insert(
    0,
    os.path.join(os.path.dirname(__file__), ".."),
)

from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QHBoxLayout,
    QFrame,
    QMainWindow,
)

from client.gui.friend_view import FriendView
from client.gui.chat_view import ChatView
from client.gui.login_view import LoginView

from client.gui.controllers.chat_controller import ChatController
from client.gui.controllers.friend_controller import FriendController
from client.gui.controllers.auth_controller import AuthController


class ClientGUI(QMainWindow):
    """
    Main E2EE chat window shown after authentication.

    Responsibilities:
        - Own the main GUI layout
        - Display the friend list
        - Display the active chat
        - Connect FriendView to ChatController
        - Connect ChatController to ChatView
        - Connect FriendController to FriendView

    Does NOT:
        - Handle authentication
        - Perform encryption
        - Manage networking
        - Implement protocol framing
        - Implement TLS
        - Create the E2EEClient
        - Manage background threads
    """

    def __init__(
        self,
        client,
        username: str = "",
        parent=None,
    ):
        super().__init__(parent)

        self.client = client
        self.username = username

        self.setWindowTitle("E2EChat")
        self.setMinimumSize(900, 600)
        self.resize(1100, 700)

        # ==============================================================
        # Controllers
        # ==============================================================

        self.chat_controller = ChatController(
            client=self.client,
            username=self.username,
        )

        self.friend_controller = FriendController(
            client=self.client,
        )

        # ==============================================================
        # UI
        # ==============================================================

        self._build_ui()
        self._wire_signals()
        self._load_styles()

    # ==================================================================
    # Construction
    # ==================================================================

    def _build_ui(self):
        central = QWidget()
        central.setObjectName("mainWindow")
        self.setCentralWidget(central)

        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # --------------------------------------------------------------
        # Friend sidebar
        # --------------------------------------------------------------

        self.friend_view = FriendView()
        self.friend_view.setObjectName("friendView")

        root.addWidget(
            self.friend_view,
            stretch=0,
        )

        # --------------------------------------------------------------
        # Divider
        # --------------------------------------------------------------

        divider = QFrame()
        divider.setFrameShape(QFrame.VLine)
        divider.setObjectName("mainDivider")

        root.addWidget(divider)

        # --------------------------------------------------------------
        # Chat area
        # --------------------------------------------------------------

        self.chat_view = ChatView()
        self.chat_view.setObjectName("chatView")

        root.addWidget(
            self.chat_view,
            stretch=1,
        )

    # ==================================================================
    # Signals
    # ==================================================================

    def _wire_signals(self):

        # --------------------------------------------------------------
        # FriendView → ChatController
        # --------------------------------------------------------------

        self.friend_view.friend_selected.connect(
            self.chat_controller.select_chat
        )

        # --------------------------------------------------------------
        # ChatController → ChatView
        # --------------------------------------------------------------

        self.chat_controller.chat_selected.connect(
            self.chat_view.set_conversation
        )

        self.chat_controller.messages_changed.connect(
            self._on_messages_changed
        )

        self.chat_controller.e2ee_status_changed.connect(
            self.chat_view.set_status
        )

        self.chat_controller.error_occurred.connect(
            self._on_error
        )

        # --------------------------------------------------------------
        # ChatView → ChatController
        # --------------------------------------------------------------

        self.chat_view.send_requested.connect(
            self._on_send_requested
        )

        self.chat_view.typing_changed.connect(
            self._on_typing_changed
        )

        self.chat_view.attachment_requested.connect(
            self._on_attachment_requested
        )

        # --------------------------------------------------------------
        # FriendController → FriendView
        # --------------------------------------------------------------

        self.friend_controller.friends_changed.connect(
            self.friend_view.set_friends
        )

        self.friend_controller.error_occurred.connect(
            self._on_error
        )

        # --------------------------------------------------------------
        # Start friend synchronization
        # --------------------------------------------------------------

        self.friend_controller.start_refresh()

    # ==================================================================
    # Message history
    # ==================================================================

    def _on_messages_changed(
        self,
        messages: list,
    ):
        """
        Render conversation history supplied by ChatController.
        """

        self.chat_view.clear_messages()

        for message in messages:
            sender = message.get(
                "sender",
                "",
            )

            text = message.get(
                "message",
                "",
            )

            outgoing = message.get(
                "outgoing",
                False,
            )

            self.chat_view.add_message(
                sender=sender,
                message=text,
                outgoing=outgoing,
            )

    # ==================================================================
    # Sending
    # ==================================================================

    def _on_send_requested(
        self,
        text: str,
    ):
        """
        Send a message through ChatController.

        ChatController handles:
            - validation
            - E2EE session
            - encryption
            - E2EEClient messaging
            - message history
        """

        recipient = self.chat_controller.current_chat

        if not recipient:
            return

        self.chat_controller.send_message(
            recipient,
            text,
        )

    # ==================================================================
    # Errors
    # ==================================================================

    def _on_error(
        self,
        message: str,
    ):
        """
        Display controller errors in the chat status area.
        """

        self.chat_view.set_status(message)

        print(
            f"[GUI] {message}"
        )

    # ==================================================================
    # Typing
    # ==================================================================

    def _on_typing_changed(
        self,
        text: str,
    ):
        """
        Reserved for future typing indicators.

        No networking is performed here.
        """

        pass

    # ==================================================================
    # Attachments
    # ==================================================================

    def _on_attachment_requested(self):
        """
        Reserved for future attachment support.

        File transfer is intentionally not implemented
        in the current GUI.
        """

        pass

    # ==================================================================
    # Styling
    # ==================================================================

    def _load_styles(self):
        try:
            qss_path = os.path.join(
                os.path.dirname(__file__),
                "clientGui.qss",
            )

            with open(
                qss_path,
                "r",
                encoding="utf-8",
            ) as f:
                self.setStyleSheet(
                    f.read()
                )

        except Exception as exc:
            print(
                "QSS load failed:",
                exc,
            )

    # ==================================================================
    # Friend API
    # ==================================================================

    def set_friends(
        self,
        friends: list[dict],
    ):
        """
        Populate the friend sidebar.
        """

        self.friend_view.set_friends(
            friends
        )

    # ==================================================================
    # Shutdown
    # ==================================================================

    def closeEvent(self, event):
        self.chat_controller.close()
        self.friend_controller.close()
        event.accept()


# ======================================================================
# Application bootstrap
# ======================================================================

class Application:
    """
    Owns the application-wide E2EEClient and GUI lifecycle.

    Flow:

        E2EEClient
            ↓
        AuthController
            ↓
        LoginView
            ↓
        successful authentication
            ↓
        ClientGUI
    """

    def __init__(self):
        self.client = None
        self.auth_controller = None

        self.login_view = None
        self.client_gui = None

    # ==================================================================
    # Start
    # ==================================================================

    def start(self):
        """
        Create the client and show the login screen.
        """

        from client.client import E2EEClient

        self.client = E2EEClient()

        self.auth_controller = AuthController(
            client=self.client,
        )

        self.login_view = LoginView(
            auth_controller=self.auth_controller,
        )

        self.login_view.login_completed.connect(
            self._on_login_completed
        )

        self.login_view.show()

    # ==================================================================
    # Login completed
    # ==================================================================

    def _on_login_completed(self):
        """
        Switch from LoginView to the authenticated chat window.
        """

        username = (
            self.auth_controller.current_username()
        )

        self.client_gui = ClientGUI(
            client=self.client,
            username=username,
        )

        self.client_gui.show()

        self.login_view.close()
        self.login_view.deleteLater()

        self.login_view = None

    # ==================================================================
    # Shutdown
    # ==================================================================

    def shutdown(self):
        """
        Cleanly shut down the application.
        """

        if self.login_view is not None:
            self.login_view.close()
            self.login_view = None

        if self.client_gui is not None:
            self.client_gui.close()
            self.client_gui = None

        if self.auth_controller is not None:
            self.auth_controller.close()
            self.auth_controller = None

        if self.client is not None:
            self.client.close()
            self.client = None


# ======================================================================
# Entry point
# ======================================================================

def main():
    app = QApplication(sys.argv)

    app.setStyle("Fusion")

    application = Application()
    application.start()

    try:
        sys.exit(app.exec())
    finally:
        application.shutdown()


if __name__ == "__main__":
    main()