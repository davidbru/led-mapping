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

gpio_to_data = {}


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

    # Add area key to map_definitions
    for definition in map_definitions.values():
        definition['area'] = definition['width'] * definition['height']

    global_offset = 0
    for row in sort:
        row['panel_row_width'] = 0
        heights = set()

        for panel in row['panels']:
            definition = map_definitions[panel['layout']]
            global_offset = calculate_panel_properties(panel, definition, global_offset)
            row['panel_row_width'] += definition['width']
            heights.add(definition['height'])

        row['panel_row_height'] = max(heights)
        row['all_panel_rows_are_equal_height'] = len(heights) == 1


    # Check if all panel rows have have proper width and height
    validate_row_widths(sort)
    validate_row_heights(sort)



# --------------------------------------- #
# TouchDesigner DAT execute DAT functions #
# --------------------------------------- #
def tableChange(dat):
    op('text1').clear()
    #op('text1').write('You changed DAT: \n' +str(dat))
    return


def rowChange(dat, rows):
    return


def colChange(dat, cols):
    return


def cellChange(dat, cells, prev):
    global sort
    global gpio_to_data

    op('text1').clear()

    # Step 1: Flatten DAT into RGB rows
    raw_rgb_rows = [[cell.val for cell in row] for row in dat.rows()]

    # Step 2: Assign input data based on mapping
    for row in sort:
        row_offset = row['panels'][0]['global_offset']
        panel_row_width = row['panel_row_width']
        panel_row_height = row['panel_row_height']

        # Build full 2D grid of characters for the row
        full_grid = [
            raw_rgb_rows[row_offset + y * panel_row_width : row_offset + (y + 1) * panel_row_width]
            for y in range(panel_row_height)
        ]

        # Assign character mappings per panel
        current_x = 0
        for panel in row['panels']:
            w, h = panel['width'], panel['height']
            panel_chars = [ch for y in range(h) for ch in full_grid[y][current_x:current_x + w]]
            panel['mapping_final'] = [panel_chars[i] for i in panel['mapping_raw']]
            current_x += w

    # Step 3: Final GPIO-Data dictionary
    gpio_to_data = {
        panel['gpio']: panel['mapping_final']
        for row in sort
        for panel in row['panels']
    }

    # Step 4: Send one binary packet per GPIO
    for gpio, rgb_values in gpio_to_data.items():
        if gpio <= 50:
            byte_array = bytearray()
            for rgb in rgb_values:
                r, g, b = (int(x) for x in rgb)
                byte_array += struct.pack('BBB', r, g, b)  # 3 bytes per LED

            # Optional: prepend GPIO pin as 1 byte or 2 bytes if needed
            # byte_array = struct.pack('B', gpio) + byte_array  # Uncomment to add GPIO as header

            if len(byte_array) > 1450:
                op('text1').write(f"⚠️ GPIO {gpio} packet too large: {len(byte_array)} bytes")
            else:
                # debug data
                rgb_list = list(struct.iter_unpack('BBB', byte_array))
                readable = '\n'.join(f"{i:3}: R={r:3} G={g:3} B={b:3}" for i, (r, g, b) in enumerate(rgb_list))
                op('text1').write(f"GPIO {gpio} RGB data:\n{readable}\n")

                # send data
                op('udpout1').sendBytes(byte_array)


def sizeChange(dat):
    return


basic_panel_preparation()