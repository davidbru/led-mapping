# ------------------------ #
# PANEL DEFINITIONS
# ------------------------ #
PANEL_DEFINITIONS = {
    '2x1_spacer': [
        [0],
        [1]
    ],
    '2x2_top_left': [
        [0, 1],
        [3, 2]
    ],
    '2x2_bottom_right': [
        [2, 3],
        [1, 0]
    ],
}

# ------------------------ #
# MAPPING DEFINITIONS (strip assignment)
# ------------------------ #
MAPPING_DEFINITIONS = [
    [
        {'used_panel': '2x1_spacer', 'strip': None, 'orderInStripGroup': 0},
        {'used_panel': '2x2_bottom_right', 'strip': 0, 'orderInStripGroup': 2},
        {'used_panel': '2x1_spacer', 'strip': None, 'orderInStripGroup': 1},
    ],
    [
        {'used_panel': '2x2_bottom_right', 'strip': 0, 'orderInStripGroup': 1},
        {'used_panel': '2x2_top_left', 'strip': 1, 'orderInStripGroup': 2}
    ],
    [
        {'used_panel': '2x1_spacer', 'strip': None, 'orderInStripGroup': 0},
        {'used_panel': '2x2_bottom_right', 'strip': 1, 'orderInStripGroup': 1},
        {'used_panel': '2x1_spacer', 'strip': None, 'orderInStripGroup': 1},
    ],
]

def build_strip_to_indices(debug=True):
    """Build flattened indices from PANEL_DEFINITIONS + MAPPING_DEFINITIONS"""
    # Precompute row widths/heights
    row_widths = []
    
    for row_index, panel_row in enumerate(MAPPING_DEFINITIONS):
        width = sum(len(PANEL_DEFINITIONS[p['used_panel']][0]) for p in panel_row)
        heights = [len(PANEL_DEFINITIONS[p['used_panel']]) for p in panel_row]

        if len(set(heights)) != 1:
            raise ValueError(f"Row {row_index} has panels of unequal height: {heights}")

        row_widths.append(width)

    if len(set(row_widths)) != 1:
        raise ValueError(f"Panel rows have different total widths: {row_widths}")

    # Build led_entries = (strip, order, cellIndex, globalPixelIndex)
    led_entries = []

    full_width = row_widths[0]

    row_offset_pixels = 0
    for panel_row in MAPPING_DEFINITIONS:
        max_height = max(len(PANEL_DEFINITIONS[p['used_panel']]) for p in panel_row)
        col_offset_pixels = 0

        for panel in panel_row:
            layout = PANEL_DEFINITIONS[panel['used_panel']]
            strip = panel['strip']
            order = panel['orderInStripGroup']

            for r, layout_row in enumerate(layout):
                for c, cell_index in enumerate(layout_row):
                    global_pixel_index = (row_offset_pixels + r) * full_width + (col_offset_pixels + c)
                    led_entries.append((strip, order, cell_index, global_pixel_index))

            col_offset_pixels += len(layout[0])
        row_offset_pixels += max_height

    # Filter out entries where strip is None before sorting
    led_entries = [e for e in led_entries if e[0] is not None]

    # Sort by strip → order → cell index
    led_entries.sort(key=lambda x: (x[0], x[1], x[2]))

    # Build flattened indices
    flattened_indices = [idx for _, _, _, idx in led_entries]

    # Debug
    if debug:
        print(f"Flattened indices (total {len(flattened_indices)}): {flattened_indices}")

    return flattened_indices

build_strip_to_indices()