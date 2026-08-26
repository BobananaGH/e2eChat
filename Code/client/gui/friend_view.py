# Code/client/gui/friend_view.py

from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSizePolicy,
)
from PySide6.QtCore import Qt, Signal


class FriendView(QWidget):
    """
    Pure UI for displaying and selecting friends.

    Responsibilities
    ----------------
    - Display friend list
    - Display online/offline state
    - Handle friend search
    - Emit friend selection
    - Emit add-friend requests

    Does NOT
    --------
    - Fetch friends
    - Send messages
    - Manage networking
    - Manage E2EE
    - Manage threads
    """

    friend_selected = Signal(str)
    search_changed = Signal(str)
    add_friend_requested = Signal()

    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._friends: dict[str, dict] = {}

        self._build_ui()

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(10)

        self._build_header(root)
        self._build_search(root)
        self._build_friend_list(root)

    def _build_header(self, root: QVBoxLayout) -> None:
        header = QHBoxLayout()
        header.setContentsMargins(10, 10, 10, 0)

        title = QLabel("FRIENDS")
        title.setObjectName("sectionLabel")

        self.add_btn = QPushButton("+")
        self.add_btn.setObjectName("addFriendBtn")
        self.add_btn.setFixedSize(30, 30)
        self.add_btn.setCursor(Qt.PointingHandCursor)

        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.add_btn)

        root.addLayout(header)

        self.add_btn.clicked.connect(
            self.add_friend_requested.emit
        )

    def _build_search(self, root: QVBoxLayout) -> None:
        search_row = QHBoxLayout()
        search_row.setContentsMargins(10, 0, 10, 0)

        search_icon = QLabel("🔍")
        search_icon.setObjectName("searchIcon")

        self.search_bar = QLineEdit()
        self.search_bar.setObjectName("friendSearch")
        self.search_bar.setPlaceholderText(
            "Search friends..."
        )

        search_row.addWidget(search_icon)
        search_row.addWidget(self.search_bar)

        root.addLayout(search_row)

        self.search_bar.textChanged.connect(
            lambda text: self.search_changed.emit(text.strip())
        )

    def _build_friend_list(self, root: QVBoxLayout) -> None:
        self.friend_list = QListWidget()
        self.friend_list.setObjectName("friendList")

        self.friend_list.setSelectionMode(
            QListWidget.SingleSelection
        )

        self.friend_list.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding,
        )

        self.friend_list.itemClicked.connect(
            self._on_friend_clicked
        )

        root.addWidget(self.friend_list)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_friends(
        self,
        friends: list[dict],
    ) -> None:
        """
        Replace the visible friend list.

        Expected friend format:

        {
            "username": str,
            "online": bool,
        }
        """

        self.friend_list.clear()
        self._friends.clear()

        if not friends:
            item = QListWidgetItem(
                "No friends yet"
            )

            item.setFlags(
                item.flags() & ~Qt.ItemIsSelectable
            )

            self.friend_list.addItem(item)
            return

        for friend in friends:
            username = friend["username"]
            online = friend.get("online", False)

            self._friends[username] = friend

            item = self._create_friend_item(
                username,
                online,
            )

            self.friend_list.addItem(item)

    def add_friend(
        self,
        username: str,
        online: bool = False,
    ) -> None:
        """Add one friend to the visible list."""

        if username in self._friends:
            return

        self._friends[username] = {
            "username": username,
            "online": online,
        }

        item = self._create_friend_item(
            username,
            online,
        )

        self.friend_list.addItem(item)

    def remove_friend(
        self,
        username: str,
    ) -> None:
        """Remove a friend from the visible list."""

        self._friends.pop(username, None)

        for index in range(
            self.friend_list.count()
        ):
            item = self.friend_list.item(index)

            if item.data(Qt.UserRole) == username:
                self.friend_list.takeItem(index)
                return

    def set_friend_status(
        self,
        username: str,
        online: bool,
    ) -> None:
        """Update a friend's online state."""

        friend = self._friends.get(username)

        if friend is None:
            return

        friend["online"] = online

        for index in range(
            self.friend_list.count()
        ):
            item = self.friend_list.item(index)

            if item.data(Qt.UserRole) != username:
                continue

            self._render_friend_item(
                item,
                username,
                online,
            )

            return

    def select_friend(
        self,
        username: str,
    ) -> None:
        """Select a friend programmatically."""

        for index in range(
            self.friend_list.count()
        ):
            item = self.friend_list.item(index)

            if item.data(Qt.UserRole) == username:
                self.friend_list.setCurrentItem(item)
                return

    def clear_selection(self) -> None:
        """Clear the current friend selection."""

        self.friend_list.clearSelection()

    def selected_friend(self) -> str | None:
        """Return the currently selected username."""

        item = self.friend_list.currentItem()

        if item is None:
            return None

        return item.data(Qt.UserRole)

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def _create_friend_item(
        self,
        username: str,
        online: bool,
    ) -> QListWidgetItem:
        item = QListWidgetItem()

        item.setData(
            Qt.UserRole,
            username,
        )

        self._render_friend_item(
            item,
            username,
            online,
        )

        return item

    def _render_friend_item(
        self,
        item: QListWidgetItem,
        username: str,
        online: bool,
    ) -> None:
        status = "🟢 Online" if online else "⚫ Offline"

        item.setText(
            f"{username}    {status}"
        )

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _on_friend_clicked(
        self,
        item: QListWidgetItem,
    ) -> None:
        username = item.data(Qt.UserRole)

        if username:
            self.friend_selected.emit(username)