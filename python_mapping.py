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

# Step 1: Build led_group_values preserving insertion order
led_group_values = {}
row_offset = 0

for panel_row in mapping:
    max_height = max(len(panel_definitions[p['used_panel']]) for p in panel_row)
    col_offset = 0

    for panel in panel_row:
        layout = panel_definitions[panel['used_panel']]
        gpio = panel['gpioPin']
        order = panel['orderInGpioPinGroup']

        if gpio not in led_group_values:
            led_group_values[gpio] = {}
        if order not in led_group_values[gpio]:
            led_group_values[gpio][order] = {}

        for r, layout_row in enumerate(layout):
            for c, cell in enumerate(layout_row):
                led_group_values[gpio][order][cell] = original[row_offset + r][col_offset + c]

        col_offset += len(layout[0])
    row_offset += max_height

print("led_group_values:", led_group_values)

# Step 2: Flatten with **sorted order** for output
led_stripe_values_flattened = {
    gpio: [
        value
        for order in sorted(led_group_values[gpio].keys())          # sort by orderInGpioPinGroup
        for cell in sorted(led_group_values[gpio][order].keys())     # sort by cell index
        for value in [led_group_values[gpio][order][cell]]
    ]
    for gpio in sorted(led_group_values.keys())                      # optional: sort GPIOs
}

print("led_stripe_values_flattened:", led_stripe_values_flattened)
