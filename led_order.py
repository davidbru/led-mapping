# Panel mapping: physical wiring order (0-based LED numbers)
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

# Panel layout in grid format (row-major)
layout_grid = [
    [
        {'gpio': 1, 'layout': '2x3'}, {'gpio': 2, 'layout': '4x3'}
    ],
    [
        {'gpio': 3, 'layout': '4x2'}, {'gpio': 4, 'layout': '2x2'}
    ],
]

# Panel dimensions: (cols, rows)
panel_dims = {
    '2x3': (2, 3),
    '2x2': (2, 2),
    '4x2': (4, 2),
    '4x3': (4, 3),
}

# Total global layout dimensions
def get_total_cols():
    return sum(panel_dims[panel['layout']][0] for panel in layout_grid[0])

def get_total_rows():
    return sum(max(panel_dims[panel['layout']][1] for panel in row) for row in layout_grid)

def get_leds_per_row(layout_grid, panel_mapping):
    leds_per_row = []

    for row in layout_grid:
        total_leds = 0
        for panel in row:
            layout = panel['layout']
            total_leds += len(panel_mapping[layout])
        leds_per_row.append(total_leds)

    return leds_per_row

def find_value_in_array1_for_value_in_array2(value, array1, array2):
    for row_index, row in enumerate(array2):
        for col_index, element in enumerate(row):
            if element == value:
                return array1[row_index][col_index]
    return None  # if value not found

total_cols = get_total_cols()
total_rows = get_total_rows()
print(f"Global layout dimensions: {total_cols} x {total_rows} rows")



led_matrix = []
counter = 0
for r in range(total_rows):
    row = []
    for c in range(total_cols):
        row.append(counter)
        counter += 1
    led_matrix.append(row)




leds_per_row = get_leds_per_row(layout_grid, panel_mapping);
print(f"LEDs per row: {leds_per_row}\n")



global_led_order = {}  # key = gpio, value = list of global indices


# Iterate through each panel and print its GPIO and mapping
for row_index, row in enumerate(layout_grid):
    for panel in row:
        gpio = panel['gpio']
        layout = panel['layout']
        mapping = panel_mapping[layout]
        print(f"GPIO {gpio} ({layout}): {mapping}")
print("")


# Print panel mappings row by row
leds_so_far = 0
stitched_rows = []
for layout_index, layout_row in enumerate(layout_grid):
#     print(f"LEDs so far: {leds_so_far}")
    row_panels = []

    # all panels in the same row must have the same amount of rows
    # --> just take the first panel and extract the rows
    current_rows = panel_dims[layout_row[0]['layout']][1]

    # Build per-panel rows
    panel_rows = []

    for panel_index, panel in enumerate(layout_row):
        layout = panel['layout']
        mapping = panel_mapping[layout]
        mapping_increased = [val + leds_so_far for val in mapping]
        cols, rows = panel_dims[layout]

        # Reshape panel mapping to 2D row-major
        panel_matrix = [
            mapping_increased[r * cols:(r + 1) * cols]
            for r in range(rows)
        ]

        layout_grid[layout_index][panel_index]['LED_mapping_0_orig'] = panel_mapping[layout_grid[layout_index][panel_index]['layout']]
        layout_grid[layout_index][panel_index]['LED_mapping_1'] = panel_matrix
        layout_grid[layout_index][panel_index]['LED_mapping_1_flat'] = [item for row in panel_matrix for item in row]

        panel_rows.append(panel_matrix)
        leds_so_far += len(panel_mapping[panel['layout']])


    # Stitch together all rows for this layout_row
    for row_index, row in enumerate(range(current_rows)):
        stitched_row = []
        for panel_matrix in panel_rows:
            stitched_row.extend(panel_matrix[row])
        stitched_rows.append(stitched_row)


for layout_index, layout_row in enumerate(layout_grid):
    for panel_index, panel in enumerate(layout_row):
        led_mapping_2 = []
        for row_index, row in enumerate(panel['LED_mapping_1']):
            tmp_led_mapping_row = []
            for col_index, col in enumerate(row):
                corresponding_value = find_value_in_array1_for_value_in_array2(col, led_matrix, stitched_rows)
                tmp_led_mapping_row.append(corresponding_value)

            led_mapping_2.append(tmp_led_mapping_row)
        layout_grid[layout_index][panel_index]['LED_mapping_2'] = led_mapping_2
        layout_grid[layout_index][panel_index]['LED_mapping_2_flat'] = [item for row in led_mapping_2 for item in row]

        ordered = [None] * len(layout_grid[layout_index][panel_index]['LED_mapping_0_orig'])
        for i, target_index in enumerate(layout_grid[layout_index][panel_index]['LED_mapping_0_orig']):
            ordered[target_index] = layout_grid[layout_index][panel_index]['LED_mapping_2_flat'][i]

        layout_grid[layout_index][panel_index]['LED_mapping_3_flat'] = ordered


for layout_index, layout_row in enumerate(layout_grid):
    for panel_index, panel in enumerate(layout_row):
        print(f"{panel['gpio']}: {panel['LED_mapping_3_flat']}")
