# code/shared/auth.py

import hashlib
import hmac
import secrets
import threading


class AuthError(Exception):
    """Base exception for authentication-related errors."""


class UserAlreadyExistsError(AuthError):
    """Raised when attempting to register an existing username."""


class InvalidCredentialsError(AuthError):
    """Raised when login credentials are invalid."""


class InvalidUsernameError(AuthError):
    """Raised when a username is invalid."""


class AuthManager:
    """
    Authentication manager.

    This class is intentionally separate from the E2EE implementation.

    Authentication answers:
        "Who is this user?"

    E2EE answers:
        "Can the server read this user's messages?"

    The server may use this class to authenticate users, while the
    actual ECDH/AES-GCM operations remain inside client/core/crypto.py.
    """

    MIN_USERNAME_LENGTH = 3
    MAX_USERNAME_LENGTH = 32

    MIN_PASSWORD_LENGTH = 6

    def __init__(self):
        # {
        #     username: {
        #         "password_hash": "...",
        #         "salt": "..."
        #     }
        # }
        #
        # This is intentionally in-memory for the current project.
        # A database can replace this later without changing the
        # E2EE architecture.
        self._users = {}

        self._lock = threading.Lock()

    # ==================================================================
    # USERNAME VALIDATION
    # ==================================================================

    @classmethod
    def validate_username(cls, username: str) -> bool:
        """
        Validate a username.

        Rules:
        - must be a string
        - 3-32 characters
        - letters, numbers, underscore, and hyphen only
        """
        if not isinstance(username, str):
            return False

        username = username.strip()

        if not (
            cls.MIN_USERNAME_LENGTH
            <= len(username)
            <= cls.MAX_USERNAME_LENGTH
        ):
            return False

        for char in username:
            if not (
                char.isalnum()
                or char in ("_", "-")
            ):
                return False

        return True

    @classmethod
    def validate_password(cls, password: str) -> bool:
        """
        Validate password length.
        """
        return (
            isinstance(password, str)
            and len(password) >= cls.MIN_PASSWORD_LENGTH
        )

    # ==================================================================
    # PASSWORD HASHING
    # ==================================================================

    @staticmethod
    def _hash_password(password: str, salt: bytes) -> bytes:
        """
        Derive a password hash using PBKDF2-HMAC-SHA256.

        The plaintext password is never stored.
        """
        return hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            600_000,
        )

    @staticmethod
    def _encode_bytes(value: bytes) -> str:
        return value.hex()

    @staticmethod
    def _decode_hex(value: str) -> bytes:
        return bytes.fromhex(value)

    # ==================================================================
    # REGISTRATION
    # ==================================================================

    def register(
        self,
        username: str,
        password: str,
    ) -> bool:
        """
        Register a new user.

        Returns:
            True if registration succeeds.

        Raises:
            InvalidUsernameError
            ValueError
            UserAlreadyExistsError
        """
        username = username.strip()

        if not self.validate_username(username):
            raise InvalidUsernameError(
                "Username must contain only letters, numbers, "
                "underscore, or hyphen and be 3-32 characters long."
            )

        if not self.validate_password(password):
            raise ValueError(
                f"Password must contain at least "
                f"{self.MIN_PASSWORD_LENGTH} characters."
            )

        with self._lock:
            if username in self._users:
                raise UserAlreadyExistsError(
                    f"Username '{username}' already exists."
                )

            salt = secrets.token_bytes(16)

            password_hash = self._hash_password(
                password,
                salt,
            )

            self._users[username] = {
                "password_hash": self._encode_bytes(password_hash),
                "salt": self._encode_bytes(salt),
            }

        return True

    # ==================================================================
    # LOGIN
    # ==================================================================

    def authenticate(
        self,
        username: str,
        password: str,
    ) -> bool:
        """
        Authenticate a user.

        Returns:
            True if credentials are valid.
            False otherwise.
        """
        username = username.strip()

        with self._lock:
            user = self._users.get(username)

        if user is None:
            return False

        try:
            salt = self._decode_hex(user["salt"])
            expected_hash = self._decode_hex(
                user["password_hash"]
            )

        except (KeyError, ValueError):
            return False

        actual_hash = self._hash_password(
            password,
            salt,
        )

        return hmac.compare_digest(
            actual_hash,
            expected_hash,
        )

    # ==================================================================
    # USER LOOKUP
    # ==================================================================

    def user_exists(self, username: str) -> bool:
        """
        Check whether a username exists.
        """
        username = username.strip()

        with self._lock:
            return username in self._users

    # ==================================================================
    # DEBUG / TESTING
    # ==================================================================

    def user_count(self) -> int:
        """
        Return the number of registered users.

        Useful for tests.
        """
        with self._lock:
            return len(self._users)