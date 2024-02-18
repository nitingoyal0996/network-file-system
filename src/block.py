import pickle, logging
import fsconfig
import xmlrpc.client, socket, time
import math
#### BLOCK LAYER

# global TOTAL_NUM_BLOCKS, BLOCK_SIZE, INODE_SIZE, MAX_NUM_INODES, MAX_FILENAME, INODE_NUMBER_DIRENTRY_SIZE

class DiskBlocks():
    def __init__(self):

        # initialize clientID
        if fsconfig.CID >= 0 and fsconfig.CID < fsconfig.MAX_CLIENTS:
            self.clientID = fsconfig.CID
        else:
            print('Must specify valid cid')
            quit()

        # initialize XMLRPC client connection to raw block server
        if fsconfig.START_PORT_NUM:
            START_PORT_NUM = fsconfig.START_PORT_NUM
        else:
            print('Must specify a starting port number')
            quit()

        socket.setdefaulttimeout(fsconfig.SOCKET_TIMEOUT)
        
        self.block_servers = {}
        for i in range(0, fsconfig.MAX_SERVERS):
            server_address = 'http://' + fsconfig.SERVER_ADDRESS + ':' + str(START_PORT_NUM + i)
            self.block_servers[i] = xmlrpc.client.ServerProxy(server_address, use_builtin_types=True)
        
        # initialize block cache empty
        self.blockcache = {}

        self.parity_server_idx = fsconfig.MAX_SERVERS - 1
        self.data_blocks_per_disk = int((fsconfig.TOTAL_NUM_BLOCKS / (fsconfig.MAX_SERVERS)))
        
    # validates whether the cache logging is enabled by the user or not
    def print_cache_logs(self, message):
        if fsconfig.LOG_CACHE != False:
            print(message)

    ## Put: interface to write a raw block of data to the block indexed by block number
    ## Blocks are padded with zeroes up to BLOCK_SIZE
    def Put(self, block_number, block_data):

        logging.debug('Put: ' + str(block_number) + ' len ' + str(len(block_data)))
        if len(block_data) > fsconfig.BLOCK_SIZE:
            logging.debug('error: Put: Block larger than BLOCK_SIZE: ' + str(len(block_data)))
            quit()

        if block_number in range(0, fsconfig.TOTAL_NUM_BLOCKS):
            old_data = self.Get(block_number)
            # ljust does the padding with zeros
            put_data = bytearray(block_data.ljust(fsconfig.BLOCK_SIZE, b'\x00'))
            block_location = self.MapVirtualBlockToPhysicalAddress(block_number)
            data = self.SinglePut(block_location[0], block_location[1], put_data)
            logging.debug('DATA PUT: ' + str(put_data) + ' \nServer ID: ' + str(block_location[0]) + ' \nBlock Number: ' + str(block_location[1]))
            
            # update parity
            # if block_number != fsconfig.TOTAL_NUM_BLOCKS - 1:
            parity = self.GetParity(block_location[1], put_data, old_data)
            parity_data, parity_server = parity[0], parity[1]
            logging.debug('Initiate Parity Update At: ' + str(block_location[1]) + ' Parity Server: ' + str(parity_server))
            parity_data = self.SinglePut(parity_server, block_location[1], parity_data)
            logging.debug('PARITY PUT: ' + str(block_location[1]) + ' \nParity Server ID: ' + str(parity_server) + ' \nParity: ' + str(parity_data))

            # error handling
            if data == -1 and parity_data == -1:
                logging.debug('PUT: Multiple Server Failures')
                quit()
            elif data == -1:
                # continue operation: Not Possible
                # self.Put(block_number + 1, put_data) # retry write to the next available block this would override the existing data on a different block, which is incorrect.
                logging.debug('PUT: Server Disconnected: ' + str(block_number))
                print(f'SERVER_DISCONNECTED: {block_number}')
            elif parity_data == -1:
                # continue operation: Not Possible
                # if we retry parity write to the next available block - how would we access this back, since the deterministic pattern is broken?
                logging.debug('PUT: Parity Server Disconnected: ' + str(block_number))
                print(f'SERVER_DISCONNECTED: {block_number}')
            elif data == -2 or parity_data == -2:
                print(f'SERVER_TIMED_OUT {block_number}')
                logging.debug('PARITY LAST_WRITER PUT: ' + str(block_location[1]) + ' \nParity Server ID: ' + str(parity_server) + ' \nParity: ' + str(parity_data))
                quit()

            # TODO: uncomment update block cache
            self.print_cache_logs('CACHE_WRITE_THROUGH ' + str(block_number))
            self.blockcache[block_number] = put_data
            
            # flag this is the last writer
            # unless this is a release - which doesn't flag last writer
            if block_number != fsconfig.TOTAL_NUM_BLOCKS - 1:
                LAST_WRITER_BLOCK = fsconfig.TOTAL_NUM_BLOCKS - 2

                block_location = self.MapVirtualBlockToPhysicalAddress(LAST_WRITER_BLOCK)
                updated_block = bytearray(fsconfig.BLOCK_SIZE)
                updated_block[0] = fsconfig.CID
                old_data = self.Get(LAST_WRITER_BLOCK)
                data = self.SinglePut(block_location[0], block_location[1], updated_block)
                
                # fetch parity location
                # parity = self.GetParity(block_location[1], updated_block, old_data)
                # parity_data, parity_server = parity[0], parity[1]
                # logging.debug('Initiate Parity Update At LAST_WRITER: ' + str(block_location[1]) + ' Parity Server: ' + str(parity_server))
                # parity_data = self.SinglePut(parity_server, block_location[1], parity_data)
                
                # error handling
                # if data == -1 and parity_data == -1:
                #     logging.debug('Last Writer: Put: Multiple Server Failures')
                #     # quit()
                if data == -1:
                    logging.debug('Last Writer: Put: Server Disconnected: ' + str(block_number))
                    print(f'SERVER_DISCONNECTED: {block_number}')
                # elif parity_data == -1:
                #     logging.debug('Last Writer: Put: Parity Server Disconnected: ' + str(block_number))
                #     print(f'SERVER_DISCONNECTED: {block_number}')
                elif data == -2:
                    logging.debug('PARITY LAST_WRITER PUT: ' + str(block_location[1]) + ' \nParity Server ID: ' + str(parity_server) + ' \nParity: ' + str(parity_data))
                    print(f'SERVER_TIMED_OUT {block_number}')
            return data
        else:
            logging.debug('ERROR: Put: Block out of range: ' + str(block_number))
            quit()

    ## Get: interface to read a raw block of data from block indexed by block number
    ## Equivalent to the textbook's BLOCK_NUMBER_TO_BLOCK(b)
    def Get(self, block_number):

        logging.debug('Get: ' + str(block_number))
        if block_number in range(0, fsconfig.TOTAL_NUM_BLOCKS):
            # except data and parity blocks - do not use cache
            if (block_number < fsconfig.TOTAL_NUM_BLOCKS - 2 or block_number > fsconfig.TOTAL_NUM_BLOCKS) and (block_number in self.blockcache):
                self.print_cache_logs('CACHE_HIT '+ str(block_number))
                data = self.blockcache[block_number]
            else:
                self.print_cache_logs('CACHE_MISS ' + str(block_number))
                
                block_location = self.MapVirtualBlockToPhysicalAddress(block_number)
                ret = self.SingleGet(block_location[0], block_location[1])
                data, has_error = ret[0], ret[1]

                if data == -1:
                    print(f'SERVER_DISCONNECTED {block_number}')
                    # continue function: recover the data from other servers and parity for that data strip and return
                    data = self.RecoverDataBlock(block_location, block_number)
                elif data == -2: 
                    print(f'SERVER_TIMED_OUT {block_number}')
                    # retry = True
                elif has_error:
                    logging.debug('CHECKSUM_ERROR DETECTED: ' + str(block_number))
                    print(f'CORRUPTED_BLOCK {block_number}')
                    # recover the corrupted block
                    data = self.RecoverDataBlock(block_location, block_number)
                    
                # TODO: add data to cache
                self.blockcache[block_number] = data
            
            return bytearray(data)

        logging.debug('ERROR: DiskBlocks::Get: Block number larger than TOTAL_NUM_BLOCKS: ' + str(block_number) + ' ' + str(fsconfig.TOTAL_NUM_BLOCKS))
        quit()

    ## RSM: read and set memory equivalent
    def RSM(self, block_number):
        logging.debug('RSM: ' + str(block_number))

        if block_number in range(0, fsconfig.TOTAL_NUM_BLOCKS):
            block_location = self.MapVirtualBlockToPhysicalAddress(block_number)
            ret = self.SingleRSM(block_location[0], block_location[1])
            data, has_error = ret[0], ret[1]

            if data == -1:
                print(f'SERVER_DISCONNECTED RSM {block_number}')
                # continue function: recover the data from other servers and parity for that data strip and return
                data = self.RecoverDataBlock(block_location, block_number)
            if data == -2: 
                print(f'SERVER_TIMED_OUT RSM {block_number}')
            if has_error:
                logging.debug('CHECKSUM_ERROR DETECTED ON RSM: ' + str(block_number))
                print(f'RSM CORRUPTED_BLOCK {block_number}')
                # recover the corrupted block
                data = self.RecoverDataBlock(block_location, block_number)
                
            return bytearray(data)

        logging.debug('ERROR: RSM: Block number larger than TOTAL_NUM_BLOCKS: ' + str(block_number))
        quit()

    ## Acquire and Release using a disk block lock
    def Acquire(self):
        logging.debug('Acquire')
        RSM_BLOCK = fsconfig.TOTAL_NUM_BLOCKS - 1
        lockvalue = self.RSM(RSM_BLOCK);
        logging.debug("RSM_BLOCK Lock value: " + str(lockvalue))
        while lockvalue[0] == 1:  # test just first byte of block to check if RSM_LOCKED
            logging.debug("Acquire: spinning...")
            lockvalue = self.RSM(RSM_BLOCK);
        # once the lock is acquired, check if need to invalidate cache
        self.CheckAndInvalidateCache()
        return 0

    def Release(self):
        logging.debug('Release')
        RSM_BLOCK = fsconfig.TOTAL_NUM_BLOCKS - 1
        # Put()s a zero-filled block to release lock
        self.Put(RSM_BLOCK,bytearray(fsconfig.RSM_UNLOCKED.ljust(fsconfig.BLOCK_SIZE, b'\x00')))
        return 0

    def CheckAndInvalidateCache(self):
        # logging.debug('Check and Invalidate Cache')
        LAST_WRITER_BLOCK = fsconfig.TOTAL_NUM_BLOCKS - 2
        last_writer = self.Get(LAST_WRITER_BLOCK)
        # if ID of last writer is not self, invalidate and update
        if last_writer[0] != fsconfig.CID:
            self.print_cache_logs("CACHE_INVALIDATED")
            self.blockcache = {}
            updated_block = bytearray(fsconfig.BLOCK_SIZE)
            updated_block[0] = fsconfig.CID
            self.Put(LAST_WRITER_BLOCK,updated_block)

    ## Serializes and saves the DiskBlocks block[] data structure to a "dump" file on your disk
    def DumpToDisk(self, filename):

        logging.info("DiskBlocks::DumpToDisk: Dumping pickled blocks to file " + filename)
        file = open(filename,'wb')
        file_system_constants = "BS_" + str(fsconfig.BLOCK_SIZE) + "_NB_" + str((fsconfig.TOTAL_NUM_BLOCKS - self.data_blocks_per_disk)) + "_IS_" + str(fsconfig.INODE_SIZE) \
                            + "_MI_" + str(fsconfig.MAX_NUM_INODES) + "_MF_" + str(fsconfig.MAX_FILENAME) + "_IDS_" + str(fsconfig.INODE_NUMBER_DIRENTRY_SIZE)
        pickle.dump(file_system_constants, file)
        pickle.dump(self.block, file)

        file.close()

    ## Loads DiskBlocks block[] data structure from a "dump" file on your disk
    def LoadFromDump(self, filename):

        logging.info("DiskBlocks::LoadFromDump: Reading blocks from pickled file " + filename)
        file = open(filename,'rb')
        file_system_constants = "BS_" + str(fsconfig.BLOCK_SIZE) + "_NB_" + str((fsconfig.TOTAL_NUM_BLOCKS - self.data_blocks_per_disk)) + "_IS_" + str(fsconfig.INODE_SIZE) \
                            + "_MI_" + str(fsconfig.MAX_NUM_INODES) + "_MF_" + str(fsconfig.MAX_FILENAME) + "_IDS_" + str(fsconfig.INODE_NUMBER_DIRENTRY_SIZE)

        try:
            read_file_system_constants = pickle.load(file)
            if file_system_constants != read_file_system_constants:
                print('DiskBlocks::LoadFromDump Error: File System constants of File :' + read_file_system_constants + ' do not match with current file system constants :' + file_system_constants)
                return -1
            block = pickle.load(file)
            for i in range(0, (fsconfig.TOTAL_NUM_BLOCKS - self.data_blocks_per_disk)):
                self.Put(i,block[i])
            return 0
        except TypeError:
            print("DiskBlocks::LoadFromDump: Error: File not in proper format, encountered type error ")
            return -1
        except EOFError:
            print("DiskBlocks::LoadFromDump: Error: File not in proper format, encountered EOFError error ")
            return -1
        finally:
            file.close()

    def PrintBlocks(self,tag,min,max):
        print ('#### Raw disk blocks: ' + tag)
        for i in range(min,max):
            print ('Block [' + str(i) + '] : ' + str((self.Get(i)).hex()))

    #############################################################################
    # Mapping: Virtual to Physical Address Functions
    #############################################################################
    def GetParityServer(self, block_idx):
        parity_server_id = (fsconfig.MAX_SERVERS - 1) - block_idx % fsconfig.MAX_SERVERS
        return parity_server_id, block_idx

    def GetBlockNumberAcrossServers(self, block_idx):
        logging.debug('Retrieve Block Number Across Servers for Block Index: ' + str(block_idx))
        
        # number of data servers = #total_servers - #parity_servers
        effective_servers = fsconfig.MAX_SERVERS - 1
        
        # Calculate the block number across all servers in the strip
        block_number_across_servers = []
        for server_number in range(effective_servers):
            virtual_block_number = block_idx * effective_servers + server_number
            
            # Adjust server number based on parity
            parity_server_number = effective_servers - (block_idx % fsconfig.MAX_SERVERS)
            if parity_server_number <= server_number:
                server_number = server_number - 1 if server_number > 0 else effective_servers - 1
            
            block_number_across_servers.append(virtual_block_number)
        
        logging.debug('Block Number Across Servers for Block Index ' + str(block_idx) + ': ' + str(block_number_across_servers))
        return block_number_across_servers, block_idx, parity_server_number 

    def MapVirtualBlockToPhysicalAddress(self, virtual_block_number):
        logging.debug('Process Virtual Block Number: ' + str(virtual_block_number))
        if (virtual_block_number < 0 or virtual_block_number > fsconfig.TOTAL_NUM_BLOCKS):
            print('block number is out of bounds')
            quit()
        # number of data servers = #total_servers - #parity_servers
        effective_servers = fsconfig.MAX_SERVERS - 1
        block_idx = virtual_block_number // effective_servers
        parity_server_number = effective_servers - (block_idx % fsconfig.MAX_SERVERS)
        server_number = virtual_block_number % effective_servers
        if parity_server_number <= server_number:
            server_number = server_number + 1
        
        logging.debug('V2P RESULTS: Data Server Number: ' + str(server_number) + ' Block Number on Disk: ' + str(block_idx))
        return server_number, block_idx

    def MapPhysicalAddressToVirtualBlock(self, server_number, block_idx):
        logging.debug('Process Physical Address: Server Number - ' + str(server_number) + ', Block Index - ' + str(block_idx))
        
        # number of data servers = #total_servers - #parity_servers
        effective_servers = fsconfig.MAX_SERVERS - 1
        
        # Calculate the virtual block number
        block_idx *= effective_servers
        server_number %= effective_servers
        
        # Adjust server number based on parity
        parity_server_number = effective_servers - (block_idx % fsconfig.MAX_SERVERS)
        if parity_server_number <= server_number:
            server_number = server_number - 1 if server_number > 0 else effective_servers - 1
        
        # Calculate virtual block number
        virtual_block_number = block_idx + server_number
        
        logging.debug('P2V RESULTS: Virtual Block Number: ' + str(virtual_block_number))
        return virtual_block_number

    #############################################################################
    # Parity: Block AND Server Recovery Functions
    #############################################################################
    def CalculateParity(self, blocks):
        logging.debug('Calculate Parity for Data Blocks: ' + str(blocks))
        parity = None
        for x in blocks:
            if parity is None:
                parity = x
            else:
                parity = bytearray(a ^ b for a, b in zip(parity, x))
        return parity
    
    def FetchDataBlocks(self, blocks):
        logging.debug('Fetch Data Blocks: ' + str(blocks))
        data_blocks = [
            self.Get(block_number)
            for block_number in blocks
        ]
        logging.debug('Data Blocks: ' + str(data_blocks))
        return data_blocks

    def GetParity(self, block_idx, new_data, old_data):
        logging.debug('Process Parity for Location: ' + str(block_idx))
        logging.debug('Old Data: ' + str(old_data) + ' \nNew Data: ' + str(new_data))

        # if the block_data and the parity previously was not empty - we could XOR the old_data, new_data and the old_parity to calculate the new parity
        # else when there is no parity - we could calculate the parity by XORing all the participating data blocks in the stripe
        # filter participating_blocks to remove the parity block
        parity_location = self.GetParityServer(block_idx)
        parity_server, parity_block = parity_location[0], parity_location[1]
        logging.debug('Parity Server: ' + str(parity_server) + ' Parity Block Index: ' + str(parity_block))

        ret = self.SingleGet(parity_server, parity_block)
        old_parity, _ = ret[0], ret[1]
        logging.debug('Old Parity: ' + str(old_parity))
        # error handling
        if old_parity == -1:
            logging.debug('Parity Server Disconnected: ' + str(block_idx) + ' Parity Server: ' + str(parity_server))
            print(f'SERVER_DISCONNECTED: {block_idx}')
            # recover parity block
            old_parity = self.RecoverParityBlock(block_idx) 
        
        if old_data != bytearray(b'\x00' * fsconfig.BLOCK_SIZE) and old_parity != bytearray(b'\x00' * fsconfig.BLOCK_SIZE):
            logging.debug('Parity: Update')
            data = [old_data, new_data, old_parity]
        else:
            # create parity with data on the strip - data blocks
            logging.debug('Parity: Create')
            strip = self.GetBlockNumberAcrossServers(block_idx)
            blocks = strip[0]
            data = self.FetchDataBlocks(blocks)

        # calculate and return parity 
        new_parity = self.CalculateParity(data)
        logging.debug('New Parity: ' + str(new_parity))
        return new_parity, parity_server

    def RecoverDataBlock(self, location, block_number):
        block_idx = location[1]
        # input the block_number
        corrupt_block_number = block_number
        logging.debug('RECOVERY: Corrupt Block: Location: ' + str(corrupt_block_number))
        logging.debug('Started Recovery at Location:' + str(location))

        # Calculate participating blocks excluding the corrupt block
        # data strip - data and parity blocks
        strip = self.GetBlockNumberAcrossServers(block_idx)
        blocks = strip[0]
        parity_block = strip[1]
        parity_server = strip[2]
        # remove the corrupt block from the participating blocks
        blocks.remove(corrupt_block_number)

        logging.debug('Participating blocks in Recovery:' + str(blocks))
        logging.debug('Participating Parity Block: ' + str(parity_block) + ' Parity Server: ' + str(parity_server))
    
        # fetch the strip parity to start recovery for the corrupt data block
        ret = self.SingleGet(parity_server, parity_block)
        parity_data = ret[0]
        logging.debug('Parity Data: ' + str(parity_data))

        # Fetch data blocks excluding the corrupt block
        data = self.FetchDataBlocks(blocks)
        data.append(parity_data)

        recovered_block = self.CalculateParity(data)        
        logging.debug('Recovered Data: ' + str(recovered_block))

        return recovered_block

    def RecoverParityBlock(self, block_idx):
        logging.debug('RECOVERY: Parity Block: Location: ' + str(block_idx))
        # get the strip data block
        strip = self.GetBlockNumberAcrossServers(block_idx)
        participating_blocks = strip[0]

        # fetch the strip data blocks
        blocks = self.FetchDataBlocks(participating_blocks)

        # calculate parity
        recovered_parity = self.CalculateParity(blocks)
        logging.debug('Recovered Parity: ' + str(recovered_parity))

        return recovered_parity

    def RepairServer(self, server_id): 
        logging.debug('REPAIR: Server ID: ' + str(server_id))

        # virtual to physical will skip the parity servers while mapping virtual block numbers
        parity_block_physical_ids = [fsconfig.MAX_SERVERS - int(server_id) - 1 + idx * 4 for idx in range(0, 64)]
        logging.debug('Failed Parity Blocks Indices: ' + str(parity_block_physical_ids))
        
        data_block_physical_ids = [idx for idx in range(0, 192) if idx not in parity_block_physical_ids]
        data_block_virtual_ids = [self.MapPhysicalAddressToVirtualBlock(int(server_id), idx) for idx in data_block_physical_ids]
        
        logging.debug('Failed Data Blocks: ' + str(data_block_virtual_ids))

        # recover data blocks - RecoverDataBlock()
        for block in zip(data_block_physical_ids, data_block_virtual_ids):
            recovered_block_data = self.RecoverDataBlock((int(server_id), block[0]), block[1])
            self.Put(block[1], recovered_block_data)

        # recover parity blocks - RecoverParityBlock()
        for block_idx in parity_block_physical_ids:
            recovered_parity_data = self.RecoverParityBlock(block_idx)
            self.SinglePut(int(server_id), block_idx, recovered_parity_data)

        logging.debug('RepairServer: SERVER RECOVERY COMPLETED: Server ID: ' + server_id)
        return 0

    def SingleGet(self, server_id, block_id):
        has_error = False
        try:
            block_server = self.block_servers[server_id]
            data, has_error = block_server.Get(block_id)
            logging.debug('DATA GET: ' + str(data) + ' \nServer ID: ' + str(server_id) + ' \nBlock Number: ' + str(block_id))
        except socket.timeout:
            logging.debug('ERROR: GET: SERVER_TIMED_OUT')
            data = -2
        except Exception as e:
            logging.debug('ERROR: GET: SERVER_DISCONNECTED: Error ' + str(e)) 
            data = -1
        logging.debug('SingleGet: Server ID: ' + str(server_id) + ' Block ID: ' + str(block_id) + ' Data: ' + str(data))
        return data, has_error 

    def SinglePut(self, server_id, block_id, block_data):
        try:
            logging.debug('SinglePut: Server ID: ' + str(server_id) + ' Block ID: ' + str(block_id) + ' Block Data: ' + str(block_data))
            block_server = self.block_servers[server_id]
            data = block_server.Put(block_id, block_data)
        except socket.timeout:
            logging.debug('ERROR: PUT: SERVER_TIMED_OUT')
            data = -2
        except Exception as e:
            logging.debug('ERROR: PUT: SERVER_DISCONNECTED: Error ' + str(e)) 
            data = -1

        return data

    def SingleRSM(self, server_id, block_id):
        has_error = False
        
        try:
            logging.debug('SingleRSM: Server ID: ' + str(server_id) + ' Block ID: ' + str(block_id))
            rsm_server = self.block_servers[server_id]
            data, has_error = rsm_server.RSM(block_id)
            logging.debug('DATA RSM: ' + str(data) + ' \nServer ID: ' + str(server_id) + ' \nBlock Number: ' + str(block_id))
        except socket.timeout:
            logging.debug('ERROR: RSM: SERVER_TIMED_OUT')
            data = -2
        except Exception as e:
            logging.debug('ERROR: RSM: SERVER_DISCONNECTED: Error ' + str(e))
            data = -1

        return data, has_error
