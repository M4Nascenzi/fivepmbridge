import socket
import threading
from fivepmbridge.bridge_game import ContractBridge, Card, Suit
from collections import defaultdict
SERVER = 0

class BridgeTable:
    def __init__(self, host='0.0.0.0', port=2410, max_clients=4):
        self.host = host
        self.port = port
        self.max_clients = max_clients
        self.admin_conn = None
        self.clients = []
        self.client_lock = threading.Lock()
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_to_name = {SERVER: "server"}

        self.game = ContractBridge(self.clients)

        self.client_to_dummy = defaultdict(bool)

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
                        msg = "[SERVER] You are the admin."
                    else:
                        msg = "[SERVER] You are a regular player."
                    self.send_message(conn, msg)

                # with self.client_lock:
                #     if len(self.clients) >= self.max_clients:
                #         conn.sendall(b"Server full. Connection refused.")
                #         conn.close()
                #         continue
                #     self.clients.append(conn)
                thread = threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True)
                thread.start()
        except:
            self.shutdown()

    def send_message(self, client, message):
        data = message.encode()
        length = len(data).to_bytes(4, byteorder='big')  # 4-byte length prefix
        client.sendall(length + data)


    def handle_client(self, conn, addr):
        print(f"[NEW CONNECTION] {addr} connected.")
        with conn:
            self.send_card_state()
            while True:
                try:
                    length_bytes = conn.recv(4)
                    if not length_bytes:
                        raise ConnectionError("Did not receive length_bytes")
                    length = int.from_bytes(length_bytes, byteorder='big')
                    data = b""
                    while len(data) < length:
                        more = conn.recv(length - len(data))
                        if not more:
                            raise ConnectionError("Socket closed")
                        data += more

                    text = data.decode()
                    if self.parse_for_admin_commands(text, conn): continue
                    if self.parse_for_social_commands(text, conn): continue
                    if self.parse_for_bridge_commands(text, conn): continue
                    self.broadcast(text, conn)


                    # self.broadcast(text, SERVER)
                except (ConnectionResetError, ConnectionAbortedError, ConnectionError):
                    break
        with self.client_lock:
            if conn in self.clients:
                self.clients.remove(conn)
                self.client_to_name.pop(conn)
            if conn is self.admin_conn:
                if len(self.clients) > 0:
                    for client in self.clients:
                        try:
                            msg = "[PRIVATE] You are now the admin!"
                            self.send_message(client, msg)
                            self.admin_conn = client
                            break
                        except:
                            pass
                else:
                    self.admin_conn = None

        print(f"[DISCONNECTED] {addr} disconnected.")
        self.send_card_state()

    def parse_for_admin_commands(self, text, conn):
        if text == "!shutdown":
            if conn == self.admin_conn:
                self.broadcast("Server is shutting down by admin.", SERVER)
                self.shutdown()
            else:
                self.scold("You can't shutdown the server!", conn)
            return True
        elif text == "!deal":
            if conn == self.admin_conn:

                if self.game.deal():
                    self.broadcast("Admin is dealing cards.", SERVER)
                    self.send_card_state()
                else:
                    pass
            else:
                self.scold("You can't deal!", conn)
            return True
        elif text.split()[0] == "!scold":
            if conn == self.admin_conn:
                try:
                    target_name = text.split()[1]
                    for client, client_name in self.client_to_name.items():
                        if target_name == client_name:
                            self.scold(" ".join(text.split()[2:]), client)
                            break
                    return True
                except:
                    pass
            else:
                self.scold("You can't scold people!", conn)
                return True
        elif text == "!resetdummy":
            if conn == self.admin_conn:
                for client in self.client_to_dummy:
                    self.client_to_dummy[client] = False
                self.broadcast("Admin reset dummy flags.", SERVER)
            else:
                self.scold("You can't scold people!", conn)
                return True
        elif text.split()[0] == "!dummy":
            if conn == self.admin_conn:
                try:
                    target_name = text.split()[1]
                    for client, client_name in self.client_to_name.items():
                        if target_name == client_name:
                            self.client_to_dummy[client] = True
                            self.broadcast(f"Admin set {client_name} dummy flag to True.", SERVER)
                            self.send_card_state()
                            break
                    return True
                except:
                    pass
            else:
                self.scold("You can't scold people!", conn)
                return True
        return False
    def parse_for_social_commands(self, text, conn):
        try:
            if text.split()[0] == "!name":
                self.broadcast(text, conn)
                self.client_to_name[conn] = ' '.join(text.split()[1:])
                self.send_card_state()
                return True
            elif text.split()[0] == "!me":
                self.broadcast(text[0:2], conn, me=True)
                return True
        except:
            pass
    def parse_for_bridge_commands(self, text, conn):
        if text[0] == "@":
            if text == "@pass":
                pass

            elif text == "@trick":
                if self.game.take_trick(conn):
                    self.broadcast(f"{self.client_to_name[conn]} took a trick!", SERVER)
                    self.send_card_state()
                else:
                    self.scold("You can't take this trick!", conn)
            elif text[0:5] == "@card":
                if self.game.play_card(conn, text.split("_")[-1]):
                    self.broadcast(f"{self.client_to_name[conn]} played {text.split('_')[-1]}", SERVER)
                    self.send_card_state()
                else:
                    self.scold("You can't play that card!", conn)
            elif len(text) == 3 and text[1] in ["1","2","3","4","5","6","7"] and text[2] in ['s', 'c', 'd', 'h', 'n']:
                self.broadcast(f"{self.client_to_name[conn]} bids '{text[1:]}'", SERVER)
            else:
                self.broadcast(f"You ({self.client_to_name[conn]}) can't bid '{text[1:]}'", SERVER)
            return True


    def broadcast(self, text, sender_conn, me=False):
        name = self.client_to_name[sender_conn]
        msg_to_send = name + ": " + text
        if me:
            msg_to_send = name + text[3:]
        with self.client_lock:
            for client in self.clients:
                try:
                    self.send_message(client, msg_to_send)
                except Exception:
                    print(f"COULD NOT SEND MESSAGE {msg_to_send}, {client}")
                    pass  # Ignore broken connections

    def scold(self, text, client):
        # name = self.client_to_name[client]
        msg_to_send = "^" + text
        with self.client_lock:
            # for client in self.clients:
            try:
                self.send_message(client, msg_to_send)
            except Exception:
                print(f"COULD NOT SEND MESSAGE {msg_to_send}, {client}")

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

    def send_card_state(self):
        #to each person, send their cards face up
        #send dummy cards face up
        # send other cards face down
        # send current played cards
        # just a dummy version right now

        if len(self.clients) != 4:
            return

        client_to_hand = self.game.get_hands()
        client_to_played_cards = self.game.get_played_cards()


        with self.client_lock:
            for client in self.clients:
                client_name = self.client_to_name[client]
                if client_name == "server":
                    continue
                player_hand_states = {}
                player_played_cards = {}

                for i, client_of_cards in enumerate(self.clients):
                    cards_owner_name = self.client_to_name[client_of_cards]
                    cards = client_to_hand[client_of_cards]
                    try:
                        player_played_cards[cards_owner_name] = client_to_played_cards[client_of_cards].to_code()
                    except (AttributeError, KeyError):
                        player_played_cards[cards_owner_name] = "None"

                    if self.client_to_dummy[client_of_cards] or client_of_cards == client:
                        player_hand_states[cards_owner_name] = [a.to_code() for a in cards]
                    else:
                        player_hand_states[cards_owner_name] = ["b" for a in cards]
                state_text = "@" + self.client_to_name[client] + "\n" + str(player_hand_states) + "\n" + str(player_played_cards)
                self.send_message(client, state_text)
        self.broadcast("Sent State", SERVER)

def start_bridge_server():
    server = BridgeTable()
    server.start()