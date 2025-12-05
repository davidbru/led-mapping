# works with multiple row

original = [
    ['a', 'b', 'c', 'd'],
    ['e', 'f', 'g', 'h'],
    ['i', 'j', 'k', 'l'],
    ['m', 'n', 'o', 'p'],
    ['q', 'r', 's', 't']
]

panelDefinitions = {
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
        { 'used_panel': '2x3_top_left', 'gpioPin': 2, 'orderInGpioPinGroup': 2 },
        { 'used_panel': '2x3_bottom_left', 'gpioPin': 3, 'orderInGpioPinGroup': 2 },
    ],
    [
        { 'used_panel': '2x2_bottom_right', 'gpioPin': 2, 'orderInGpioPinGroup': 3 },
        { 'used_panel': '2x2_top_left', 'gpioPin': 3, 'orderInGpioPinGroup': 1 },
    ]
]

ledGroupValues = {}
currentPanelsRowHeight = 0
globalOffsetRowTarget = [0]

for varPanelsRow in range(len(mapping)):
    currentPanelRow = mapping[varPanelsRow]
    globalOffsetColTarget = [0]

    for varPanelsRowPanel in range(len(currentPanelRow)):
        currentPanel = currentPanelRow[varPanelsRowPanel]
        currentPanelLayout = panelDefinitions[currentPanel['used_panel']]
        currentPanelsRowHeight = len(currentPanelLayout)

        for varLocalRow in range(len(currentPanelLayout)):
            currentPanelLayoutRow = currentPanelLayout[varLocalRow]
            localOffsetRowTarget = globalOffsetRowTarget[varPanelsRow] + varLocalRow

            for varLocalCol in range(len(currentPanelLayoutRow)):
                currentPanelLayoutRowCell = currentPanelLayoutRow[varLocalCol]
                localOffsetColTarget = globalOffsetColTarget[varPanelsRowPanel] + varLocalCol

                gpioPin = currentPanel['gpioPin']
                order = currentPanel['orderInGpioPinGroup']

                if gpioPin not in ledGroupValues:
                    ledGroupValues[gpioPin] = {}
                if order not in ledGroupValues[gpioPin]:
                    ledGroupValues[gpioPin][order] = {}

                ledGroupValues[gpioPin][order][currentPanelLayoutRowCell] = \
                    original[localOffsetRowTarget][localOffsetColTarget]

        # update column offset
        globalOffsetColTarget.append(
            globalOffsetColTarget[-1] + len(currentPanelLayout[0])
        )

    # update row offset
    globalOffsetRowTarget.append(
        globalOffsetRowTarget[-1] + currentPanelsRowHeight
    )

print("ledGroupValues:", ledGroupValues)

# Flatten the LedGroupValues for output
ledStripeValuesFlattened = {
    group: [
        value
        for section_key, section in sorted(sections.items())  # sort sections
        for key, value in sorted(section.items())            # sort LEDs within section
    ]
    for group, sections in ledGroupValues.items()
}

print("ledStripeValuesFlattened:", ledStripeValuesFlattened)
