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


layout_grid = [
	[{'gpio': 2, 'layout': '20x10'}, {'gpio': 3, 'layout': '20x10'}, {'gpio': 4, 'layout': '20x10'}, {'gpio': 5, 'layout': '20x10'}, {'gpio': 6, 'layout': '20x10'}],
	[{'gpio': 7, 'layout': '20x10'}, {'gpio': 8, 'layout': '20x10'}, {'gpio': 9, 'layout': '20x10'}, {'gpio': 10, 'layout': '20x10'}, {'gpio': 11, 'layout': '20x10'}],
#	 [{'gpio': 1, 'layout': '2x3'}, {'gpio': 2, 'layout': '4x3'}],
#	 [{'gpio': 3, 'layout': '4x2'}, {'gpio': 4, 'layout': '2x2'}],
]

panel_mapping = {
	'2x1':  [   0,   1],
	'2x2':  [   0,   1,
			    3,   2],
	'2x3':  [   0,   1,
			    3,   2,
			    4,   5],
	'4x2':  [   0,   7,   1,   6,
			    4,   3,   5,   2],
	'4x3':  [   0,  11,   1,  10,
			    8,   3,   9,   2,
			    4,   7,   5,   6],
	'5x5':  [   0,  24,   1,  23,   2,
			   20,   4,  21,   3,  22,
			    5,  19,   6,  18,   7,
			   15,   9,  16,   8,  17,
			   10,  14,  11,  13,  12],
	'10x5': [   0,  49,   1,  48,   2,  47,   3,  46,   4,  45,
			   40,   9,  41,   8,  42,   7,  43,   6,  44,   5,
			   10,  39,  11,  38,  12,  37,  13,  36,  14,  35,
			   30,  19,  31,  18,  32,  17,  33,  16,  34,  15,
			   20,  29,  21,  28,  22,  27,  23,  26,  24,  25],
	'20x10': [  0, 199,   1, 198,   2, 197,   3, 196,   4, 195,   5, 194,   6, 193,   7, 192,   8, 191,   9, 190,
			  180,  19, 181,  18, 182,  17, 183,  16, 184,  15, 185,  14, 186,  13, 187,  12, 188,  11, 189,  10,
			   20, 179,  21, 178,  22, 177,  23, 176,  24, 175,  25, 174,  26, 173,  27, 172,  28, 171,  29, 170,
			  160,  39, 161,  38, 162,  37, 163,  36, 164,  35, 165,  34, 166,  33, 167,  32, 168,  31, 169,  30,
			   40, 159,  41, 158,  42, 157,  43, 156,  44, 155,  45, 154,  46, 153,  47, 152,  48, 151,  49, 150,
			  140,  59, 141,  58, 142,  57, 143,  56, 144,  55, 145,  54, 146,  53, 147,  52, 148,  51, 149,  50,
			   60, 139,  61, 138,  62, 137,  63, 136,  64, 135,  65, 134,  66, 133,  67, 132,  68, 131,  69, 130,
			  120,  79, 121,  78, 122,  77, 123,  76, 124,  75, 125,  74, 126,  73, 127,  72, 128,  71, 129,  70,
			   80, 119,  81, 118,  82, 117,  83, 116,  84, 115,  85, 114,  86, 113,  87, 112,  88, 111,  89, 110,
			  100,  99, 101,  98, 102,  97, 103,  96, 104,  95, 105,  94, 106,  93, 107,  92, 108,  91, 109,  90],
}

final_gpio_output = {}



# ----------------- #
# Utility Functions #
# ----------------- #

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



def start():
	global final_gpio_output
	global layout_grid
	global panel_mapping

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
	for row in layout_grid:
		for panel in row:
			final_gpio_output[panel['gpio']] = panel['LED_mapping_3_flat']
			# print(f"GPIO {panel['gpio']}: {panel['LED_mapping_3_flat']}")




def tableChange(dat):
	op('text1').clear()
	#op('text1').write('You changed DAT: \n' +str(dat))
	return


def rowChange(dat, rows):
	return


def colChange(dat, cols):
	return


def cellChange(dat, cells, prev):
	global final_gpio_output

	# Step 1: Flatten DAT into RGB rows
	raw_rgb_rows = [[cell.val for cell in row] for row in dat.rows()]

	# Step 2: Assign global LED index to RGB rows
	global_rgb_map = {}
	offset = 0
	for gpio, indices in final_gpio_output.items():
		for i, global_index in enumerate(indices):
			if offset + i < len(raw_rgb_rows):
				global_rgb_map[global_index] = raw_rgb_rows[offset + i]
		offset += len(indices)

	# Step 3: Send one binary packet per GPIO
	for gpio, global_indices in final_gpio_output.items():
		byte_array = bytearray()
		for global_index in global_indices:
			rgb = global_rgb_map.get(global_index, ['0', '0', '0'])
			r, g, b = (int(x) for x in rgb)
			byte_array += struct.pack('BBB', r, g, b)  # 3 bytes per LED

		# Optional: prepend GPIO pin as 1 byte or 2 bytes if needed
		# byte_array = struct.pack('B', gpio) + byte_array  # Uncomment to add GPIO as header

		if len(byte_array) > 1450:
			op('text1').write(f"⚠️ GPIO {gpio} packet too large: {len(byte_array)} bytes")
		else:
			#op('text1').write(byte_array)
			op('udpout1').sendBytes(byte_array)



def sizeChange(dat):
	return


start()