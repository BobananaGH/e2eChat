# Code/shared/auth.py

import hashlib
import hmac
import secrets
import sqlite3
import threading
from pathlib import Path


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
    SQLite-backed authentication manager.

    Authentication answers:
        "Who is this user?"

    E2EE answers:
        "Can the server read this user's messages?"

    User accounts are persisted in SQLite so they survive
    server restarts.
    """

    MIN_USERNAME_LENGTH = 3
    MAX_USERNAME_LENGTH = 32

    MIN_PASSWORD_LENGTH = 6

    def __init__(self, db_path=None):
        """
        Initialize the authentication database.

        By default the database is stored at:

            Code/server/data/users.db
        """

        if db_path is None:
            base_dir = Path(__file__).resolve().parent.parent
            db_path = base_dir / "server" / "data" / "users.db"

        self.db_path = Path(db_path)

        self.db_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._lock = threading.Lock()

        self._initialize_database()

    # ==================================================================
    # DATABASE
    # ==================================================================

    def _get_connection(self):
        """
        Create a new SQLite connection.

        A separate connection is used for each operation because
        the server handles clients across multiple threads.
        """

        connection = sqlite3.connect(
            self.db_path,
            timeout=10,
        )

        connection.execute(
            "PRAGMA foreign_keys = ON"
        )

        return connection

    def _initialize_database(self):
        """
        Create the users table if it does not already exist.
        """

        with self._get_connection() as connection:

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL
                )
                """
            )

            connection.commit()

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
    def _hash_password(
        password: str,
        salt: bytes,
    ) -> bytes:
        """
        Derive a password hash using PBKDF2-HMAC-SHA256.

        Plaintext passwords are never stored.
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

        salt = secrets.token_bytes(16)

        password_hash = self._hash_password(
            password,
            salt,
        )

        password_hash_hex = self._encode_bytes(
            password_hash
        )

        salt_hex = self._encode_bytes(
            salt
        )

        with self._lock:

            try:

                with self._get_connection() as connection:

                    connection.execute(
                        """
                        INSERT INTO users (
                            username,
                            password_hash,
                            salt
                        )
                        VALUES (?, ?, ?)
                        """,
                        (
                            username,
                            password_hash_hex,
                            salt_hex,
                        ),
                    )

                    connection.commit()

            except sqlite3.IntegrityError:

                raise UserAlreadyExistsError(
                    f"Username '{username}' already exists."
                )

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

            with self._get_connection() as connection:

                cursor = connection.execute(
                    """
                    SELECT password_hash, salt
                    FROM users
                    WHERE username = ?
                    """,
                    (username,),
                )

                user = cursor.fetchone()

        if user is None:
            return False

        password_hash_hex, salt_hex = user

        try:

            salt = self._decode_hex(
                salt_hex
            )

            expected_hash = self._decode_hex(
                password_hash_hex
            )

        except (ValueError, TypeError):

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

    def user_exists(
        self,
        username: str,
    ) -> bool:
        """
        Check whether a username exists.
        """

        username = username.strip()

        with self._lock:

            with self._get_connection() as connection:

                cursor = connection.execute(
                    """
                    SELECT 1
                    FROM users
                    WHERE username = ?
                    LIMIT 1
                    """,
                    (username,),
                )

                return cursor.fetchone() is not None

    # ==================================================================
    # USERNAMES
    # ==================================================================

    def get_usernames(self) -> list[str]:
        """
        Return all registered usernames.
        """

        with self._lock:

            with self._get_connection() as connection:

                cursor = connection.execute(
                    """
                    SELECT username
                    FROM users
                    ORDER BY username COLLATE NOCASE
                    """
                )

                return [
                    row[0]
                    for row in cursor.fetchall()
                ]

    # ==================================================================
    # DEBUG / TESTING
    # ==================================================================

    def user_count(self) -> int:
        """
        Return the number of registered users.
        """

        with self._lock:

            with self._get_connection() as connection:

                cursor = connection.execute(
                    """
                    SELECT COUNT(*)
                    FROM users
                    """
                )

                return cursor.fetchone()[0]