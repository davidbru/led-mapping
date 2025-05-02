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



for name, definition in map_definitions.items():
    width = definition['width']
    height = definition['height']
    area = width * height
    definition['area'] = area  # Add new key to each definition


global_offset = 0
for row_index, row in enumerate(sort):
    row['panel_row_width'] = 0
    row['panel_row_height'] = 0
    row['all_panel_rows_are_equal_height'] = True
    for panel_index, panel in enumerate(row['panels']):
        panel['global_offset'] = global_offset
        panel['width'] = map_definitions[panel['layout']]['width']
        panel['height'] = map_definitions[panel['layout']]['height']
        panel['mapping_0_orig'] = map_definitions[panel['layout']]['mapping']
        row['panel_row_width'] += map_definitions[panel['layout']]['width']
        if row['panel_row_height'] != 0:
            if row['panel_row_height'] != map_definitions[panel['layout']]['height']:
                row['all_panel_rows_are_equal_height'] = False
        row['panel_row_height'] = map_definitions[panel['layout']]['height']
        global_offset += map_definitions[panel['layout']]['area']


for row in sort:
    panel_row_height = row['panel_row_height']
    panel_row_width = row['panel_row_width']
    row_offset = row['panels'][0]['global_offset']  # assume leftmost panel defines row start

    # Build the full 2D grid for the entire row
    full_grid = []
    for y in range(panel_row_height):
        start = row_offset + y * panel_row_width
        end = start + panel_row_width
        row_data = input_data[start:end]
        full_grid.append(row_data)

    # Assign mapping_2 to each panel
    current_x = 0
    for panel in row['panels']:
        w = panel['width']
        h = panel['height']
        x_start = current_x
        current_x += w

        # Extract this panel's slice from the full grid
        panel_chars = []
        for y in range(h):
            panel_chars.extend(full_grid[y][x_start:x_start + w])

        # Apply mapping_0_orig
        panel['mapping_1_applied'] = [panel_chars[i] for i in panel['mapping_0_orig']]

# Preview result
print(sort)