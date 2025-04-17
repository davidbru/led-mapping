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
	[
		{'gpio': 60, 'layout': '30x5'},
		{'gpio':  2, 'layout': '40x5'},
		{'gpio': 61, 'layout': '30x5'},
	],
	[
		{'gpio': 62, 'layout': '20x10'},
		{'gpio':  3, 'layout': '40x10'},
		{'gpio':  4, 'layout': '20x10'},
		{'gpio': 63, 'layout': '20x10'},
	],
	[
		{'gpio': 64, 'layout': '10x10'},
		{'gpio':  5, 'layout': '40x10'},
		{'gpio':  6, 'layout': '40x10'},
		{'gpio': 65, 'layout': '10x10'},
	],
	[
		{'gpio': 66, 'layout':  '5x10'},
		{'gpio':  7, 'layout': '40x10'},
		{'gpio':  8, 'layout': '40x10'},
		{'gpio':  9, 'layout': '10x10'},
		{'gpio': 67, 'layout':  '5x10'},
	],
	[
		{'gpio': 10, 'layout': '20x20'},
		{'gpio': 11, 'layout': '20x20'},
		{'gpio': 12, 'layout': '20x20'},
		{'gpio': 14, 'layout': '20x20'},
		{'gpio': 15, 'layout': '20x20'},
	],
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
	'5x10': [   0,  49,   1,  48,   2,
			   45,   4,  46,   3,  47,
				5,  44,   6,  43,   7,
			   40,   9,  41,   8,  42,
			   10,  39,  11,  38,  12,
			   35,  14,  36,  13,  37,
			   15,  34,  16,  33,  17,
			   30,  19,  31,  18,  32,
			   20,  29,  21,  28,  22,
			   25,  24,  26,  23,  27],
	'10x5': [   0,  49,   1,  48,   2,  47,   3,  46,   4,  45,
			   40,   9,  41,   8,  42,   7,  43,   6,  44,   5,
			   10,  39,  11,  38,  12,  37,  13,  36,  14,  35,
			   30,  19,  31,  18,  32,  17,  33,  16,  34,  15,
			   20,  29,  21,  28,  22,  27,  23,  26,  24,  25],
	'10x10': [  0,  99,   1,  98,   2,  97,   3,  96,   4,  95,
			   90,   9,  91,   8,  92,   7,  93,   6,  94,   5,
			   10,  89,  11,  88,  12,  87,  13,  86,  14,  85,
			   80,  19,  81,  18,  82,  17,  83,  16,  84,  15,
			   20,  79,  21,  78,  22,  77,  23,  76,  24,  75,
			   70,  29,  71,  28,  72,  27,  73,  26,  74,  25,
			   30,  69,  31,  68,  32,  67,  33,  66,  34,  65,
			   60,  39,  61,  38,  62,  37,  63,  36,  64,  35,
			   40,  59,  41,  58,  42,  57,  43,  56,  44,  55,
			   50,  49,  51,  48,  52,  47,  53,  46,  54,  45],
	'20x5': [   0,  99,   1,  98,   2,  97,   3,  96,   4,  95,   5,  94,   6,  93,   7,  92,   8,  91,   9,  90,
			   80,  19,  81,  18,  82,  17,  83,  16,  84,  15,  85,  14,  86,  13,  87,  12,  88,  11,  89,  10,
			   20,  79,  21,  78,  22,  77,  23,  76,  24,  75,  25,  74,  26,  73,  27,  72,  28,  71,  29,  70,
			   60,  39,  61,  38,  62,  37,  63,  36,  64,  35,  65,  34,  66,  33,  67,  32,  68,  31,  69,  30,
			   40,  59,  41,  58,  42,  57,  43,  56,  44,  55,  45,  54,  46,  53,  47,  52,  48,  51,  49,  50],
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
	# 20x20: pay special attention, how the led stripes are snaking through both panels
	# +---------+
	# | PANEL 2 |
	# +---------+
	# | PANEL 1 |
	# +---------+
	# Panel 2 is mirrored horizontally
	'20x20': [300, 299, 301, 298, 302, 297, 303, 296, 304, 295, 305, 294, 306, 293, 307, 292, 308, 291, 309, 290,
			  280, 319, 281, 318, 282, 317, 283, 316, 284, 315, 285, 314, 286, 313, 287, 312, 288, 311, 289, 310,
			  320, 279, 321, 278, 322, 277, 323, 276, 324, 275, 325, 274, 326, 273, 327, 272, 328, 271, 329, 270,
			  260, 339, 261, 338, 262, 337, 263, 336, 264, 335, 265, 334, 266, 333, 267, 332, 268, 331, 269, 330,
			  340, 259, 341, 258, 342, 257, 343, 256, 344, 255, 345, 254, 346, 253, 347, 252, 348, 251, 349, 250,
			  240, 359, 241, 358, 242, 357, 243, 356, 244, 355, 245, 354, 246, 353, 247, 352, 248, 351, 249, 350,
			  360, 239, 361, 238, 362, 237, 363, 236, 364, 235, 365, 234, 366, 233, 367, 232, 368, 231, 369, 230,
			  220, 379, 221, 378, 222, 377, 223, 376, 224, 375, 225, 374, 226, 373, 227, 372, 228, 371, 229, 370,
			  380, 219, 381, 218, 382, 217, 383, 216, 384, 215, 385, 214, 386, 213, 387, 212, 388, 211, 389, 210,
			  200, 399, 201, 398, 202, 397, 203, 396, 204, 395, 205, 394, 206, 393, 207, 392, 208, 391, 209, 390,
				0, 199,   1, 198,   2, 197,   3, 196,   4, 195,   5, 194,   6, 193,   7, 192,   8, 191,   9, 190,
			  180,  19, 181,  18, 182,  17, 183,  16, 184,  15, 185,  14, 186,  13, 187,  12, 188,  11, 189,  10,
			   20, 179,  21, 178,  22, 177,  23, 176,  24, 175,  25, 174,  26, 173,  27, 172,  28, 171,  29, 170,
			  160,  39, 161,  38, 162,  37, 163,  36, 164,  35, 165,  34, 166,  33, 167,  32, 168,  31, 169,  30,
			   40, 159,  41, 158,  42, 157,  43, 156,  44, 155,  45, 154,  46, 153,  47, 152,  48, 151,  49, 150,
			  140,  59, 141,  58, 142,  57, 143,  56, 144,  55, 145,  54, 146,  53, 147,  52, 148,  51, 149,  50,
			   60, 139,  61, 138,  62, 137,  63, 136,  64, 135,  65, 134,  66, 133,  67, 132,  68, 131,  69, 130,
			  120,  79, 121,  78, 122,  77, 123,  76, 124,  75, 125,  74, 126,  73, 127,  72, 128,  71, 129,  70,
			   80, 119,  81, 118,  82, 117,  83, 116,  84, 115,  85, 114,  86, 113,  87, 112,  88, 111,  89, 110,
			  100,  99, 101,  98, 102,  97, 103,  96, 104,  95, 105,  94, 106,  93, 107,  92, 108,  91, 109,  90],
	'30x5': [   0, 149,   1, 148,   2, 147,   3, 146,   4, 145,   5, 144,   6, 143,   7, 142,   8, 141,   9, 140,  10, 139,  11, 138,  12, 137,  13, 136,  14, 135,
			  120,  29, 121,  28, 122,  27, 123,  26, 124,  25, 125,  24, 126,  23, 127,  22, 128,  21, 129,  20, 130,  19, 131,  18, 132,  17, 133,  16, 134,  15,
			   30, 119,  31, 118,  32, 117,  33, 116,  34, 115,  35, 114,  36, 113,  37, 112,  38, 111,  39, 110,  40, 109,  41, 108,  42, 107,  43, 106,  44, 105,
			   90,  59,  91,  58,  92,  57,  93,  56,  94,  55,  95,  54,  96,  53,  97,  52,  98,  51,  99,  50, 100,  49, 101,  48, 102,  47, 103,  46, 104,  45,
			   60,  89,  61,  88,  62,  87,  63,  86,  64,  85,  65,  84,  66,  83,  67,  82,  68,  81,  69,  80,  70,  79,  71,  78,  72,  77,  73,  76,  74,  75],
	# 40x5: pay special attention, how the led stripes are snaking through both panels
	'40x5': [   0, 199,   1, 198,   2, 197,   3, 196,   4, 195,   5, 194,   6, 193,   7, 192,   8, 191,   9, 190,  10, 189,  11, 188,  12, 187,  13, 186,  14, 185,  15, 184,  16, 183,  17, 182,  18, 181,  19, 180,
			  160,  39, 161,  38, 162,  37, 163,  36, 164,  35, 165,  34, 166,  33, 167,  32, 168,  31, 169,  30, 170,  29, 171,  28, 172,  27, 173,  26, 174,  25, 175,  24, 176,  23, 177,  22, 178,  21, 179,  20,
			   20, 179,  21, 178,  22, 177,  23, 176,  24, 175,  25, 174,  26, 173,  27, 172,  28, 171,  29, 170,  30, 169,  31, 168,  32, 167,  33, 166,  34, 165,  35, 164,  36, 163,  37, 162,  38, 161,  39, 160,
			  140,  59, 141,  58, 142,  57, 143,  56, 144,  55, 145,  54, 146,  53, 147,  52, 148,  51, 149,  50, 150,  49, 151,  48, 152,  47, 153,  46, 154,  45, 155,  44, 156,  43, 157,  42, 158,  41, 159,  40,
			   40, 159,  41, 158,  42, 157,  43, 156,  44, 155,  45, 154,  46, 153,  47, 152,  48, 151,  49, 150,  50, 149,  51, 148,  52, 147,  53, 146,  54, 145,  55, 144,  56, 143,  57, 142,  58, 141,  59, 140],
	# 40x10: pay special attention, how the led stripes are snaking through both panels
	# +---------+---------+
	# | PANEL 2 | PANEL 1 |
	# +---------+---------+
	# Panel 2 is mirrored vertically
	'40x10': [390, 209, 391, 208, 392, 207, 393, 206, 394, 205, 395, 204, 396, 203, 397, 202, 398, 201, 399, 200,   0, 199,   1, 198,   2, 197,   3, 196,   4, 195,   5, 194,   6, 193,   7, 192,   8, 191,   9, 190,
			  210, 389, 211, 388, 212, 387, 213, 386, 214, 385, 215, 384, 216, 383, 217, 382, 218, 381, 219, 380, 180,  19, 181,  18, 182,  17, 183,  16, 184,  15, 185,  14, 186,  13, 187,  12, 188,  11, 189,  10,
			  370, 229, 371, 228, 372, 227, 373, 226, 374, 225, 375, 224, 376, 223, 377, 222, 378, 221, 379, 220,  20, 179,  21, 178,  22, 177,  23, 176,  24, 175,  25, 174,  26, 173,  27, 172,  28, 171,  29, 170,
			  230, 369, 231, 368, 232, 367, 233, 366, 234, 365, 235, 364, 236, 363, 237, 362, 238, 361, 239, 360, 160,  39, 161,  38, 162,  37, 163,  36, 164,  35, 165,  34, 166,  33, 167,  32, 168,  31, 169,  30,
			  350, 249, 351, 248, 352, 247, 353, 246, 354, 245, 355, 244, 356, 243, 357, 242, 358, 241, 359, 240,  40, 159,  41, 158,  42, 157,  43, 156,  44, 155,  45, 154,  46, 153,  47, 152,  48, 151,  49, 150,
			  250, 349, 251, 348, 252, 347, 253, 346, 254, 345, 255, 344, 256, 343, 257, 342, 258, 341, 259, 340, 140,  59, 141,  58, 142,  57, 143,  56, 144,  55, 145,  54, 146,  53, 147,  52, 148,  51, 149,  50,
			  330, 269, 331, 268, 332, 267, 333, 266, 334, 265, 335, 264, 336, 263, 337, 262, 338, 261, 339, 260,  60, 139,  61, 138,  62, 137,  63, 136,  64, 135,  65, 134,  66, 133,  67, 132,  68, 131,  69, 130,
			  270, 329, 271, 328, 272, 327, 273, 326, 274, 325, 275, 324, 276, 323, 277, 322, 278, 321, 279, 320, 120,  79, 121,  78, 122,  77, 123,  76, 124,  75, 125,  74, 126,  73, 127,  72, 128,  71, 129,  70,
			  310, 289, 311, 288, 312, 287, 313, 286, 314, 285, 315, 284, 316, 283, 317, 282, 318, 281, 319, 280,  80, 119,  81, 118,  82, 117,  83, 116,  84, 115,  85, 114,  86, 113,  87, 112,  88, 111,  89, 110,
			  290, 309, 291, 308, 292, 307, 293, 306, 294, 305, 295, 304, 296, 303, 297, 302, 298, 301, 299, 300, 100,  99, 101,  98, 102,  97, 103,  96, 104,  95, 105,  94, 106,  93, 107,  92, 108,  91, 109,  90],
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
		if gpio <= 50:
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