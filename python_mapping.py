original = [
    ['a', 'b', 'c', 'd'],
    ['e', 'f', 'g', 'h'],
    ['i', 'j', 'k', 'l'],
    ['m', 'n', 'o', 'p'],
    ['q', 'r', 's', 't']
]

panel_definitions = {
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

mapping = [
    [
        {'used_panel': '2x3_top_left', 'gpioPin': 2, 'orderInGpioPinGroup': 2},
        {'used_panel': '2x3_bottom_left', 'gpioPin': 3, 'orderInGpioPinGroup': 2},
    ],
    [
        {'used_panel': '2x2_bottom_right', 'gpioPin': 2, 'orderInGpioPinGroup': 3},
        {'used_panel': '2x2_top_left', 'gpioPin': 3, 'orderInGpioPinGroup': 1},
    ]
]

# Build flattened final array directly
led_entries = []

row_offset = 0
for panel_row in mapping:
    max_height = max(len(panel_definitions[p['used_panel']]) for p in panel_row)
    col_offset = 0
    for panel in panel_row:
        layout = panel_definitions[panel['used_panel']]
        gpio = panel['gpioPin']
        order = panel['orderInGpioPinGroup']

        for r, layout_row in enumerate(layout):
            for c, cell in enumerate(layout_row):
                led_entries.append((gpio, order, cell, original[row_offset + r][col_offset + c]))

        col_offset += len(layout[0])
    row_offset += max_height

# Sort by (gpio, orderInGpioPinGroup, cell index) to get correct flattened order
led_entries.sort(key=lambda x: (x[0], x[1], x[2]))

# Extract only the values for the final flattened array
led_stripe_values_flattened = {}
for gpio, _, _, value in led_entries:
    led_stripe_values_flattened.setdefault(gpio, []).append(value)

print("led_stripe_values_flattened:", led_stripe_values_flattened)
