input_data = [
    'a', 'b', 'c', 'd', 'e',
    'f', 'g', 'h', 'i', 'j',
    'k', 'l', 'm', 'n', 'o',
    'p', 'q', 'r', 's', 't'
]

map_definitions = {
	'3x2': {
	    'width': 3,
	    'height': 2,
	    'mapping': [
            0, 1, 2,
            5, 4, 3
	    ]
	},
    '2x2': {
	    'width': 2,
	    'height': 2,
        'mapping': [
            0, 1,
            3, 2
        ]
    }
}

sort = [
    {
        'panels': [
            {'layout': '3x2', 'gpio': 2},
            {'layout': '2x2', 'gpio': 3}
        ]
    },
    {
        'panels': [
            {'layout': '2x2', 'gpio': 4},
            {'layout': '3x2', 'gpio': 5}
        ]
    },
]



def calculate_panel_properties(panel, definition, global_offset):
    panel['global_offset'] = global_offset
    panel['width'] = definition['width']
    panel['height'] = definition['height']
    panel['mapping_raw'] = definition['mapping']
    return global_offset + definition['width'] * definition['height']

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


# Check if all panel rows have panels of equal height
for row_index, row in enumerate(sort):
    if not row['all_panel_rows_are_equal_height']:
        raise ValueError(f"Row {row_index} has panels of unequal height. Aborting.")


# Check if all panel rows have the same width
row_widths = [row['panel_row_width'] for row in sort]
if len(set(row_widths)) != 1:
    raise ValueError(f"Panel rows have different widths: {row_widths}")


# Assign input data based on mapping
for row in sort:
    row_offset = row['panels'][0]['global_offset']
    panel_row_width = row['panel_row_width']
    panel_row_height = row['panel_row_height']

    # Build full 2D grid of characters for the row
    full_grid = [
        input_data[row_offset + y * panel_row_width : row_offset + (y + 1) * panel_row_width]
        for y in range(panel_row_height)
    ]

    # Assign character mappings per panel
    current_x = 0
    for panel in row['panels']:
        w, h = panel['width'], panel['height']
        panel_chars = [ch for y in range(h) for ch in full_grid[y][current_x:current_x + w]]
        panel['mapping_final'] = [panel_chars[i] for i in panel['mapping_raw']]
        current_x += w

print(sort)