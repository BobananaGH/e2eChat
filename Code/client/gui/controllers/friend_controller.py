# Code/client/gui/controllers/friend_controller.py

from __future__ import annotations

from PySide6.QtCore import QObject, Signal, QTimer


class FriendController(QObject):
    """
    Coordinates user discovery between the client core
    and FriendView.

    Responsibilities:
        - Request users
        - Receive user updates
        - Expose friend/user state through Qt signals
        - Periodically refresh online/offline state

    Does NOT:
        - Build widgets
        - Send chat messages
        - Perform encryption
        - Handle authentication
        - Implement networking
    """

    friends_changed = Signal(list)
    error_occurred = Signal(str)
    loading_changed = Signal(bool)

    REFRESH_INTERVAL_MS = 2000

    def __init__(
        self,
        client,
        parent=None,
    ):
        super().__init__(parent)

        self.client = client

        self._setup_callbacks()

        # --------------------------------------------------------------
        # ONLINE STATUS REFRESH
        # --------------------------------------------------------------

        self._refresh_timer = QTimer(self)
        self._refresh_timer.setInterval(
            self.REFRESH_INTERVAL_MS
        )
        self._refresh_timer.timeout.connect(
            self._refresh_users
        )

    # ==================================================================
    # CALLBACKS
    # ==================================================================

    def _setup_callbacks(self):
        self.client.friends.on_users_changed = (
            self._on_users_changed
        )

        self.client.friends.on_error = (
            self._on_error
        )

    # ==================================================================
    # FETCH
    # ==================================================================

    def load_friends(self):
        """
        Request the current user list.
        """

        self.loading_changed.emit(True)

        success = self.client.friends.fetch_users()

        if not success:
            self.loading_changed.emit(False)

    # ==================================================================
    # AUTO REFRESH
    # ==================================================================

    def start_refresh(self):
        """
        Start periodically refreshing the user list.

        This keeps online/offline status synchronized
        with the server.
        """

        if not self._refresh_timer.isActive():
            self._refresh_timer.start()

        # Fetch immediately instead of waiting 2 seconds.
        self.load_friends()

    def stop_refresh(self):
        """
        Stop periodic user-list refreshing.
        """

        if self._refresh_timer.isActive():
            self._refresh_timer.stop()

    def _refresh_users(self):
        """
        Refresh the user list if the client is authenticated.
        """

        if not self.client.authenticated:
            return

        self.client.friends.fetch_users()

    # ==================================================================
    # CALLBACK HANDLERS
    # ==================================================================

    def _on_users_changed(
        self,
        users: list[dict],
    ):
        self.friends_changed.emit(
            users
        )

        self.loading_changed.emit(
            False
        )

    def _on_error(
        self,
        message: str,
    ):
        self.loading_changed.emit(
            False
        )

        self.error_occurred.emit(
            message
        )

    # ==================================================================
    # STATE
    # ==================================================================

    def users(self) -> list[dict]:
        return self.client.friends.users()

    # ==================================================================
    # CLEANUP
    # ==================================================================

    def close(self):
        self.stop_refresh()

        if (
            getattr(
                self.client.friends,
                "on_users_changed",
                None,
            )
            == self._on_users_changed
        ):
            self.client.friends.on_users_changed = None

        if (
            getattr(
                self.client.friends,
                "on_error",
                None,
            )
            == self._on_error
        ):
            self.client.friends.on_error = None