 
# In[]
server_id = 2
servers = 4
# virtual to physical will skip the parity servers while mapping virtual block numbers
parity_block_physical_ids = [servers - int(server_id) - 1 + idx * 4 for idx in range(0, 64)]
print('Failed Parity Blocks Indices: ' + str(parity_block_physical_ids))

def GetStripOffset (block_idx):
    return block_idx  * servers

def GetPhysicalAddressToVirtualBlock(server_index, block_idx):
    return GetStripOffset(block_idx) + server_index
def MapPhysicalAddressToVirtualBlock(server_number, block_idx):
    # logging.debug('Process Physical Address: Server Number - ' + str(server_number) + ', Block Index - ' + str(block_idx))
    
    # number of data servers = #total_servers - #parity_servers
    effective_servers = servers - 1
    
    # Calculate the virtual block number
    block_idx *= effective_servers
    server_number %= effective_servers
    
    # Adjust server number based on parity
    parity_server_number = effective_servers - (block_idx % servers)
    if parity_server_number <= server_number:
        server_number = server_number - 1 if server_number > 0 else effective_servers - 1
    
    # Calculate virtual block number
    virtual_block_number = block_idx + server_number
    
    # logging.debug('P2V RESULTS: Virtual Block Number: ' + str(virtual_block_number))
    return virtual_block_number

data_block_physical_ids = [idx for idx in range(0, 256) if idx not in parity_block_physical_ids]
print('Data Block Indices: ' + str(data_block_physical_ids))
data_block_virtual_ids = [MapPhysicalAddressToVirtualBlock(int(server_id), idx) for idx in data_block_physical_ids]
print(data_block_virtual_ids)
# %%

#%%

server_id = 2
parity_block_ids = []
idx = 0
parity_block_ids = [server_id+1+(int(server_id)-1)+idx*4 for idx in range(0, 64)] # range (0, 64) => total 64 parities are handled by each server
print(parity_block_ids)

server_block_ids = [idx  for idx in range(0, 256)]
print(len(server_block_ids))
print(server_block_ids)

# remove parity blocks from server blocks to get data blocks 
data_block_ids = [x for x in server_block_ids if x not in parity_block_ids]
print(data_block_ids)
print([GetPhysicalAddressToVirtualBlock(server_id, block_id) for block_id in data_block_ids])
# %%
def GetServerAndBlock(virtual_block_number):
    if (virtual_block_number < 0 or virtual_block_number > 1024):
        print('block number is out of bounds')
        quit()
    # number of data servers = #total_servers - #parity_servers
    effective_servers = 4 - 1
    block_number = virtual_block_number // effective_servers
    parity_server_number = effective_servers - (block_number % 4)
    data_server_number = virtual_block_number % effective_servers
    if parity_server_number <= data_server_number:
        data_server_number = data_server_number + 1
    
    # logging.debug('V2P RESULTS: Data Server Number: ' + str(data_server_number) + ' Block Number on Disk: ' + str(block_number))
    return data_server_number, block_number
def GetPhysicalAddressToVirtualBlock(server_index, block_index):
    offset = block_index * 3
    return offset + server_index
def GetParityBlock(block_idx):
    # if (virtual_block_number < 0 or virtual_block_number > 1024):
    #     print('block number is out of bounds')
    #     quit()
    # _, block_number = GetServerAndBlock(virtual_block_number)
    parity_server_id = (4 - 1) - block_idx % 4

    return parity_server_id, block_idx
def VirtualToPhysicalAddress(virtual_block_number):
    # logging.debug('Process Virtual Block Number: ' + str(virtual_block_number))
    server_number, block_number_on_disk = GetServerAndBlock(virtual_block_number)
    return server_number, block_number_on_disk
def GetOtherStripBlockNumbers(virtual_block_number):
    server_id, block_idx = VirtualToPhysicalAddress(virtual_block_number)
    # print('server_id:', server_id, 'block_idx:', block_idx)
    # get the corresponding parity location 
    parity_server_id, parity_block = GetParityBlock(block_idx)
    # print('parity_server_id:', parity_server_id, 'parity_block:', parity_block)
    # get the row offset for the data blocks
    strip_offset = block_idx * (4 - 1)
    # print('strip_offset:', strip_offset)
    strip_blocks = [i + strip_offset for i in range(0, 4 - 1)]
    # print('strip_blocks:', strip_blocks)
    # remove the parity block from the strip blocks
    # strip_blocks.pop(parity_server_id)
    # print('strip_blocks:', strip_blocks)
    # logging.debug('Other Row Blocks Detected: ' + str(strip_blocks))
    return strip_blocks, parity_block, parity_server_id

# %%
for i in range(0, 768):
    print(i, VirtualToPhysicalAddress(i))
    print(i, GetOtherStripBlockNumbers(i))

