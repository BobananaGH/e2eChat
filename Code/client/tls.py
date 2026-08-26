# Code/client/tls.py

import os
import socket
import ssl


class TLSConnection:
    """
    Establishes and manages the client's TLS socket.

    Responsibilities:
        - Create the TCP socket
        - Connect to the server
        - Perform the TLS handshake
        - Verify the server certificate
        - Close the secure socket

    This class does NOT handle:
        - Protocol framing
        - JSON encoding/decoding
        - E2EE
        - Authentication
        - Message routing
    """

    def __init__(
        self,
        host: str,
        port: int,
        timeout: float = 10.0,
    ):
        self.host = host
        self.port = port
        self.timeout = timeout

        self.socket = self._connect()

    # ==================================================================
    # CONNECTION
    # ==================================================================

    def _connect(self):
        """
        Establish a TLS connection to the server.

        Uses:
            Code/certs/server.crt
        """

        cert_path = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "certs",
                "server.crt",
            )
        )

        context = ssl.SSLContext(
            ssl.PROTOCOL_TLS_CLIENT
        )

        context.load_verify_locations(
            cert_path
        )

        # Local development uses a self-signed certificate.
        context.check_hostname = False
        context.verify_mode = ssl.CERT_REQUIRED

        raw_socket = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM,
        )

        raw_socket.settimeout(
            self.timeout
        )

        try:
            raw_socket.connect(
                (self.host, self.port)
            )

            secure_socket = context.wrap_socket(
                raw_socket,
                server_hostname=self.host,
            )

            secure_socket.settimeout(None)

            print(
                f"[CLIENT] Connected to "
                f"{self.host}:{self.port}"
            )

            return secure_socket

        except Exception:
            raw_socket.close()
            raise

    # ==================================================================
    # CLOSE
    # ==================================================================

    def close(self):
        """
        Close the TLS connection.
        """

        try:
            self.socket.shutdown(
                socket.SHUT_RDWR
            )
        except OSError:
            pass

        try:
            self.socket.close()
        except OSError:
            pass