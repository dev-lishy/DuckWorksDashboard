import time
import board
import displayio
import gc
import terminalio
from adafruit_display_text.label import Label
from adafruit_matrixportal.matrixportal import MatrixPortal
from adafruit_matrixportal.network import Network
from gifio import OnDiskGif
from os import getenv

GOLD_COLOR = 0xFFA500
YELLOW_COLOR = 0xFFFF00
GREEN_COLOR = 0x008000
BLUE_COLOR = 0x0000FF
PURPLE_COLOR = 0x4B0082
WHITE_COLOR = 0xEE82EE

def initialize_matrix_portal():
    displayio.release_displays()

    # Initialize MatrixPortal
    return MatrixPortal(status_neopixel=board.NEOPIXEL, width=64, height=64, debug=False)

def render_message(matrix_portal, original_root_group, header, body, header_color=WHITE_COLOR, body_color=WHITE_COLOR):
    try:
        # Colors for guide name
        matrix_portal.display.root_group = original_root_group

        # Create a new text area with the provided text
        matrix_portal.add_text(
            text_font=terminalio.FONT,
            #text_font="/fonts/helvB12.bdf", #Uncomment when we have board with more memory
            text_color=header_color,
            text_position=(2, (matrix_portal.graphics.display.height // 4) - 1),
            text_scale=1.2,
            scrolling=False,
        )
        matrix_portal.add_text(
            text_font=terminalio.FONT,
            text_color=body_color,
            text_position=(1, (matrix_portal.graphics.display.height // 2) - 1),
            text_scale=0.8,
            scrolling=True,
        )

        matrix_portal.set_text(header, 0)
        matrix_portal.set_text(body, 1)

        matrix_portal.scroll_text(0.02)
    except Exception as e:
        print(f"Error rendering message: {e}")
    finally:
        matrix_portal.remove_all_text() # Clean up the text area if needed
        cleanup(matrix_portal)
        gc.collect()
        print("Text area cleared and garbage collection performed.")

def render_gif(matrix_portal, file, seconds):
    print(f"Rendering gif {file} for {seconds} seconds.")

    matrix_portal.display.root_group = gif_group
    odg = None

    try:
        odg = OnDiskGif(file)
        start = time.monotonic()
        next_delay = odg.next_frame()
        end = time.monotonic()
        overhead = end - start  # How long did loading a frame take

        gif_tile = displayio.TileGrid(
            odg.bitmap,
            pixel_shader=displayio.ColorConverter(
                input_colorspace=displayio.Colorspace.RGB565_SWAPPED
            ),
        )
        gif_group.append(gif_tile)

        start = time.monotonic()
        while time.monotonic() < start + seconds:
            frame_shown = time.monotonic()
            matrix_portal.display.refresh()
            next_delay = odg.next_frame()
            time.sleep(max(0, next_delay - overhead))
        gif_group.remove(gif_tile)
    except MemoryError:
        print("MemoryError: Cannot allocate memory for GIF frames.")
    finally:
        if odg:
            odg.deinit()
            odg = None
        cleanup(matrix_portal)
        gc.collect()
        print("GIF rendering complete or interrupted, resources cleaned up.")

def fetch_data_from_api(url, matrix_portal, fieldsOfInterest=[]):
    print("Fetching JSON from", url)

    response = None
    json_data = {}
    values = ['unknown'] * len(fieldsOfInterest)

    try:
        # Fetch data from the URL
        response = matrix_portal.network.fetch(url)
        # Parse JSON data from the response
        json_data = response.json()
        for index, field in enumerate(fieldsOfInterest):
            print('field ' + field)
            values[index] = json_data.get(field, 'unknown')
        del json_data
    except Exception as e:
        print(f"Error fetching data: {e}")
    finally:
        # Ensure the response is closed
        if response:
            try:
                response.close()
                response = None
                matrix_portal.network.response = None
            except Exception as e:
                print(f"Error closing response: {e}")
        cleanup(matrix_portal)
        gc.collect()
        print("Garbage collection performed.")
    return values

def connect_to_wifi(matrix_portal):
    try:
        #font=terminalio.FONT
        #startupLabel = Label(font=font, text="Connecting", color=BLUE_COLOR)
        #matrix_portal.display.root_group = startupLabel
        #font_width, font_height = font.get_bounding_box()
        #startupLabel.x, startupLabel.y = get_text_positions(matrix_portal, startupLabel.text, font)

        # Load secrets
        secrets = {
            "ssid": getenv("CIRCUITPY_WIFI_SSID"),
            "password": getenv("CIRCUITPY_WIFI_PASSWORD"),
        }

        if not secrets["ssid"] or not secrets["password"]:
            print("Wi-Fi credentials not found.")
            #startupLabel.text = "No Wi-Fi"
            #font_width, font_height = font.get_bounding_box()
            #startupLabel.x, startupLabel.y = get_text_positions(matrix_portal, startupLabel.text, font)
            return

        # Connect to Wi-Fi
        print("Connecting to Wi-Fi...")

        # Wait for connection
        while not matrix_portal.network._wifi.is_connected:
            print("Waiting for network connection...")
            matrix_portal.network.connect()

        print("Connected to", secrets["ssid"])
    finally:
        gc.collect()

def cleanup(matrix_portal):
    try:
        gc.collect()
        root_group = matrix_portal.display.root_group
        while len(root_group):
            root_group.pop()

        matrix_portal.display.refresh()
    except Exception as e:
        print(f"Error clearing text area: {e}")

def center_width(width, text_length, font_width):
    return (width - (font_width * text_length)) // 2

def get_text_positions(matrix_portal, text, font):
    font_width, font_height = font.get_bounding_box()
    x = center_width(matrix_portal.display.width, len(text), font_width)
    y = matrix_portal.display.height // 2
    return x, y

def main_loop(matrix_portal):
    original_root_group = matrix_portal.display.root_group

    connect_to_wifi(matrix_portal)
    cleanup(matrix_portal)
    gold_api_url = getenv("GOLD_API_URL")
    print('url = ' + gold_api_url)

    while True:
        # Show GIF for 5 seconds
        render_gif(matrix_portal, './duckWalk.gif', 600)

        # Fetch data from API
        [current_value_gold, percent_change_gold] = fetch_data_from_api(gold_api_url, matrix_portal, ['currentValue', 'percentChange'])

        # Prepare text to display
        gold_info = f"Current value: {current_value_gold}, Percent change: {percent_change_gold}"

        # Render display with new message
        render_message(matrix_portal, original_root_group, 'GOLD', gold_info, header_color=GOLD_COLOR)

gif_group = displayio.Group()

if __name__ == "__main__":
    # Initialize and set up MatrixPortal
    matrix_portal = initialize_matrix_portal()

    # Start main loop
    main_loop(matrix_portal)
