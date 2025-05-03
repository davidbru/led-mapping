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


map_definitions = {
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
}

sort = [
    {
        'panels': [
            {'layout': '1x2', 'gpio': 2},
            {'layout': '2x2', 'gpio': 3},
#             {'layout': '2x2', 'gpio': 3}
        ]
    },
#     {
#         'panels': [
#             {'layout': '2x2', 'gpio': 4},
#             {'layout': '3x2', 'gpio': 5}
#         ]
#     },
]

gpio_to_indices = {}
DEBUG = True
DEBUG_GPIO = 2


# ---------------- #
# HELPER FUNCTIONS #
# ---------------- #
def calculate_panel_properties(panel, definition, global_offset):
    panel['global_offset'] = global_offset
    panel['width'] = definition['width']
    panel['height'] = definition['height']
    panel['mapping_raw'] = definition['mapping']
    return global_offset + definition['width'] * definition['height']

def validate_row_heights(sort):
    for row_index, row in enumerate(sort):
        if not row['all_panel_rows_are_equal_height']:
            raise ValueError(f"Row {row_index} has panels of unequal height. Aborting.")

def validate_row_widths(sort):
    row_widths = [row['panel_row_width'] for row in sort]
    if len(set(row_widths)) != 1:
        raise ValueError(f"Panel rows have different widths: {row_widths}")

def basic_panel_preparation():
    global map_definitions
    global sort
    global gpio_to_indices

    gpio_to_indices = {}  # Initialize or clear the dictionary

    # Add area key to map_definitions
    for definition in map_definitions.values():
        definition['area'] = definition['width'] * definition['height']

    global_offset = 0
    for row in sort:
        row['panel_row_width'] = 0
        heights = set()

        # Step 1: Prepare panels and calculate sizes
        for panel in row['panels']:
            definition = map_definitions[panel['layout']]
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

            gpio_to_indices[panel['gpio']] = panel_indices
            current_x += w

    # Check consistency
    validate_row_widths(sort)
    validate_row_heights(sort)



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
            rgb_list = list(struct.iter_unpack('BBB', byte_array))
            readable = '\n'.join(f"{i:3}: R={r:3} G={g:3} B={b:3}" for i, (r, g, b) in enumerate(rgb_list))
            if DEBUG and DEBUG_GPIO == gpio:
                op('text1').write(f"GPIO {gpio} RGB data:\n{readable}\n")

            op('udpout1').sendBytes(byte_array)


def sizeChange(dat):
    return


basic_panel_preparation()