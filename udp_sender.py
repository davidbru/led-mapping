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
STRIP_TO_DEBUG = 2

last_execution_time = 0
MIN_FRAME_INTERVAL = 1.0 / 24.0  # 24 FPS = ~0.0417 seconds between frames

# ------------------------ #
# PANEL DEFINITIONS
# ------------------------ #
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
    '20x10_top_left': [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19],
        [199, 198, 197, 196, 195, 194, 193, 192, 191, 190, 189, 188, 187, 186, 185, 184, 183, 182, 181, 20],
        [162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 174, 175, 176, 177, 178, 179, 180, 21],
        [161, 160, 159, 158, 157, 156, 155, 154, 153, 152, 151, 150, 149, 148, 147, 146, 145, 144, 143, 22],
        [124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 23],
        [123, 122, 121, 120, 119, 118, 117, 116, 115, 114, 113, 112, 111, 110, 109, 108, 107, 106, 105, 24],
        [86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 25],
        [85, 84, 83, 82, 81, 80, 79, 78, 77, 76, 75, 74, 73, 72, 71, 70, 69, 68, 67, 26],
        [48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 27],
        [47, 46, 45, 44, 43, 42, 41, 40, 39, 38, 37, 36, 35, 34, 33, 32, 31, 30, 29, 28]
    ],
}

# ------------------------ #
# MAPPING DEFINITIONS (strip assignment)
# ------------------------ #
MAPPING_DEFINITIONS = [
    [
        {'used_panel': '20x10_top_left', 'strip': 3, 'orderInStripGroup': 1}
    ],
    [
        {'used_panel': '20x10_top_left', 'strip': 2, 'orderInStripGroup': 1}
    ],
]

strip_to_indices = {}


# ---------------- #
# HELPER FUNCTIONS #
# ---------------- #
def basic_panel_preparation():
    """
    Builds strip_to_indices from PANEL_DEFINITIONS + MAPPING_DEFINITIONS
    """

    global strip_to_indices
    strip_to_indices = {}

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

    # Build led_entries = (strip, order, cellIndex, globalPixelIndex)
    led_entries = []

    full_width = row_widths[0]  # All rows have same width after consistency check

    row_offset_pixels = 0
    for panel_row in MAPPING_DEFINITIONS:
        max_height = max(len(PANEL_DEFINITIONS[p['used_panel']]) for p in panel_row)
        col_offset_pixels = 0

        for panel in panel_row:
            layout = PANEL_DEFINITIONS[panel['used_panel']]
            strip = panel['strip']
            order = panel['orderInStripGroup']

            panel_height = len(layout)
            panel_width  = len(layout[0])

            for r, layout_row in enumerate(layout):
                for c, cell_index in enumerate(layout_row):
                    global_pixel_index = (row_offset_pixels + r) * full_width + (col_offset_pixels + c)
                    led_entries.append((strip, order, cell_index, global_pixel_index))

            col_offset_pixels += panel_width

        row_offset_pixels += max_height

    # Sort by strip → group order → cell index
    led_entries.sort(key=lambda x: (x[0], x[1], x[2]))

    # Build strip_to_indices
    for strip, _, _, idx in led_entries:
        if strip is None:
            continue
        strip_to_indices.setdefault(strip, []).append(idx)

    # Debug print first strip
    if DEBUG and STRIP_TO_DEBUG in strip_to_indices:
        print(f"Strip {STRIP_TO_DEBUG} indices: {strip_to_indices[STRIP_TO_DEBUG]}")

# ------------------------ #
# DAT EXECUTE FUNCTIONS
# ------------------------ #
def tableChange(dat):
#     op('text1').clear()
#     op('text1').write('You changed DAT: \n' +str(dat))
    return


def rowChange(dat, rows):
    return


def colChange(dat, cols):
    return


def cellChange(dat, cells, prev):
    global strip_to_indices
    global last_execution_time
    
    # Throttle execution to 24 FPS
    current_time = absTime.seconds
    if current_time - last_execution_time < MIN_FRAME_INTERVAL:
        return  # Skip this execution
    
    last_execution_time = current_time

    op('text1').clear()

    # parse RGB values from DAT
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

    # send UDP per strip
    for strip, indices in strip_to_indices.items():
        byte_array = bytearray()
        byte_array.append(strip)  # first byte = strip index
        try:
            for i in indices:
                r, g, b = raw_rgb_tuples[i]
                byte_array += struct.pack('BBB', r, g, b)
        except IndexError:
            op('text1').write(f"❌ IndexError for strip {strip}")
            continue

        # debug print first 5 pixels
        if DEBUG and strip == STRIP_TO_DEBUG:
            readable_lines = []
            rgb_payload = byte_array[1:]
            rgb_list = list(struct.iter_unpack('BBB', rgb_payload))
            for i, (r, g, b) in enumerate(rgb_list[:5]):
                hexval = f"#{r:02X}{g:02X}{b:02X}"
                readable_lines.append(f"{i:3}: R={r:3} G={g:3} B={b:3} HEX={hexval}")
            readable = "\n".join(readable_lines)
            op('text1').write(f"Strip {strip} RGB data (first 5):\n{readable}\n")

        op('udpout1').sendBytes(byte_array)

def sizeChange(dat):
    return

# ------------------------ #
# INITIALIZATION
# ------------------------ #
basic_panel_preparation()