# copy the content of this script into the touchdesigner file > "datexec1"
# it only sends debug output if it receives new pixel data
# --> static image = no (new) debug infos

# me is this DAT.
#
# dat is the changed DAT.
# rows is a list of row indices.
# cols is a list of column indices.
# cells is the list of cells that have changed content.
# prev is the list of previous string contents of the changed cells.
#
# Make sure the corresponding toggle is enabled in the DAT Execute DAT.
#
# If rows or columns are deleted, sizeChange will be called instead of row/col/cellChange.

import struct  # Only needed for byte-packing


# --------------------------------- #
# VARIABLE AND CONSTANT DEFINITIONS #
# --------------------------------- #
DEBUG = True
GPIO_TO_DEBUG = 2

last_execution_time = 0
MIN_FRAME_INTERVAL = 1.0 / 24.0  # 24 FPS = ~0.0417 seconds between frames

# ----------------------------------
# Your new panel layout definitions
# ----------------------------------
PANEL_DEFINITIONS = {
    '2x2_top_left': [
        [0, 1],
        [3, 2]
    ],
    '2x2_bottom_right': [
        [2, 3],
        [1, 0]
    ],
    '2x3_top_left': [
        [0, 1],
        [5, 2],
        [4, 3]
    ],
    '2x3_bottom_left': [
        [4, 3],
        [5, 2],
        [0, 1]
    ],
}

# MAPPING_DEFINITIONS grid of panels
MAPPING_DEFINITIONS = [
    [
        {'used_panel': '2x2_top_left',    'gpioPin': 2, 'orderInGpioPinGroup': 2},
        {'used_panel': '2x2_bottom_right', 'gpioPin': 3, 'orderInGpioPinGroup': 2},
    ],
#     [
#         {'used_panel': '2x2_bottom_right','gpioPin': 2, 'orderInGpioPinGroup': 3},
#         {'used_panel': '2x2_top_left',    'gpioPin': 3, 'orderInGpioPinGroup': 1},
#     ]
]

gpio_to_indices = {}


# ---------------- #
# HELPER FUNCTIONS #
# ---------------- #
def basic_panel_preparation():
    """
    Build gpio_to_indices using the new PANEL_DEFINITIONS + MAPPING_DEFINITIONS logic.
    Includes consistency checks for row widths and heights.
    """

    global gpio_to_indices
    gpio_to_indices = {}

    # ----------------------------------
    # Precompute row widths and heights for consistency checks
    # ----------------------------------
    row_widths = []
    row_heights = []

    for row_index, panel_row in enumerate(MAPPING_DEFINITIONS):
        width = sum(len(PANEL_DEFINITIONS[p['used_panel']][0]) for p in panel_row)
        heights = [len(PANEL_DEFINITIONS[p['used_panel']]) for p in panel_row]

        if len(set(heights)) != 1:
            raise ValueError(f"Row {row_index} has panels of unequal height: {heights}")

        row_widths.append(width)
        row_heights.append(heights[0])

    if len(set(row_widths)) != 1:
        raise ValueError(f"Panel rows have different total widths: {row_widths}")

    # ----------------------------------
    # Compute LED entries (gpio, order, cellIndex, globalPixelIndex)
    # ----------------------------------
    led_entries = []

    full_width = row_widths[0]  # All rows have same width after consistency check

    row_offset_pixels = 0
    for panel_row in MAPPING_DEFINITIONS:
        max_height = max(len(PANEL_DEFINITIONS[p['used_panel']]) for p in panel_row)
        col_offset_pixels = 0

        for panel in panel_row:
            layout = PANEL_DEFINITIONS[panel['used_panel']]
            gpio = panel['gpioPin']
            order = panel['orderInGpioPinGroup']

            panel_height = len(layout)
            panel_width  = len(layout[0])

            for r, layout_row in enumerate(layout):
                for c, cell_index in enumerate(layout_row):
                    global_pixel_index = (row_offset_pixels + r) * full_width + (col_offset_pixels + c)
                    led_entries.append((gpio, order, cell_index, global_pixel_index))

            col_offset_pixels += panel_width

        row_offset_pixels += max_height

    # ----------------------------------
    # Sort by GPIO → group order → cell index
    # ----------------------------------
    led_entries.sort(key=lambda x: (x[0], x[1], x[2]))

    # ----------------------------------
    # Build gpio_to_indices = {gpio : [globalPixelIndex, ...]}
    # ----------------------------------
    for gpio, _, _, idx in led_entries:
        if gpio is None:
            continue
        gpio_to_indices.setdefault(gpio, []).append(idx)

    if DEBUG and GPIO_TO_DEBUG == gpio:
        for gpio, indices in gpio_to_indices.items():
            print(f"GPIO {gpio} indices: {indices}")


# --------------------------------------- #
# TouchDesigner DAT execute DAT functions #
# --------------------------------------- #
def tableChange(dat):
#     op('text1').clear()
#     op('text1').write('You changed DAT: \n' +str(dat))
    return


def rowChange(dat, rows):
    return


def colChange(dat, cols):
    return


def cellChange(dat, cells, prev):
    global gpio_to_indices
    global last_execution_time
    
    # Throttle execution to 24 FPS
    current_time = absTime.seconds
    if current_time - last_execution_time < MIN_FRAME_INTERVAL:
        return  # Skip this execution
    
    last_execution_time = current_time

    op('text1').clear()

    # Step 1: Parse DAT into list of RGB tuples using dat[i, col]
    raw_rgb_tuples = []
    for i in range(dat.numRows):
        try:
            r = int(dat[i, 0])
            g = int(dat[i, 1])
            b = int(dat[i, 2])
            raw_rgb_tuples.append((r, g, b))
        except (ValueError, TypeError):
            op('text1').write(f"❌ Invalid RGB at row {i}: {dat[i, 0].val}, {dat[i, 1].val}, {dat[i, 2].val}")
            return

    # Step 2: Send one binary packet per GPIO using precomputed indices
    for gpio, indices in gpio_to_indices.items():
        byte_array = bytearray()
        byte_array.append(gpio)  # 1-byte header: GPIO number
        try:
            for i in indices:
                r, g, b = raw_rgb_tuples[i]
                byte_array += struct.pack('BBB', r, g, b)
        except IndexError:
            op('text1').write(f"❌ IndexError: One of the RGB indices for GPIO {gpio} is out of range.")
            continue

        if len(byte_array) > 1450:
            op('text1').write(f"⚠️ GPIO {gpio} packet too large: {len(byte_array)} bytes")
        else:
            # Skip the first byte (the GPIO header)
            rgb_payload = byte_array[1:]
            rgb_list = list(struct.iter_unpack('BBB', rgb_payload))

            if DEBUG and GPIO_TO_DEBUG == gpio:
                readable_lines = []
                for i, (r, g, b) in enumerate(rgb_list):
                    hexval = f"#{r:02X}{g:02X}{b:02X}"
                    readable_lines.append(
                        f"{i:3}: R={r:3} G={g:3} B={b:3}  HEX={hexval}"
                    )

                readable = "\n".join(readable_lines)

                op('text1').write(f"GPIO {gpio} RGB data:\n{readable}\n")

            op('udpout1').sendBytes(byte_array)


def sizeChange(dat):
    return


basic_panel_preparation()