# %%
Corrupt_block = 9
print(GetOtherStripBlockNumbers(Corrupt_block))
print(VirtualToPhysicalAddress(Corrupt_block))
# %%
# VirtualToPhysicalAddress(4)
# %%
VirtualToPhysicalAddress(5)
# %%
VirtualToPhysicalAddress(764)
# %%
# Parity Test
def CalculateParity(blocks):
    # logging.debug('Calculate Parity for Data Blocks: ' + str(blocks))
    parity = None
    for x in blocks:
        if parity is None:
            parity = x
        else:
            parity = bytearray(a ^ b for a, b in zip(parity, x))
    return parity

# old = bytearray(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
# new_data, parity
blocks = [bytearray(b'.\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00f\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'), bytearray(b'.\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00f\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'), b'.\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00']
# complete_block_array = blocks + [old]
# new_parity = bytearray(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
# expected = bytearray(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
block_1_recovery = CalculateParity(blocks)
print(block_1_recovery)



# %%
# RAID-4 Configuration
MAX_SERVERS = 5
TOTAL_NUM_BLOCKS = 64
blocks_per_disk = 16

# %%

# Raid - 5: virtual to physical address translation

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


# test
for i in range(0, TOTAL_NUM_BLOCKS):
    locate_data = get_server_and_block(i, MAX_SERVERS)
    locate_parity = get_parity_block(i)
    print('virtual block number:', i, 'data_disk:', locate_data[1], 'block_number_on_disk:', locate_data[0], 'parity_server:', locate_parity[1], 'parity_block:', locate_parity[0])

# %%

# recovery
virtual_block_number = 11
# locate_data = get_server_and_block(virtual_block_number, MAX_SERVERS)
# locate_parity = get_parity_block(virtual_block_number)
# print('virtual block number:', virtual_block_number, 'data_disk:', locate_data[1], 'block_number_on_disk:', locate_data[0], 'parity_server:', locate_parity[1], 'parity_block:', locate_parity[0])
row_index, column = get_server_and_block(virtual_block_number, MAX_SERVERS)
row_offset = row_index * (MAX_SERVERS - 1)
# blocks = [row_offset + i for i in range(0, MAX_SERVERS - 1) if i != column]
blocks = [row_offset + i for i in range(0, MAX_SERVERS)]
parity_block = get_parity_block(virtual_block_number)
print('data blocks: ' , blocks)
print('parity block: ', parity_block)
# %%



# %%


# def VirtualToPhysicalAddress(virtual_block_number):
#     if virtual_block_number > TOTAL_NUM_BLOCKS:
#         print('block number is out of bounds')
#         quit()

#     # Calculate the total number of data blocks per disk (excluding parity blocks)
#     data_blocks_per_disk = TOTAL_NUM_BLOCKS // (MAX_SERVERS - 1)
#     total_blocks_per_section = data_blocks_per_disk * (MAX_SERVERS - 1)

#     # Determine the data disk or the parity disk for the given virtual block number
#     if virtual_block_number % total_blocks_per_section == 0:
#         # If the block belongs to the parity disk
#         server_number = MAX_SERVERS - 1  # Parity disk is the last disk
#         block_number_on_disk = virtual_block_number // total_blocks_per_section
#     else:
#         # For data disks
#         server_number = virtual_block_number % (MAX_SERVERS - 1)
        
#         # Calculate the block number within the section for the identified data disk
#         block_within_section = virtual_block_number % total_blocks_per_section
#         block_number_on_disk = block_within_section // (MAX_SERVERS - 1)

#     parity = GetParityBlock(block_number_on_disk)
#     # Output the identified data disk/parity disk and the block number on that disk
#     print('virtual block number: ', virtual_block_number, ' data_disk: ', server_number, 'block_number_on_disk:', block_number_on_disk, 'parity_server:', parity[0], 'parity_block:', parity[1])
#     return server_number, block_number_on_disk

# def GetParityBlock(data_block_number):
#     # Calculate the stripe number containing the given data block
#     data_blocks_per_stripe = (MAX_SERVERS - 1)
#     total_blocks_per_stripe = data_blocks_per_stripe + 1  # Including parity
#     stripe_number = data_block_number // data_blocks_per_stripe

#     # Calculate the index of the parity disk for the stripe
#     parity_disk = (stripe_number % (MAX_SERVERS - 1)) + 1

#     # XOR all data blocks in the stripe (excluding the parity block itself)
#     parity_block = 0
#     for i in range(total_blocks_per_stripe):
#         if i != data_block_number % data_blocks_per_stripe:
#             parity_block ^= stripe_number * data_blocks_per_stripe + i

#     # print('Parity block for data block', data_block_number, 'is on disk', parity_disk, 'with value:', parity_block)
#     return parity_disk, parity_block

