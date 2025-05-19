import wx
import os
from enum import Enum
import random

from fivepmbridge.bridge_player import BridgeClient
from fivepmbridge.bridge_game import Card, Suit

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
CARD_DIR = os.path.join(THIS_DIR, 'cards')

def get_image_name(card):
    return f"{card.value}_of_{card.suit.name.lower()}.png"

class BridgeClientGUI(wx.Frame):
    def __init__(self, host='127.0.0.1', port=5000):
        super().__init__(None, title="Bridge Client", size=(800, 800))
        self.client = BridgeClient(self, host, port)
        self.main_panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        play_area = self.create_play_area_panel([[Card(13,Suit.SPADES)],[Card(1,Suit.SPADES)],[Card(1,Suit.SPADES)],[Card(1,Suit.SPADES)]], [True, False, False, False])


        wrapper_panel = wx.Panel(self.main_panel)
        chat = self.create_chat(wrapper_panel)
        control_panel = self.create_control_panel(wrapper_panel)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(chat, proportion=3, flag=wx.EXPAND | wx.ALL, border=5)
        hbox.Add(control_panel, proportion=1, flag=wx.EXPAND | wx.ALL, border=5)
        wrapper_panel.SetSizer(hbox)


        # Ratio of 800:200 = 4:1
        main_sizer.Add(play_area, proportion=4, flag=wx.EXPAND)
        main_sizer.Add(wrapper_panel, proportion=1, flag=wx.EXPAND)

        self.main_panel.SetSizer(main_sizer)
        self.Centre()
        self.Show()

        self.client.connect()

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

    def create_play_area_panel(self, hands, face_up_flags):
        panel = wx.Panel(self.main_panel)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Top row - third hand normal orientation, horizontal
        top_hand_panel = HandPanel(panel, hands[3], face_up_flags[3], vertical=False)
        main_sizer.Add(top_hand_panel, 0, wx.CENTER | wx.TOP | wx.BOTTOM, 10)

        # Middle row with 3 columns
        middle_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Left col - second hand vertical, no rotation
        left_hand_panel = HandPanel(panel, hands[2], face_up_flags[2], vertical=True)
        middle_sizer.Add(left_hand_panel, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.ALIGN_LEFT | wx.TOP | wx.BOTTOM, 10)

        # Add stretchable spacer between left and right hand panels
        middle_sizer.AddStretchSpacer(1)

        # Right col - fourth hand vertical, no rotation
        right_hand_panel = HandPanel(panel, hands[1], face_up_flags[1], vertical=True)
        middle_sizer.Add(right_hand_panel, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT | wx.TOP | wx.BOTTOM, 10)

        # Add middle row sizer to main vertical sizer with proportion=1 and expand flag
        main_sizer.Add(middle_sizer, 1, wx.EXPAND | wx.LEFT | wx.RIGHT , 20)

        # Bottom row - first hand normal, horizontal
        bottom_hand_panel = HandPanel(panel, hands[0], face_up_flags[0], vertical=False)
        main_sizer.Add(bottom_hand_panel, 0, wx.CENTER | wx.TOP | wx.BOTTOM, 10)

        panel.SetSizer(main_sizer)
        return panel

    def create_chat(self, parent):
        panel = wx.Panel(parent)
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
        self.input.Bind(wx.EVT_TEXT_ENTER, self.on_send)
        self.Bind(wx.EVT_CLOSE, self.on_close)
        return panel

    def create_control_panel(self,parent):
        panel = wx.Panel(parent)
        vbox = wx.BoxSizer(wx.VERTICAL)

        # Example button
        btn1 = wx.Button(panel, label="Action 1")
        btn2 = wx.Button(panel, label="Action 2")

        # Example display field
        self.status_display = wx.StaticText(panel, label="Status: Waiting")

        vbox.Add(btn1, flag=wx.EXPAND | wx.BOTTOM, border=5)
        vbox.Add(btn2, flag=wx.EXPAND | wx.BOTTOM, border=5)
        vbox.AddStretchSpacer()
        vbox.Add(self.status_display, flag=wx.EXPAND | wx.TOP, border=5)

        panel.SetSizer(vbox)
        return panel


# --- GUI Hand Panel ---
class HandPanel(wx.Panel):
    def __init__(self, parent, hand, face_up, vertical=False):
        super().__init__(parent)
        self.hand = hand
        self.face_up = face_up
        self.vertical = vertical

        self.card_cache = {}
        self.card_back_img = wx.Image(os.path.join(CARD_DIR, "card_back.png"), wx.BITMAP_TYPE_PNG).Scale(60, 90)
        if self.vertical:
                self.card_back_img = self.card_back_img.Rotate90()

        if vertical:
            self.sizer = wx.BoxSizer(wx.VERTICAL)
        else:
            self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(self.sizer)

        self.populate_cards()

    def get_card_bitmap(self, card):
        filename = get_image_name(card)
        if filename not in self.card_cache:
            img = wx.Image(os.path.join(CARD_DIR, filename), wx.BITMAP_TYPE_PNG).Scale(60, 90)
            if self.vertical:
                img = img.Rotate90()
            self.card_cache[filename] = img
        return self.card_cache[filename]

    def populate_cards(self):
        self.sizer.Clear(True)
        for card in self.hand:
            if self.face_up:
                img = self.get_card_bitmap(card)
            else:
                img = self.card_back_img

            bmp = img.ConvertToBitmap()
            bmp_ctrl = wx.StaticBitmap(self, bitmap=bmp)
            if self.vertical:

                self.sizer.Add(bmp_ctrl, 0, wx.BOTTOM, -35)
            else:
                self.sizer.Add(bmp_ctrl, 0, wx.RIGHT, -35)
        self.Layout()
def join_bridge_game(host, port):
    app = wx.App(False)
    BridgeClientGUI(host, port)  # Replace with actual server IP
    app.MainLoop()