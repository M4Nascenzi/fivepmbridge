import wx
import socket
import threading
import ast

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
            # try:
            msg = self.socket.recv(4096)
            if not msg:
                break
            text = msg.decode()
            if self.parse_commands(text):
                pass
            else:
                self.gui.append_message(text)
            # except Exception as e:
            #     self.gui.append_message(f"Error receiving message: {e}")
            #     break
        self.running = False
        self.socket.close()
        self.gui.append_message("Disconnected from server.")
    def parse_commands(self, text):
        if text[0] == "@":
            self.parse_bridge_state(text[1:])
            return True
        elif text[0] == "^":
            self.gui.scold(text[1:])
            return True
        return False
    def parse_bridge_state(self, state_text):

        my_name, hands, played_cards = state_text.split("\n")
        hands = ast.literal_eval(hands)
        played_cards = ast.literal_eval(played_cards)
        # order goes south, west, north, east
        names = list(hands.keys())
        my_index = names.index(my_name)
        names_ordered = []
        hands_ordered = []
        played_cards_ordered = []
        for i in range(4):
            names_ordered.append(names[(my_index+i)%4])
            hands_ordered.append(hands[names_ordered[-1]])
            if played_cards[names_ordered[-1]] == "None":
                played_cards_ordered.append(None)
            else:
                played_cards_ordered.append(played_cards[names_ordered[-1]])
        wx.CallAfter(self.gui.update_state, names_ordered, hands_ordered, played_cards_ordered)
        # self.gui.update_state(names_ordered, hands_ordered, played_cards_ordered)

    def send_message(self, message):
        if self.running:
            try:
                self.socket.sendall(message.encode())
            except Exception as e:
                self.gui.append_message(f"Error sending message: {e}")

    def play_card(self, card):
        self.send_message("@card_"+card)

    def take_trick(self):
        self.send_message("@trick")

    def disconnect(self):
        self.running = False
        try:
            self.socket.shutdown(socket.SHUT_RDWR)
        except:
            pass
        self.socket.close()
        self.gui.append_message("Disconnected.")



