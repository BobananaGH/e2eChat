# Code/server/tls.py

import os
import ssl


class TLSServer:
    """
    Configure TLS for the chat server.

    Responsibilities:
        - Create the server SSL context
        - Load the server certificate
        - Load the server private key
        - Wrap accepted sockets with TLS

    This class does NOT handle:
        - TCP protocol framing
        - Authentication
        - E2EE
        - Message routing
    """

    def __init__(self):
        self.context = self._create_context()

    # ==================================================================
    # SSL CONTEXT
    # ==================================================================

    @staticmethod
    def _create_context():
        """
        Create the TLS server context.
        """

        cert_path = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "certs",
                "server.crt",
            )
        )

        key_path = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "certs",
                "server.key",
            )
        )

        context = ssl.SSLContext(
            ssl.PROTOCOL_TLS_SERVER
        )

        context.load_cert_chain(
            certfile=cert_path,
            keyfile=key_path,
        )

        return context

    # ==================================================================
    # WRAP SOCKET
    # ==================================================================

    def wrap_socket(self, raw_socket):
        """
        Wrap an accepted TCP socket with TLS.
        """

        return self.context.wrap_socket(
            raw_socket,
            server_side=True,
        )