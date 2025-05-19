import wx
import socket
import threading

class BridgeClient:
    def __init__(self, gui, host, port):
        self.gui = gui
        self.host = host
        self.port = port
        self.running = False
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        try:
            self.socket.connect((self.host, self.port))
            self.running = True
            self.gui.append_message(f"Connected to server at {self.host}:{self.port}")
            threading.Thread(target=self.receive_messages, daemon=True).start()
        except Exception as e:
            self.gui.append_message(f"Connection failed: {e}")

    def receive_messages(self):
        while self.running:
            try:
                msg = self.socket.recv(1024)
                if not msg:
                    break
                self.gui.append_message(msg.decode())
            except Exception as e:
                self.gui.append_message(f"Error receiving message: {e}")
                break
        self.running = False
        self.socket.close()
        self.gui.append_message("Disconnected from server.")

    def send_message(self, message):
        if self.running:
            try:
                self.socket.sendall(message.encode())
            except Exception as e:
                self.gui.append_message(f"Error sending message: {e}")

    def disconnect(self):
        self.running = False
        try:
            self.socket.shutdown(socket.SHUT_RDWR)
        except:
            pass
        self.socket.close()
        self.gui.append_message("Disconnected.")