# def v2p(vbn):
#     sid = vbn % (MAX_SERVERS-1)
#     # offset = (sid) * blocks_per_disk
#     # bn  = int((vbn - offset) % blocks_per_disk)
#     bn = vbn % blocks_per_disk
#     parity_server = (i % (MAX_SERVERS))
#     print('virtual block number: ', vbn, ' data_disk: ', sid, 'block_number_on_disk:', bn, 'parity_server:', parity_server)
#     return sid, bn

# def v2p(vbn, MaxServers, blocks_per_disk):
#     server_number = vbn // blocks_per_disk  # Calculate the server number
#     sid = server_number % MaxServers  # Calculate the data disk number (sid)
#     bn = vbn % blocks_per_disk  # Calculate the block number on the disk (bn)
#     parity_server = vbn % MaxServers  # Calculate the parity server
#     print('virtual block number:', vbn, 'data_disk:', sid, 'server_number: ', server_number, 'block_number_on_disk:', bn, 'parity_server:', parity_server)
#     return sid, bn

def block_number_translate(virtual_block_number) :
    a = virtual_block_number
    lbn = a/(MAX_SERVERS-1)
    check_server_num = (lbn)%MAX_SERVERS
    check = a+(a/(MAX_SERVERS-1))+1-(a/(MAX_SERVERS-1))*MAX_SERVERS
    if check == check_server_num:
        server_number = check - 1
    else:
        server_number = check
    local_Block_offset = lbn
    
    print('virtual block number:', virtual_block_number, 'data_disk:', server_number, 'block_number_on_disk:', local_Block_offset)
    return server_number, local_Block_offset

# Example usage:
# blocks_per_disk = 16
# for i in range(TOTAL_NUM_BLOCKS):
    # v2p(i)
    # block_number_translate(i)
    # VirtualToPhysicalAddress(i)

# for i in [84, 340, 596]:

# %%

last_block_server = 0

def find_parity_server(vbn):
    return vbn % MAX_SERVERS

# def v2p(vbn):
#     current_server = 

# %%

# for i in range(0, TOTAL_NUM_BLOCKS):
    # VirtualToPhysicalAddress(i)
    # v2p(i, MAX_SERVERS, blocks_per_disk)

# %%
bn = 15

[(i*blocks_per_disk)+bn for i in range(0, MAX_SERVERS)]

for i in range(1, MAX_SERVERS+1):
    if (bn+1) % i == 0: print('Parity Server:', i-1)

# bn = 15
# MAX_SERVERS = 4  # Assuming there are 4 servers

for i in range(1, TOTAL_NUM_BLOCKS):
    # Choose a parity server based on the virtual block number
    parity_server = (i % (MAX_SERVERS - 1)) + 1
    print('Parity Server:', parity_server)


