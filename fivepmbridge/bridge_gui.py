import wx
import os
from enum import Enum
import random

from fivepmbridge.bridge_player import BridgeClient

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
CARD_DIR = os.path.join(THIS_DIR, 'cards')


def get_image_name(card_code, covered=False):
    value = card_code[1:]
    suit_code = card_code[0]
    if suit_code == 'C':
        suit_code = "clubs"
    elif suit_code == 'D':
        suit_code = "diamonds"
    elif suit_code == 'H':
        suit_code = "hearts"
    elif suit_code == 'S':
        suit_code = "spades"
    if covered:
        return f"{value}_of_{suit_code}_covered.png"
    return f"{value}_of_{suit_code}.png"

class BridgeClientGUI(wx.Frame):
    def __init__(self, host='127.0.0.1', port=5000):
        super().__init__(None, title="Bridge Client", size=(800, 800))
        self.client = BridgeClient(self, host, port)
        self.main_panel = wx.Panel(self)

        self.selected_hand_panel = None
        self.selected_card = None

        main_sizer = wx.BoxSizer(wx.VERTICAL)

        play_area = self.create_play_area_panel([[],[],[],[]], [True, False, False, False])


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

    def scold(self, text):
        dlg = wx.MessageDialog(self,
                               message=text,
                               caption="You can't bid that!",
                               style=wx.OK | wx.ICON_WARNING)
        dlg.ShowModal()
        dlg.Destroy()

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
        self.top_hand_panel = HandPanel(panel, hands[3], face_up_flags[3], self, vertical=False, horizantal=True)
        main_sizer.Add(self.top_hand_panel, 0, wx.CENTER | wx.TOP | wx.BOTTOM, 10)

        # Middle row with 3 columns
        middle_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Left col - second hand vertical, no rotation
        self.left_hand_panel = HandPanel(panel, hands[2], face_up_flags[2], self, vertical=True, horizantal=False)
        middle_sizer.Add(self.left_hand_panel, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.ALIGN_LEFT | wx.TOP | wx.BOTTOM, 10)

        # Center played cards panel
        self.played_cards_panel = PlayedCardsPanel(panel)
        middle_sizer.AddStretchSpacer(1)
        middle_sizer.Add(self.played_cards_panel, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        middle_sizer.AddStretchSpacer(1)

        # Right col - fourth hand vertical, no rotation
        self.right_hand_panel = HandPanel(panel, hands[1], face_up_flags[1], self, vertical=True, horizantal=True)
        middle_sizer.Add(self.right_hand_panel, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT | wx.TOP | wx.BOTTOM, 10)

        # Add middle row sizer to main vertical sizer with proportion=1 and expand flag
        main_sizer.Add(middle_sizer, 1, wx.EXPAND | wx.LEFT | wx.RIGHT , 20)

        # Bottom row - first hand normal, horizontal
        self.bottom_hand_panel = HandPanel(panel, hands[0], face_up_flags[0], self, vertical=False, horizantal=False)
        main_sizer.Add(self.bottom_hand_panel, 0, wx.CENTER | wx.TOP | wx.BOTTOM, 10)

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
        btn1 = wx.Button(panel, label="Play Card")
        btn2 = wx.Button(panel, label="Take Trick")

        btn1.Bind(wx.EVT_BUTTON, self.on_play_card)
        btn2.Bind(wx.EVT_BUTTON, self.on_take_trick)

        # Example display field
        self.status_display = wx.StaticText(panel, label="Status: Waiting")

        vbox.Add(btn1, flag=wx.EXPAND | wx.BOTTOM, border=5)
        vbox.Add(btn2, flag=wx.EXPAND | wx.BOTTOM, border=5)
        vbox.AddStretchSpacer()
        vbox.Add(self.status_display, flag=wx.EXPAND | wx.TOP, border=5)

        panel.SetSizer(vbox)
        return panel

    def update_state(self, names, hands, played_cards):

        if len(hands[0]) > 0:
            self.bottom_hand_panel.set_hand(names[0], hands[0], (hands[0][0]!='b'))
        if len(hands[1]) > 0:
            self.left_hand_panel.set_hand(names[1], hands[1], (hands[1][0]!='b'))
        if len(hands[2]) > 0:
            self.top_hand_panel.set_hand(names[2], hands[2], (hands[2][0]!='b'))
        if len(hands[3]) > 0:
            self.right_hand_panel.set_hand(names[3], hands[3], (hands[3][0]!='b'))

        # Show played cards
        self.played_cards_panel.set_played_cards(played_cards)

    def on_play_card(self, event):
        print("play card")
        if self.selected_card:
            self.client.play_card(self.selected_card)
            self.selected_card = None
            self.selected_hand_panel.selected_card = None
            self.selected_hand_panel.populate_cards()
            self.selected_hand_panel = None
            self.status_display.SetLabel("Status: Waiting")


    def on_take_trick(self, event):
        print("take trick")
        self.client.take_trick()

    def card_clicked(self, panel, card):
        # Deselect previous selection
        if self.selected_hand_panel and self.selected_hand_panel != panel:
            self.selected_hand_panel.selected_card = None
            self.selected_hand_panel.populate_cards()

        # Toggle selection
        if self.selected_card == card and self.selected_hand_panel == panel:
            self.selected_card = None
            self.selected_hand_panel = None
            self.status_display.SetLabel("Status: Waiting")
        else:
            self.selected_card = card
            self.selected_hand_panel = panel
            self.status_display.SetLabel(f"Selected card: {card}")

        # Refresh the clicked panel either way
        panel.selected_card = self.selected_card if self.selected_hand_panel == panel else None
        panel.populate_cards()

class PlayedCardsPanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        self.card_cache = {}
        self.grid = wx.GridSizer(rows=3, cols=3, hgap=10, vgap=10)
        self.SetSizer(self.grid)

        # Pre-fill with blank cells
        self.slots = [wx.Panel(self, size=(60, 90)) for _ in range(9)]
        for slot in self.slots:
            self.grid.Add(slot, 0, wx.ALIGN_CENTER)

    def set_played_cards(self, cards):
        # Clear previous content from all 9 grid cells
        for slot in self.slots:
            slot.DestroyChildren()

        # Player positions → grid index: South, West, North, East
        slot_indices = [7, 3, 1, 5]

        for i, card in enumerate(cards):
            if card:
                slot = self.slots[slot_indices[i]]
                bmp = self.get_card_bitmap(card).ConvertToBitmap()
                bmp_ctrl = wx.StaticBitmap(slot, bitmap=bmp)
                sizer = wx.BoxSizer(wx.VERTICAL)
                sizer.Add(bmp_ctrl, 0, wx.ALIGN_CENTER)
                slot.SetSizer(sizer)

        self.Layout()

    def get_card_bitmap(self, card):
        filename = get_image_name(card)
        if filename not in self.card_cache:
            img = wx.Image(os.path.join(CARD_DIR, filename), wx.BITMAP_TYPE_PNG).Scale(60, 90)
            self.card_cache[filename] = img
        return self.card_cache[filename]

# --- GUI Hand Panel ---
class HandPanel(wx.Panel):
    def __init__(self, parent, hand, face_up, gui, vertical=False, horizantal=False):
        super().__init__(parent)
        self.name = "Empty"
        self.gui = gui

        self.hand = hand
        self.face_up = face_up
        self.vertical = vertical
        self.horizantal = horizantal
        if self.vertical:
            self.name = "\n".join(self.name)

        self.selected_card = None  # Track selected card
        self.card_controls = {}  # Maps StaticBitmap to Card

        self.card_cache = {}
        self.card_back_img = wx.Image(os.path.join(CARD_DIR, "card_back.png"), wx.BITMAP_TYPE_PNG).Scale(60, 90)
        self.card_back_img_covered = wx.Image(os.path.join(CARD_DIR, "card_back_covered.png"), wx.BITMAP_TYPE_PNG).Scale(30, 90)
        if self.vertical and not self.horizantal:
            self.card_back_img = self.card_back_img.Rotate90()
            self.card_back_img_covered = self.card_back_img_covered.Rotate90()
        elif not self.vertical and self.horizantal:
            self.card_back_img = self.card_back_img.Rotate180()
            self.card_back_img_covered = self.card_back_img_covered.Rotate180()
        elif self.vertical and self.horizantal:
            self.card_back_img = self.card_back_img.Rotate90(False)
            self.card_back_img_covered = self.card_back_img_covered.Rotate90(False)

        if vertical:
            self.sizer = wx.BoxSizer(wx.VERTICAL)
        else:
            self.sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Determine main orientation
        self.name_label = wx.StaticText(self, label=self.name)

        # Determine where to place the name based on orientation
        if self.vertical and self.horizantal:
            # Both: Name on the right
            main_sizer = wx.BoxSizer(wx.HORIZONTAL)
            self.sizer = wx.BoxSizer(wx.VERTICAL)
            main_sizer.Add(self.sizer, 0, wx.ALIGN_CENTER_VERTICAL)
            main_sizer.AddSpacer(5)
            main_sizer.Add(self.name_label, 0, wx.ALIGN_CENTER_VERTICAL)

        elif self.vertical:
            # Vertical only: Name on the left
            main_sizer = wx.BoxSizer(wx.HORIZONTAL)
            self.sizer = wx.BoxSizer(wx.VERTICAL)
            main_sizer.Add(self.name_label, 0, wx.ALIGN_CENTER_VERTICAL)
            main_sizer.AddSpacer(5)
            main_sizer.Add(self.sizer, 0, wx.ALIGN_CENTER_VERTICAL)

        elif self.horizantal:
            # Horizontal only: Name above
            main_sizer = wx.BoxSizer(wx.VERTICAL)
            self.sizer = wx.BoxSizer(wx.HORIZONTAL)
            main_sizer.Add(self.name_label, 0, wx.ALIGN_CENTER_HORIZONTAL)
            main_sizer.AddSpacer(5)
            main_sizer.Add(self.sizer, 0, wx.ALIGN_CENTER_HORIZONTAL)

        else:
            # Neither: Name below
            main_sizer = wx.BoxSizer(wx.VERTICAL)
            self.sizer = wx.BoxSizer(wx.HORIZONTAL)
            main_sizer.Add(self.sizer, 0, wx.ALIGN_CENTER_HORIZONTAL)
            main_sizer.AddSpacer(5)
            main_sizer.Add(self.name_label, 0, wx.ALIGN_CENTER_HORIZONTAL)

        self.SetSizer(main_sizer)

        self.populate_cards()

    def set_hand(self, name, hand, face_up):
        self.name = name
        self.hand = hand
        self.face_up = face_up
        self.selected_card = None
        self.populate_cards()
        if self.vertical:
            self.name = "\n".join(self.name)
        self.name_label.SetLabel(self.name)
        self.Update()

    def get_card_bitmap(self, card, covered=False):
        filename = get_image_name(card, covered)
        width = 60
        if covered:
            width = 30
        if filename not in self.card_cache:
            img = wx.Image(os.path.join(CARD_DIR, filename), wx.BITMAP_TYPE_PNG).Scale(width, 90)
            if self.vertical and not self.horizantal:
                img = img.Rotate90()
            elif not self.vertical and self.horizantal:
                img = img.Rotate180()
            elif self.vertical and self.horizantal:
                img = img.Rotate90(False)
            self.card_cache[filename] = img
        return self.card_cache[filename]

    def populate_cards(self):
        self.sizer.Clear(True)
        temp_list = self.hand
        if self.horizantal:
            temp_list = reversed(temp_list)
        for i, card in enumerate(temp_list):
            is_last = (i == len(self.hand) - 1)
            covered = not is_last
            if self.face_up:
                img = self.get_card_bitmap(card, covered)
            else:
                if covered:
                    img = self.card_back_img_covered
                else:
                    img = self.card_back_img

            bmp = img.ConvertToBitmap()
            bmp_ctrl = wx.StaticBitmap(self, bitmap=bmp)
            self.card_controls[card] = bmp_ctrl
            bmp_ctrl.Bind(wx.EVT_LEFT_DOWN, self.on_card_click)


            if self.vertical and not self.horizantal:
                border = 10 if card == self.selected_card else 0
                self.sizer.Add(bmp_ctrl, 0, wx.LEFT, border)
            elif not self.vertical and self.horizantal:
                border = 10 if card == self.selected_card else 0
                self.sizer.Add(bmp_ctrl, 0, wx.TOP, border)
            elif self.vertical and self.horizantal:
                border = 0 if card == self.selected_card else 10
                self.sizer.Add(bmp_ctrl, 0, wx.LEFT, border)
            else:
                border = 0 if card == self.selected_card else 10
                self.sizer.Add(bmp_ctrl, 0, wx.TOP, border)
        self.Fit()
        self.Layout()

    def on_card_click(self, event):


        clicked_ctrl = event.GetEventObject()
        clicked_card = next((c for c, ctrl in self.card_controls.items() if ctrl == clicked_ctrl), None)

        if self.gui:
            self.gui.card_clicked(self, clicked_card)

def join_bridge_game(host, port):
    app = wx.App(False)
    BridgeClientGUI(host, port)  # Replace with actual server IP
    app.MainLoop()