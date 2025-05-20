from PIL import Image, ImageDraw, ImageFont
import os

# Map Suit enum names to Unicode symbols
SUIT_SYMBOLS = {
    'CLUBS': '♣',
    'DIAMONDS': '♦',
    'HEARTS': '♥',
    'SPADES': '♠',
}

# Map values 1-13 to display strings (Ace, 2..10, J, Q, K)
VALUE_STRINGS = {
    13: 'A',
    10: 'J',
    11: 'Q',
    12: 'K'
}

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
CARD_DIR = os.path.join(THIS_DIR, 'cards')

for v in range(1, 10):
    VALUE_STRINGS[v] = str(v+1)

def draw_card(value, suit_name, full=True):
    if full:
        fake_width = 200
    else:
        fake_width = 100
    width, height = 200, 300
    card_color = (255, 255, 255)
    if suit_name in ['HEARTS', 'DIAMONDS']:
        text_color = (220, 20, 60)  # Crimson red
    else:
        text_color = (0, 0, 0)      # Black

    # Create blank white card image
    img = Image.new('RGBA', (fake_width, height), card_color)
    draw = ImageDraw.Draw(img)

    # Load font
    try:
        font = ImageFont.truetype("arial.ttf", 56)
    except IOError:
        font = ImageFont.load_default()

    value_str = VALUE_STRINGS[value]
    suit_symbol = SUIT_SYMBOLS[suit_name]

    # Compose multiline text for corners
    text = f"{value_str}\n{suit_symbol}"

    # Draw top-left text
    draw.multiline_text((10, 10), text, font=font, fill=text_color, spacing=4)

    # Create an image with the text for bottom-right (to rotate)
    text_img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    text_draw = ImageDraw.Draw(text_img)
    text_draw.multiline_text((10, 10), text, font=font, fill=text_color, spacing=4)

    # Rotate the text image 180 degrees
    text_img = text_img.rotate(180, expand=True)

    # Calculate bottom-right position for rotated text
    offset_x = width - text_img.width - 10
    offset_y = height - text_img.height - 10

    # Paste rotated text with transparency
    img.paste(text_img, (offset_x, offset_y), text_img)

    # Draw border
    border_color = (0, 0, 0)
    border_width = 3
    draw.rectangle(
        [(0, 0), (width - 1, height - 1)],
        outline=border_color,
        width=border_width
    )

    # Create output folder if needed
    os.makedirs(CARD_DIR, exist_ok=True)

    # Save file, e.g. "1_of_spades.png"
    if full:
        filename = os.path.join(CARD_DIR, f"{value}_of_{suit_name.lower()}.png")
    else:
        filename = os.path.join(CARD_DIR, f"{value}_of_{suit_name.lower()}_covered.png")
    img.save(filename)
    print(f"Saved {filename}")

def draw_card_back(full=True):
    if full:
        fake_width = 200
    else:
        fake_width = 100
    width, height = 200, 300
    background_color = (150, 0, 0)  # Deep red
    border_color = (255, 255, 255)  # White
    pattern_color = (220, 220, 220)  # Light gray

    img = Image.new('RGB', (fake_width, height), background_color)
    draw = ImageDraw.Draw(img)

    # Draw white border
    border_width = 6
    draw.rectangle(
        [border_width // 2, border_width // 2, width - border_width // 2, height - border_width // 2],
        outline=border_color,
        width=border_width
    )

    # Add diagonal cross pattern
    for i in range(0, width, 20):
        draw.line([(i, 0), (0, i)], fill=pattern_color, width=1)
        draw.line([(width - i, 0), (width, i)], fill=pattern_color, width=1)
        draw.line([(i, height), (0, height - i)], fill=pattern_color, width=1)
        draw.line([(width - i, height), (width, height - i)], fill=pattern_color, width=1)

    # Save and resize
    img = img.resize((60, 90), Image.LANCZOS)
    if full:
        output_path = os.path.join(CARD_DIR, "card_back.png")
    else:
        output_path = os.path.join(CARD_DIR, "card_back_covered.png")
    img.save(output_path)
    print(f"Saved {output_path}")

if __name__ == "__main__":
    for suit in ['CLUBS', 'DIAMONDS', 'HEARTS', 'SPADES']:
        for value in range(1, 14):
            draw_card(value, suit, full=True)
            draw_card(value, suit, full=False)
    draw_card_back(full=True)
    draw_card_back(full=False)