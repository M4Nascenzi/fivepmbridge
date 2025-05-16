import socket
import threading

class BridgeTable:
    def __init__(self, host='0.0.0.0', port=2410, max_clients=4):
        self.host = host
        self.port = port
        self.max_clients = max_clients
        self.admin_conn = None
        self.clients = []
        self.client_lock = threading.Lock()
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_to_name = {}

    def start(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(self.max_clients)
        print(f"[STARTED] Bridge server listening on {self.host}:{self.port}")

        try:
            while True:
                conn, addr = self.server_socket.accept()
                with self.client_lock:
                    self.clients.append(conn)
                    self.client_to_name[conn] = str(addr)
                    if self.admin_conn is None:
                        self.admin_conn = conn
                        conn.sendall(b"[SERVER] You are the admin.\n")
                    else:
                        conn.sendall(b"[SERVER] You are a regular player.\n")
                # with self.client_lock:
                #     if len(self.clients) >= self.max_clients:
                #         conn.sendall(b"Server full. Connection refused.\n")
                #         conn.close()
                #         continue
                #     self.clients.append(conn)
                thread = threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True)
                thread.start()
        except:
            self.shutdown()

    def handle_client(self, conn, addr):
        print(f"[NEW CONNECTION] {addr} connected.")
        with conn:
            while True:
                try:
                    msg = conn.recv(1024)
                    if not msg:
                        break
                    text = msg.decode().strip()
                    print(text)
                    if text == "!shutdown":
                        if conn == self.admin_conn:
                            self.broadcast(b"[SERVER] Server is shutting down by admin.\n", conn)
                            self.shutdown()
                            break
                    if text.split()[0] == "!name":
                        self.client_to_name[conn] = ' '.join(text.split()[1:])
                    self.broadcast(msg, conn)
                except (ConnectionResetError, ConnectionAbortedError):
                    break
        with self.client_lock:
            if conn in self.clients:
                self.clients.remove(conn)
            if conn is self.admin_conn:
                if len(self.clients) > 0:
                    self.admin_conn = self.clients[0]
                    self.admin_conn.sendall("[PRIVATE] You are now the admin!")
                else:
                    self.admin_conn = None
        print(f"[DISCONNECTED] {addr} disconnected.")

    def broadcast(self, message, sender_conn):
        name = self.client_to_name[sender_conn]
        text = name + ": " + message.decode().strip()
        msg_to_send = text.encode()
        with self.client_lock:
            for client in self.clients:
                try:
                    client.sendall(msg_to_send)
                except Exception:
                    pass  # Ignore broken connections

    def shutdown(self):
        print("[SHUTDOWN] Server is shutting down.")
        with self.client_lock:
            for client in self.clients:
                try:
                    client.close()
                except:
                    pass
            self.clients.clear()
        self.server_socket.close()

def start_bridge_server():
    server = BridgeTable()
    server.start()