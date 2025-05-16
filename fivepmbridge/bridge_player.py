import wx
import socket
import threading

class BridgeServer:
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

class BridgeServerGUI(wx.Frame):
    def __init__(self, host='127.0.0.1', port=5000):
        super().__init__(None, title="Bridge Client", size=(500, 400))
        self.client = BridgeServer(self, host, port)

        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        self.log = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY)
        vbox.Add(self.log, proportion=1, flag=wx.EXPAND | wx.ALL, border=5)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.input = wx.TextCtrl(panel, style=wx.TE_PROCESS_ENTER)
        self.send_btn = wx.Button(panel, label="Send")

        hbox.Add(self.input, proportion=1, flag=wx.EXPAND | wx.RIGHT, border=5)
        hbox.Add(self.send_btn, proportion=0)

        vbox.Add(hbox, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=5)
        panel.SetSizer(vbox)

        self.send_btn.Bind(wx.EVT_BUTTON, self.on_send)
        # self.input.Bind(wx.EVT_TEXT_ENTER, self.on_send)
        self.Bind(wx.EVT_CLOSE, self.on_close)

        self.client.connect()
        self.Show()

    def append_message(self, message):
        wx.CallAfter(self.log.AppendText, message + '\n')

    def on_send(self, event):
        message = self.input.GetValue()
        if message:
            self.client.send_message(message)
            self.input.SetValue("")

    def on_close(self, event):
        self.client.disconnect()
        self.Destroy()

def join_bridge_game(host, port):
    app = wx.App(False)
    BridgeServerGUI(host, port)  # Replace with actual server IP
    app.MainLoop()