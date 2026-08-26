# Code/client/core/friends.py
from __future__ import annotations

from shared.protocol import MessageType

class FriendManager:
    """
    Manages the user's discovered contacts.

    Responsibilities:
        - Request users from the server
        - Store the current user list
        - Track online/offline state
        - Provide friend lookup

    Does NOT:
        - Build GUI widgets
        - Encrypt messages
        - Handle TLS
        - Handle authentication
        - Implement protocol framing
    """

    def __init__(self, client):
        self.client = client

        self._users: list[dict] = []

        self.on_users_changed = None
        self.on_error = None

    # ==================================================================
    # FETCH
    # ==================================================================

    def fetch_users(self) -> bool:
        """
        Request the current user list from the server.
        """

        if not self.client.authenticated:
            self._emit_error(
                "Authentication required."
            )
            return False

        try:
            self.client._send(
                MessageType.FETCH_USERS,
                {},
            )
            return True

        except Exception as exc:
            self._emit_error(
                f"Failed to fetch users: {exc}"
            )
            return False

    # ==================================================================
    # RESPONSE
    # ==================================================================

    def handle_users_response(
        self,
        payload: dict,
    ) -> None:
        """
        Process USERS_RESPONSE from the router.
        """

        users = payload.get(
            "users",
            [],
        )

        if not isinstance(users, list):
            self._emit_error(
                "Invalid users response."
            )
            return

        normalized = []

        for user in users:
            if not isinstance(user, dict):
                continue

            username = str(
                user.get("username", "")
            ).strip()

            if not username:
                continue

            normalized.append({
                "username": username,
                "online": bool(
                    user.get("online", False)
                ),
            })

        normalized.sort(
            key=lambda user: user["username"].lower()
        )

        self._users = normalized

        if self.on_users_changed:
            self.on_users_changed(
                list(self._users)
            )

    # ==================================================================
    # STATE
    # ==================================================================

    def users(self) -> list[dict]:
        """
        Return a copy of the current users.
        """

        return list(self._users)

    def get_user(
        self,
        username: str,
    ) -> dict | None:
        username = username.strip()

        for user in self._users:
            if user["username"] == username:
                return dict(user)

        return None

    def is_online(
        self,
        username: str,
    ) -> bool:
        user = self.get_user(username)

        if user is None:
            return False

        return user["online"]

    # ==================================================================
    # INTERNAL
    # ==================================================================

    def _emit_error(self, message: str):
        if self.on_error:
            self.on_error(message)