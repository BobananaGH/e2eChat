# code/shared/protocol.py
import json
import struct
from enum import Enum

class MessageType(str, Enum):
    # Auth
    REGISTER = "REGISTER"
    LOGIN = "LOGIN"
    AUTH_SUCCESS = "AUTH_SUCCESS"
    AUTH_FAIL = "AUTH_FAIL"
    
    # Key Exchange
    UPLOAD_PUBLIC_KEY = "UPLOAD_PUBLIC_KEY"
    FETCH_PUBLIC_KEY = "FETCH_PUBLIC_KEY"
    PUBLIC_KEY_RESPONSE = "PUBLIC_KEY_RESPONSE"
    
    # Messaging
    SEND_MSG = "SEND_MSG"
    RELAY_MSG = "RELAY_MSG"
    
    # Status / General
    ERROR = "ERROR"
    SUCCESS = "SUCCESS"

class Protocol:
    HEADER_FORMAT = "!I"  # 4-byte unsigned integer for payload length
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

    @staticmethod
    def pack(msg_type: MessageType, payload: dict) -> bytes:
        """Serializes message type and payload into a framed byte stream."""
        data = {
            "type": msg_type.value,
            "payload": payload
        }
        json_bytes = json.dumps(data).encode('utf-8')
        header = struct.pack(Protocol.HEADER_FORMAT, len(json_bytes))
        return header + json_bytes

    @staticmethod
    def unpack_header(header_bytes: bytes) -> int:
        """Extracts expected payload length from header."""
        return struct.unpack(Protocol.HEADER_FORMAT, header_bytes)[0]

    @staticmethod
    def parse_payload(payload_bytes: bytes) -> tuple[MessageType, dict]:
        """Parses JSON byte payload into MessageType and data dictionary."""
        data = json.loads(payload_bytes.decode('utf-8'))
        return MessageType(data["type"]), data["payload"]