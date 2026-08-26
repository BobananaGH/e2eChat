import json
import struct
import threading
from enum import Enum


class MessageType(str, Enum):
    REGISTER = "REGISTER"
    LOGIN = "LOGIN"

    AUTH_SUCCESS = "AUTH_SUCCESS"
    AUTH_FAIL = "AUTH_FAIL"

    UPLOAD_PUBLIC_KEY = "UPLOAD_PUBLIC_KEY"
    FETCH_PUBLIC_KEY = "FETCH_PUBLIC_KEY"
    PUBLIC_KEY_RESPONSE = "PUBLIC_KEY_RESPONSE"

    FETCH_USERS = "FETCH_USERS"
    USERS_RESPONSE = "USERS_RESPONSE"

    SEND_MSG = "SEND_MSG"
    RELAY_MSG = "RELAY_MSG"

    ERROR = "ERROR"
    SUCCESS = "SUCCESS"


class Protocol:
    HEADER_FORMAT = "!I"
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

    MAX_PAYLOAD_SIZE = 10 * 1024 * 1024

    @classmethod
    def pack(cls, message_type, payload):
        data = {
            "type": message_type.value,
            "payload": payload,
        }

        encoded = json.dumps(
            data,
            separators=(",", ":"),
        ).encode("utf-8")

        if len(encoded) > cls.MAX_PAYLOAD_SIZE:
            raise ValueError(
                "Payload too large."
            )

        header = struct.pack(
            cls.HEADER_FORMAT,
            len(encoded),
        )

        return header + encoded

    @classmethod
    def unpack_header(cls, header):
        if len(header) != cls.HEADER_SIZE:
            raise ValueError(
                "Invalid header."
            )

        length = struct.unpack(
            cls.HEADER_FORMAT,
            header,
        )[0]

        if length <= 0:
            raise ValueError(
                "Invalid payload length."
            )

        if length > cls.MAX_PAYLOAD_SIZE:
            raise ValueError(
                "Payload too large."
            )

        return length

    @classmethod
    def parse_payload(cls, payload):
        data = json.loads(
            payload.decode("utf-8")
        )

        return (
            MessageType(data["type"]),
            data["payload"],
        )


class Connection:
    """
    Reliable transport wrapper around a connected TLS socket.

    Handles:
        - protocol framing
        - exact reads
        - sending messages
        - receiving messages
    """

    def __init__(self, socket):
        self.socket = socket
        self._send_lock = threading.Lock()

    def send(
        self,
        message_type,
        payload,
    ):
        packet = Protocol.pack(
            message_type,
            payload,
        )

        with self._send_lock:
            self.socket.sendall(packet)

    def recv(self):
        header = self.recv_exact(
            Protocol.HEADER_SIZE
        )

        if not header:
            return None

        payload_length = Protocol.unpack_header(
            header
        )

        payload = self.recv_exact(
            payload_length
        )

        if not payload:
            return None

        return Protocol.parse_payload(
            payload
        )

    def recv_exact(self, size):
        data = bytearray()

        while len(data) < size:
            chunk = self.socket.recv(
                size - len(data)
            )

            if not chunk:
                return None

            data.extend(chunk)

        return bytes(data)

    def close(self):
        try:
            self.socket.shutdown(
                2
            )
        except OSError:
            pass

        try:
            self.socket.close()
        except OSError:
            pass