# %%
x = 47
y = 16 
print(x // y)
print(x % y)
print(x / y)
# %%
hex_string = "00000020000200020000000c00000000000000000001000100000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
byte_array = bytearray.fromhex(hex_string)
# print(byte_array)
byte_array.decode('utf-8', errors='ignore')  # Decode as ASCII

# %%
# from sympy.ntheory.modular import solve_congruence

def find_virtual_block_number(server_number, block_number_on_disk, data_blocks_per_disk, MAX_SERVERS):
    # Use the Chinese Remainder Theorem to solve simultaneous congruences
    virtual_block_numbers = []
    
    for k in range(MAX_SERVERS - 1):
        virtual_block_number = k * data_blocks_per_disk + block_number_on_disk
        if virtual_block_number % (MAX_SERVERS - 1) == server_number:
            virtual_block_numbers.append(virtual_block_number)
    
    virtual_block_number_last = block_number_on_disk + (MAX_SERVERS - 1) * data_blocks_per_disk
    if virtual_block_number_last % (MAX_SERVERS - 1) == server_number:
        virtual_block_numbers.append(virtual_block_number_last)

    return virtual_block_numbers if virtual_block_numbers else None

server_number = 3
block_number_on_disk = 10
data_blocks_per_disk = 256
MAX_SERVERS = 4

result = find_virtual_block_number(server_number, block_number_on_disk, data_blocks_per_disk, MAX_SERVERS)
print("Virtual Block Number:", result)

# %%

MAX_SERVERS = 4 
TOTAL_NUM_BLOCKS = 48
blocks_per_disk = 16

def calculate_parity_disk(index, num_disks):
        return num_disks - ((index % num_disks) + 1)

# def calculate_parity_block(index, num_disks):
#     parity_disk = num_disks - ((index % num_disks) + 1)
#     block_number = (index - parity_disk) % (num_disks - 1)
#     return block_number

for i in range(0, TOTAL_NUM_BLOCKS):
    parity = calculate_parity_disk(i, MAX_SERVERS)
    # calculate_parity_block(i, MAX_SERVERS)
    print('virtual block number:', i, 'parity_server:', parity)


# print('\n\n')
# for i in range(0, TOTAL_NUM_BLOCKS):
#     # parity = calculate_parity_disk(i, MAX_SERVERS)
#     parity = calculate_parity_disk(i, MAX_SERVERS)
#     server_number = i % (MAX_SERVERS)
#     block_number_on_disk = i % blocks_per_disk
#     # print('>>> virtual block number: ' + str(i) + ' data_disk: ' + str(server_number) + ' block_number_on_disk: ' + str(block_number_on_disk), "parity_server:", parity)
#     print(str(i), str(server_number), str(block_number_on_disk), parity , '\n')

# data_block_index = stripe_index % (MAX_SERVERS - 1)
# parity_block_index = MAX_SERVERS - 1

# %%

MAX_SERVERS = 4
TOTAL_NUM_BLOCKS = 48
blocks_per_disk = 16

def translate_virtual_block_number(virtual_block_number, disk_count):
    stripe_size = int(blocks_per_disk / disk_count)
    stripe_index = virtual_block_number // stripe_size
    data_block_index = virtual_block_number % stripe_size
    parity_block_index = disk_count - 1

    return stripe_index, data_block_index, parity_block_index


for i in range(TOTAL_NUM_BLOCKS):
    stripe_index, data_block_index, parity_block_index = translate_virtual_block_number(i, MAX_SERVERS)
    print('virtual block number:', i, 'stripe_index:', stripe_index, 'data_block_index:', data_block_index, 'parity_block_index:', parity_block_index)

# %%
MAX_SERVERS = 4
TOTAL_NUM_BLOCKS = 48
blocks_per_disk = 16

for i in range(TOTAL_NUM_BLOCKS):
    # parity_offset = math.ceil(i / MAX_SERVERS)
    # avbn = i + parity_offset 
    # sid = avbn % MAX_SERVERS
    # blockIdx = avbn % blocks_per_disk
    # parity_server = MAX_SERVERS - ((i % MAX_SERVERS) + 1)
    # parity_block = blockIdx
    sid = i % MAX_SERVERS
    blockIdx = i % blocks_per_disk
    parity_server = (i // MAX_SERVERS) ^ (sid // blocks_per_disk)
    parity_block = (i // blocks_per_disk) ^ (i % blocks_per_disk)

    print('virtual block number:', i, 'data_disk:', sid, 'block_number_on_disk:', blockIdx, 'parity_server:', parity_server, 'parity_block:', parity_block)

    # print('virtual block number:', avbn, 'data_disk:', sid, 'block_number_on_disk:', blockIdx, 'parity_server:', parity_server, 'parity_block:', parity_block)

# i = 4
# offset = i / MAX_SERVERS
# avbn = i + offset 
# sid = avbn % MAX_SERVERS
# blockIdx = avbn % blocks_per_disk
# parity_server = MAX_SERVERS - (avbn % MAX_SERVERS) + 1
# parity_block = blockIdx
# print('virtual block number:', avbn, 'data_disk:', sid, 'block_number_on_disk:', blockIdx, 'parity_server:', parity_server, 'parity_block:', parity_block)

parity_participating_blocks = []
for j in range(MAX_SERVERS):
    if j != parity_server:
        parity_participating_blocks.append((j * blocks_per_disk) + blockIdx)
print(parity_participating_blocks)
# %%
def find_elements_twice(nums):
    result = []
    for num in nums:
        if nums.count(num * 2) == 1:
            result.append(num)
    return result

# Example list
numbers = [1, 1, 2]

# Finding elements meeting the condition
find_elements_twice(numbers)
# %%
raw_data = [[2001, 1001, 1],
             [2001, 1002, 2],
             [2001, 1003, 3],
             [2002, 1001, 2],
             [2002, 1002, 1],
             [2002, 1003, 3]]

def print_classification(raw_data):
  # Calculate the points for each racer.
  racer_points = {}
  for race, racer_name, position in raw_data:
    if racer_name not in racer_points:
      racer_points[racer_name] = 0
    if position == 1:
      racer_points[racer_name] += 10
    elif position == 2:
      racer_points[racer_name] += 6
    elif position == 3:
      racer_points[racer_name] += 4
    elif position == 4:
      racer_points[racer_name] += 3
    elif position == 5:
      racer_points[racer_name] += 2
    elif position == 6:
      racer_points[racer_name] += 1

  # Find the winner.
  winner_racer_name = max(racer_points, key=racer_points.get)
  winner_points = racer_points[winner_racer_name]

  # Print the winner.
  print(winner_racer_name, winner_points)

if __name__ == '__main__':
  print_classification(raw_data)