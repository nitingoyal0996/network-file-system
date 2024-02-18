# Raid - 5: virtual to physical address translation

# DUMMY Configuration
MAX_SERVERS = 5
TOTAL_NUM_BLOCKS = 64
blocks_per_disk = 16

def get_server_and_block(virtual_block_number, number_of_servers):
    if (virtual_block_number < 0 or virtual_block_number > TOTAL_NUM_BLOCKS):
        print('block number is out of bounds')
        quit()
    effective_servers = number_of_servers - 1
    block_number = virtual_block_number // effective_servers
    parity_server_number = effective_servers - (block_number % MAX_SERVERS)
    data_server_number = virtual_block_number % effective_servers
    if parity_server_number <= data_server_number:
        data_server_number = data_server_number + 1
    
    return block_number, data_server_number

def get_parity_block(virtual_block_number):
    if (virtual_block_number < 0 or virtual_block_number > TOTAL_NUM_BLOCKS):
        print('block number is out of bounds')
        quit()
    block_number, _ = get_server_and_block(virtual_block_number, MAX_SERVERS)
    parity_server_id = MAX_SERVERS - 1 - block_number % MAX_SERVERS

    return block_number, parity_server_id

def get_other_row_block_numbers(block_index, number_of_servers):
    row_index, column = get_server_and_block(block_index, number_of_servers)
    row_offset = row_index * (number_of_servers - 1)
    blocks = [row_offset + i for i in range(0, number_of_servers - 1) if i != column]
    return blocks

def get_physical_to_virtual_address(block_index, server_index):
    offset = block_index * MAX_SERVERS
    return offset + server_index
    

# test
for i in range(0, TOTAL_NUM_BLOCKS):
    locate_data = get_server_and_block(i, MAX_SERVERS)
    locate_parity = get_parity_block(i)
    print('virtual block number:', i, 'data_disk:', locate_data[1], 'block_number_on_disk:', locate_data[0], 'parity_server:', locate_parity[1], 'parity_block:', locate_parity[0])
