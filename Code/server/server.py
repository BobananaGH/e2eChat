# Code/server/server.py
import socket
import threading

from shared.auth import AuthManager
from server.tls import TLSServer
from server.core.client_handler import ClientHandler


class ChatServer:
    """
    E2EE chat relay server.

    Responsibilities:
        - Create the listening TCP socket
        - Configure TLS
        - Accept client connections
        - Maintain shared server state
        - Start a ClientHandler for each client

    Client-specific logic is handled by:
        server/core/client_handler.py

    The server NEVER performs:
        - ECDH
        - AES encryption/decryption
        - plaintext message processing

    The server only stores public keys and relays
    encrypted message payloads.
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 5000,
    ):
        self.host = host
        self.port = port

        # ==============================================================
        # AUTHENTICATION
        # ==============================================================

        self.auth_manager = AuthManager()

        # ==============================================================
        # ACTIVE CLIENTS
        #
        # {
        #     username: Connection
        # }
        # ==============================================================

        self.active_clients = {}

        # ==============================================================
        # E2EE PUBLIC KEYS
        #
        # {
        #     username: public_key
        # }
        #
        # Private keys NEVER exist on the server.
        # ==============================================================

        self.public_keys = {}

        # ==============================================================
        # SHARED STATE LOCK
        # ==============================================================

        self.lock = threading.Lock()

        # ==============================================================
        # TLS
        # ==============================================================

        self.tls = TLSServer()

        # ==============================================================
        # SERVER SOCKET
        # ==============================================================

        self.server_socket = None
        self.is_running = False

    # ==================================================================
    # SERVER START
    # ==================================================================

    def start(self):
        """
        Start the TCP/TLS server and accept clients.
        """

        raw_socket = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM,
        )

        raw_socket.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            1,
        )

        raw_socket.bind(
            (self.host, self.port)
        )

        raw_socket.listen(100)

        # --------------------------------------------------------------
        # TLS
        # --------------------------------------------------------------

        self.server_socket = self.tls.wrap_socket(
            raw_socket
        )

        self.is_running = True

        print(
            f"[SERVER] Running on "
            f"{self.host}:{self.port}"
        )

        try:
            while self.is_running:

                client_socket, address = (
                    self.server_socket.accept()
                )

                self._start_client_handler(
                    client_socket,
                    address,
                )

        except OSError as exc:

            if self.is_running:
                print(
                    f"[SERVER] Socket error: {exc}"
                )

        except KeyboardInterrupt:

            print(
                "\n[SERVER] Shutdown requested."
            )

        except Exception as exc:

            print(
                f"[SERVER] Stopped: {exc}"
            )

        finally:

            self.stop()

    # ==================================================================
    # CLIENT HANDLER
    # ==================================================================

    def _start_client_handler(
        self,
        client_socket: socket.socket,
        address,
    ):
        """
        Start a dedicated ClientHandler thread.
        """

        handler = ClientHandler(
            server=self,
            sock=client_socket,
            addr=address,
        )

        threading.Thread(
            target=handler.handle,
            daemon=True,
        ).start()

    # ==================================================================
    # SERVER SHUTDOWN
    # ==================================================================

    def stop(self):
        """
        Stop accepting new connections and close
        the server socket.
        """

        if not self.is_running:
            return

        self.is_running = False

        if self.server_socket:

            try:
                self.server_socket.close()
            except OSError:
                pass

            self.server_socket = None

        print("[SERVER] Stopped.")


def main():
    """
    Application entry point.
    """

    server = ChatServer(
        host="127.0.0.1",
        port=5000,
    )

    server.start()


if __name__ == "__main__":
    main()