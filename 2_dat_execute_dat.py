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
		{'gpio':  2, 'layout': '3x2'},
	],
]

panel_mapping = {
	'3x2': [  0,   1,   2,
			  5,   4,   3],
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
	"""Parses a layout key like '3x2' and returns (cols, rows) as integers"""
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
				# debug data
				rgb_list = list(struct.iter_unpack('BBB', byte_array))
				readable = '\n'.join(f"{i:3}: R={r:3} G={g:3} B={b:3}" for i, (r, g, b) in enumerate(rgb_list))
				op('text1').clear()
				op('text1').write(f"GPIO {gpio} RGB data:\n{readable}")

				# send data
				op('udpout1').sendBytes(byte_array)



def sizeChange(dat):
	return


start()