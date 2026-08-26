# Code/server/core/user_handler.py

from shared.protocol import MessageType


class UserHandler:
    """
    Handles user discovery requests.

    Responsibilities:
        - Return registered users
        - Report online/offline state

    This handler does NOT:
        - Authenticate users
        - Encrypt messages
        - Manage TLS
        - Perform E2EE
        - Handle TCP framing
    """

    def __init__(self, client_handler):
        self.client_handler = client_handler

    @property
    def server(self):
        return self.client_handler.server

    @property
    def connection(self):
        return self.client_handler.connection

    @property
    def current_user(self):
        return self.client_handler.current_user

    # ==================================================================
    # FETCH USERS
    # ==================================================================

    def handle_fetch_users(self, payload: dict):
        """
        Return all registered users except the requesting user.

        Online state comes from server.active_clients.
        """

        if not self.current_user:
            self.client_handler.send_auth_required()
            return

        # --------------------------------------------------------------
        # GET REGISTERED USERS FROM SQLITE
        # --------------------------------------------------------------

        usernames = (
            self.server.auth_manager.get_usernames()
        )

        # --------------------------------------------------------------
        # GET CURRENTLY ONLINE USERS
        # --------------------------------------------------------------

        with self.server.lock:

            active_users = set(
                self.server.active_clients.keys()
            )

        # --------------------------------------------------------------
        # BUILD RESPONSE
        # --------------------------------------------------------------

        users = []

        for username in usernames:

            if username == self.current_user:
                continue

            users.append({
                "username": username,
                "online": username in active_users,
            })

        users.sort(
            key=lambda user: user["username"].lower()
        )

        self.connection.send(
            MessageType.USERS_RESPONSE,
            {
                "users": users,
            },
        )