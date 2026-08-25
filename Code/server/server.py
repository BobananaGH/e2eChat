# code/server/server.py
import socket
import ssl
import threading
from shared.protocol import Protocol, MessageType

class ChatServer:
    def __init__(self, host: str, port: int, ssl_context: ssl.SSLContext = None):
        self.host = host
        self.port = port
        self.ssl_context = ssl_context
        
        # State Management
        self.active_clients = {}  # {username: socket}
        self.public_keys = {}     # {username: pem_public_key_str}
        self.lock = threading.Lock()
        self.is_running = False

    def start(self):
        raw_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        raw_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        raw_socket.bind((self.host, self.port))
        raw_socket.listen(100)
        
        if self.ssl_context:
            self.server_socket = self.ssl_context.wrap_socket(raw_socket, server_side=True)
        else:
            self.server_socket = raw_socket

        self.is_running = True
        print(f"[SERVER] Running on {self.host}:{self.port}")

        try:
            while self.is_running:
                client_sock, addr = self.server_socket.accept()
                threading.Thread(
                    target=self._handle_client, 
                    args=(client_sock, addr), 
                    daemon=True
                ).start()
        except Exception as e:
            print(f"[SERVER] Stopped: {e}")
        finally:
            self.server_socket.close()

    def _recv_exact(self, sock: socket.socket, num_bytes: int) -> bytes:
        """Helper to ensure full packet delivery over TCP."""
        buffer = bytearray()
        while len(buffer) < num_bytes:
            packet = sock.recv(num_bytes - len(buffer))
            if not packet:
                return None
            buffer.extend(packet)
        return bytes(buffer)

    def _handle_client(self, sock: socket.socket, addr: tuple):
        current_user = None
        print(f"[CONNECTED] Client connected from {addr}")

        try:
            while True:
                header = self._recv_exact(sock, Protocol.HEADER_SIZE)
                if not header:
                    break
                
                payload_len = Protocol.unpack_header(header)
                payload_bytes = self._recv_exact(sock, payload_len)
                if not payload_bytes:
                    break

                msg_type, payload = Protocol.parse_payload(payload_bytes)
                
                # --- COMMAND ROUTING ---
                if msg_type == MessageType.LOGIN or msg_type == MessageType.REGISTER:
                    # Basic auth hook (Replace with DB verification logic as needed)
                    current_user = payload.get("username")
                    with self.lock:
                        self.active_clients[current_user] = sock
                    
                    sock.sendall(Protocol.pack(
                        MessageType.AUTH_SUCCESS, 
                        {"message": f"Welcome {current_user}"}
                    ))
                    print(f"[AUTH] User '{current_user}' logged in.")

                elif msg_type == MessageType.UPLOAD_PUBLIC_KEY:
                    pub_key = payload.get("public_key")
                    if current_user and pub_key:
                        with self.lock:
                            self.public_keys[current_user] = pub_key
                        sock.sendall(Protocol.pack(MessageType.SUCCESS, {"details": "Key stored"}))

                elif msg_type == MessageType.FETCH_PUBLIC_KEY:
                    target_user = payload.get("target_user")
                    with self.lock:
                        key = self.public_keys.get(target_user)
                    
                    if key:
                        sock.sendall(Protocol.pack(
                            MessageType.PUBLIC_KEY_RESPONSE, 
                            {"target_user": target_user, "public_key": key}
                        ))
                    else:
                        sock.sendall(Protocol.pack(
                            MessageType.ERROR, 
                            {"message": "User or key not found"}
                        ))

                elif msg_type == MessageType.SEND_MSG:
                    recipient = payload.get("recipient")
                    encrypted_data = payload.get("encrypted_payload")

                    with self.lock:
                        recipient_sock = self.active_clients.get(recipient)

                    if recipient_sock:
                        # Direct relay to active recipient
                        relay_packet = Protocol.pack(MessageType.RELAY_MSG, {
                            "sender": current_user,
                            "encrypted_payload": encrypted_data
                        })
                        recipient_sock.sendall(relay_packet)
                    else:
                        sock.sendall(Protocol.pack(
                            MessageType.ERROR, 
                            {"message": f"User {recipient} is offline"}
                        ))

        except (ConnectionResetError, BrokenPipeError):
            pass
        finally:
            if current_user:
                with self.lock:
                    if current_user in self.active_clients:
                        del self.active_clients[current_user]
                print(f"[DISCONNECTED] User '{current_user}' left.")
            sock.close()