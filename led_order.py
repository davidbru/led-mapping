# Utility functions

def flatten(matrix):
    return [item for row in matrix for item in row]

def reshape_mapping(mapping, cols, offset=0):
    mapping = [val + offset for val in mapping]
    return [mapping[r * cols:(r + 1) * cols] for r in range(len(mapping) // cols)]

def get_panel_info(panel, panel_mapping):
    layout = panel['layout']
    return layout, panel_mapping[layout], get_dims_from_key(layout)

def calculate_offsets(layout_grid, panel_mapping):
    offset = 0
    offsets = []
    for row in layout_grid:
        row_offsets = []
        for panel in row:
            row_offsets.append(offset)
            offset += len(panel_mapping[panel['layout']])
        offsets.append(row_offsets)
    return offsets

def find_value_in_array1_for_value_in_array2(value, array1, array2):
    for row_index, row in enumerate(array2):
        for col_index, element in enumerate(row):
            if element == value:
                return array1[row_index][col_index]
    return None

def get_total_cols(layout_grid):
    return sum(get_dims_from_key(panel['layout'])[0] for panel in layout_grid[0])

def get_total_rows(layout_grid):
    return sum(max(get_dims_from_key(panel['layout'])[1] for panel in row) for row in layout_grid)

def get_leds_per_row(layout_grid, panel_mapping):
    leds_per_row = []
    for row in layout_grid:
        total_leds = sum(len(panel_mapping[panel['layout']]) for panel in row)
        leds_per_row.append(total_leds)
    return leds_per_row

def get_dims_from_key(layout_key):
    """Parses a layout key like '2x3' and returns (cols, rows) as integers"""
    w, h = layout_key.split('x')
    return int(w), int(h)

# Initialize
layout_grid = [
    [{'gpio': 1, 'layout': '2x3'}, {'gpio': 2, 'layout': '4x3'}],
    [{'gpio': 3, 'layout': '4x2'}, {'gpio': 4, 'layout': '2x2'}],
]

panel_mapping = {
    '2x2':  [ 0,  1,
              3,  2],
    '2x3':  [ 0,  1,
              3,  2,
              4,  5],
    '4x2':  [ 0,  7,  1,  6,
              4,  3,  5,  2],
    '4x3':  [ 0, 11,  1, 10,
              8,  3,  9,  2,
              4,  7,  5,  6],
    '5x5':  [ 0, 24,  1, 23,  2,
             20,  4, 21,  3, 22,
              5, 19,  6, 18,  7,
             15,  9, 16,  8, 17,
             10, 14, 11, 13, 12],
    '10x5': [ 0, 49,  1, 48,  2, 47,  3, 46,  4, 45,
             40,  9, 41,  8, 42,  7, 43,  6, 44,  5,
             10, 39, 11, 38, 12, 37, 13, 36, 14, 35,
             30, 19, 31, 18, 32, 17, 33, 16, 34, 15,
             20, 29, 21, 28, 22, 27, 23, 26, 24, 25],
}

total_cols = get_total_cols(layout_grid)
total_rows = get_total_rows(layout_grid)

# Generate full matrix of global LED indices
led_matrix = [[c + r * total_cols for c in range(total_cols)] for r in range(total_rows)]
offsets = calculate_offsets(layout_grid, panel_mapping)
stitched_rows = []

for row_idx, layout_row in enumerate(layout_grid):
    current_rows = get_dims_from_key(layout_row[0]['layout'])[1]
    panel_matrices = []
    for panel_idx, panel in enumerate(layout_row):
        layout, mapping, (cols, rows) = get_panel_info(panel, panel_mapping)
        offset = offsets[row_idx][panel_idx]
        matrix = reshape_mapping(mapping, cols, offset)

        layout_grid[row_idx][panel_idx]['LED_mapping_0_orig'] = mapping
        layout_grid[row_idx][panel_idx]['LED_mapping_1'] = matrix
        layout_grid[row_idx][panel_idx]['LED_mapping_1_flat'] = flatten(matrix)
        panel_matrices.append(matrix)

    for r in range(current_rows):
        row = []
        for matrix in panel_matrices:
            row.extend(matrix[r])
        stitched_rows.append(row)

# Re-map to global layout
for row_idx, layout_row in enumerate(layout_grid):
    for panel_idx, panel in enumerate(layout_row):
        mapping_2 = []
        for r, row in enumerate(panel['LED_mapping_1']):
            new_row = [find_value_in_array1_for_value_in_array2(val, led_matrix, stitched_rows) for val in row]
            mapping_2.append(new_row)

        panel['LED_mapping_2'] = mapping_2
        panel['LED_mapping_2_flat'] = flatten(mapping_2)

        # Reorder to match original mapping order
        ordered = [None] * len(panel['LED_mapping_0_orig'])
        for i, target_index in enumerate(panel['LED_mapping_0_orig']):
            ordered[target_index] = panel['LED_mapping_2_flat'][i]

        panel['LED_mapping_3_flat'] = ordered

# Output final panel maps
final_gpio_output = {}
for row in layout_grid:
    for panel in row:
        final_gpio_output[panel['gpio']] = panel['LED_mapping_3_flat']
        print(f"GPIO {panel['gpio']}: {panel['LED_mapping_3_flat']}")
print(final_gpio_output)
