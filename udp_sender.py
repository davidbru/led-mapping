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

MAP_DEFINITIONS = {
    '1x2': {
        'width': 1,
        'height': 2,
        'mapping': [
            0,
            1
        ]
    },
    '2x2': {
        'width': 2,
        'height': 2,
        'mapping': [
            0, 1,
            3, 2
        ]
    },
    '3x2': {
        'width': 3,
        'height': 2,
        'mapping': [
            0, 1, 2,
            5, 4, 3
        ]
    },
    '4x3': {
        'width': 4,
        'height': 3,
        'mapping': [
            0, 1, 2, 3,
            7, 6, 5, 4,
            8, 9, 10, 11
        ]
    },
    '20x10': {
        'width': 20,
        'height': 10,
        'mapping': [
              0,   1,   2,   3,   4,   5,   6,   7,   8,   9,  10,  11,  12,  13,  14,  15,  16,  17,  18,  19,
             39,  38,  37,  36,  35,  34,  33,  32,  31,  30,  29,  28,  27,  26,  25,  24,  23,  22,  21,  20,
             40,  41,  42,  43,  44,  45,  46,  47,  48,  49,  50,  51,  52,  53,  54,  55,  56,  57,  58,  59,
             79,  78,  77,  76,  75,  74,  73,  72,  71,  70,  69,  68,  67,  66,  65,  64,  63,  62,  61,  60,
             80,  81,  82,  83,  84,  85,  86,  87,  88,  89,  90,  91,  92,  93,  94,  95,  96,  97,  98,  99,
            119, 118, 117, 116, 115, 114, 113, 112, 111, 110, 109, 108, 107, 106, 105, 104, 103, 102, 101, 100,
            120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139,
            159, 158, 157, 156, 155, 154, 153, 152, 151, 150, 149, 148, 147, 146, 145, 144, 143, 142, 141, 140,
            160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 174, 175, 176, 177, 178, 179,
            199, 198, 197, 196, 195, 194, 193, 192, 191, 190, 189, 188, 187, 186, 185, 184, 183, 182, 181, 180
        ]
    }
}

# if
# 'gpio': None
# the panel is not sent to the teensy
SORT = [
    {
        'panels': [
#             {'layout': '4x3', 'gpio': 2},
            {'layout': '2x2', 'gpio': 2},
            {'layout': '3x2', 'gpio': 3}
        ]
    },
    {
        'panels': [
            {'layout': '3x2', 'gpio': None},
            {'layout': '2x2', 'gpio': 5}
        ]
    },
]

gpio_to_indices = {}


# ---------------- #
# HELPER FUNCTIONS #
# ---------------- #
def calculate_panel_properties(panel, definition, global_offset):
    panel['global_offset'] = global_offset
    panel['width'] = definition['width']
    panel['height'] = definition['height']
    panel['mapping_raw'] = definition['mapping']
    return global_offset + definition['width'] * definition['height']

def validate_row_heights(SORT):
    for row_index, row in enumerate(SORT):
        if not row['all_panel_rows_are_equal_height']:
            raise ValueError(f"Row {row_index} has panels of unequal height. Aborting.")

def validate_row_widths(SORT):
    row_widths = [row['panel_row_width'] for row in SORT]
    if len(set(row_widths)) != 1:
        raise ValueError(f"Panel rows have different widths: {row_widths}")

def basic_panel_preparation():
    global MAP_DEFINITIONS
    global SORT
    global gpio_to_indices

    gpio_to_indices = {}  # Initialize or clear the dictionary

    # Add area key to MAP_DEFINITIONS
    for definition in MAP_DEFINITIONS.values():
        definition['area'] = definition['width'] * definition['height']

    global_offset = 0
    for row in SORT:
        row['panel_row_width'] = 0
        heights = set()

        # Step 1: Prepare panels and calculate sizes
        for panel in row['panels']:
            definition = MAP_DEFINITIONS[panel['layout']]
            global_offset = calculate_panel_properties(panel, definition, global_offset)
            row['panel_row_width'] += definition['width']
            heights.add(definition['height'])

        row['panel_row_height'] = max(heights)
        row['all_panel_rows_are_equal_height'] = len(heights) == 1

        # Step 2: Precompute static index mappings for each panel
        row_offset = row['panels'][0]['global_offset']
        panel_row_width = row['panel_row_width']
        panel_row_height = row['panel_row_height']

        current_x = 0
        for panel in row['panels']:
            w, h = panel['width'], panel['height']
            panel_indices = []

            for i in panel['mapping_raw']:
                y = i // w
                x = i % w
                absolute_index = (y * panel_row_width) + (current_x + x)
                panel_indices.append(row_offset + absolute_index)

            # ⬅️ Skip disabled panels
            if panel['gpio'] is not None:
                gpio_to_indices[panel['gpio']] = panel_indices
            current_x += w

    # Check consistency
    validate_row_widths(SORT)
    validate_row_heights(SORT)



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