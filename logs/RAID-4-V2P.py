# RAID-4: virtual to physical mapping

# DUMMY Configuration
MAX_SERVERS = 5
TOTAL_NUM_BLOCKS = 64
blocks_per_disk = 16

def get_server_and_block(virtual_block_number, number_of_servers):
    # print('virtual block number:', virtual_block_number, 'number of servers:', number_of_servers)
    if (virtual_block_number < 0 or virtual_block_number > TOTAL_NUM_BLOCKS):
        print('block number is out of bounds')
        quit()
    effective_servers = number_of_servers - 1
    block_number = virtual_block_number // effective_servers
    server_number = virtual_block_number % effective_servers

    return block_number, server_number

def get_parity_block(virtual_block_number):
    # print('virtual block number:', virtual_block_number, 'number of servers:', number_of_servers)
    if (virtual_block_number < 0 or virtual_block_number > TOTAL_NUM_BLOCKS):
        print('block number is out of bounds')
        quit()
    parity_server_id = MAX_SERVERS - 1
    block_number = virtual_block_number // parity_server_id

    return block_number, parity_server_id

def get_other_row_block_numbers(block_index, number_of_servers):
    row_index, column = get_server_and_block(block_index, number_of_servers)
    row_offset = row_index * (number_of_servers - 1)
    blocks = [row_offset + i for i in range(0, number_of_servers - 1) if i != column]
    return blocks