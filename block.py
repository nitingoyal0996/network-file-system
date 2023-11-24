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
        self.total_virtual_blocks = fsconfig.TOTAL_NUM_BLOCKS - self.data_blocks_per_disk
        
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
            # ljust does the padding with zeros
            putdata = bytearray(block_data.ljust(fsconfig.BLOCK_SIZE, b'\x00'))
            
            # at-most-once semantics
            block_location = self.VirtualToPhysicalAddress(block_number)
            data = self.SinglePut(block_location[0], block_location[1], putdata)
            logging.debug('DATA PUT: ' + str(putdata) + ' \nServer ID: ' + str(block_location[0]) + ' \nBlock Number: ' + str(block_location[1]))
            
            # if the location is not updating the rsm 
            if block_number != self.total_virtual_blocks - 1:
                parity, parity_server = self.ParityUpdate(block_number, block_location[1], putdata)
                logging.debug('Initiate Parity Update At: ' + str(block_location[1]) + ' Parity Server: ' + str(parity_server))
                
                parity_data = self.SinglePut(parity_server, block_location[1], parity)
                logging.debug('PARITY PUT: ' + str(block_location[1]) + ' \nParity Server ID: ' + str(parity_server) + ' \nParity: ' + str(parity))

                if data == -1 and parity_data == -1:
                    logging.debug('PUT: Multiple Server Failures')
                    quit()
                elif data == -1:
                    print(f'SERVER_DISCONNECTED PUT DATA_BLOCK: {block_number}')
                    # TODO: continue operation: retry write to the next available block
                    self.Put(block_number + 1, putdata)
                elif parity_data == -1:
                    print(f'SERVER_DISCONNECTED PUT PARITY_BLOCK: {block_number}')
                    # TODO: continue operation: if we retry parity write to the next available block - how would we access this back, since the deterministic pattern is broken?
                elif data == -2 or parity_data == -2:
                    print(f'SERVER_TIMED_OUT PUT {block_number}')
                    logging.debug('PARITY LAST_WRITER PUT: ' + str(block_location[1]) + ' \nParity Server ID: ' + str(parity_server) + ' \nParity: ' + str(parity))
                    quit()

            # TODO: update block cache
            self.print_cache_logs('CACHE_WRITE_THROUGH ' + str(block_number))
            # self.blockcache[block_number] = putdata
            
            # flag this is the last writer
            # unless this is a release - which doesn't flag last writer
            if block_number != self.total_virtual_blocks - 1:
                LAST_WRITER_BLOCK = self.total_virtual_blocks - 2
                block_location = self.VirtualToPhysicalAddress(LAST_WRITER_BLOCK)
                updated_block = bytearray(fsconfig.BLOCK_SIZE)
                updated_block[0] = fsconfig.CID

                data = self.SinglePut(block_location[0], block_location[1], updated_block)
                parity, parity_server = self.ParityUpdate(LAST_WRITER_BLOCK, block_location[1], updated_block)

                logging.debug('Initiate Parity Update At LAST_WRITER: ' + str(block_location[1]) + ' Parity Server: ' + str(parity_server))
                parity_data = self.SinglePut(parity_server, block_location[1], parity)
                
                if data == -1 and parity_data == -1:
                    logging.debug('PUT: Multiple Server Failures')
                    quit()
                elif data == -1:
                    print(f'SERVER_DISCONNECTED PUT LAST_WRITER_BLOCK: {block_number}')
                    # TODO: continue operation: retry write to the next available block
                    quit()
                elif parity_data == -1:
                    print(f'SERVER_DISCONNECTED PUT LAST_WRITER_PARITY_BLOCK: {block_number}')
                    # TODO: continue operation: retry write to the next available block
                    quit()
                elif data == -2 or parity_data == -2:
                    print(f'SERVER_TIMED_OUT PUT {block_number}')
                    logging.debug('PARITY LAST_WRITER PUT: ' + str(block_location[1]) + ' \nParity Server ID: ' + str(parity_server) + ' \nParity: ' + str(parity))
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
            if (block_number < self.total_virtual_blocks - 2 or block_number > self.total_virtual_blocks) and (block_number in self.blockcache):
                self.print_cache_logs('CACHE_HIT '+ str(block_number))
                data = self.blockcache[block_number]
            else:
                # retry = True
                # while retry:
                self.print_cache_logs('CACHE_MISS ' + str(block_number))
                block_location = self.VirtualToPhysicalAddress(block_number)
                ret = self.SingleGet(block_location[0], block_location[1])
                data, has_error = ret[0], ret[1]
                # retry = False

                if data == -1:
                    print(f'SERVER_DISCONNECTED GET {block_number}')
                    # continue function: recover the data from other servers and parity for that data strip and return
                    data = self.RecoverBlock(block_location)
                elif data == -2: 
                    print(f'SERVER_TIMED_OUT GET {block_number}')
                    # retry = True
                elif has_error:
                    logging.debug('CHECKSUM_ERROR DETECTED: ' + str(block_number))
                    print(f'GET CORRUPTED_BLOCK {block_location[1]}')
                    # recover the corrupted block
                    data = self.RecoverBlock(block_location)
                    # Update the recovered block
                    block_number = self.GetPhysicalAddressToVirtualBlock(block_location[0], block_location[1])
                    self.Put(block_number, data)
                    logging.debug('RECOVERY: PUT: Recovered Corrupt Block: Location: ' + str(block_number))
                    
                # TODO: add data to cache
                # self.blockcache[block_number] = data
            
            return bytearray(data)

        logging.debug('ERROR: DiskBlocks::Get: Block number larger than TOTAL_NUM_BLOCKS: ' + str(block_number))
        quit()

    ## RSM: read and set memory equivalent
    def RSM(self, block_number):
        logging.debug('RSM: ' + str(block_number))

        if block_number in range(0, self.total_virtual_blocks):
            block_location = self.VirtualToPhysicalAddress(block_number)
            ret = self.SingleRSM(block_location[0], block_location[1])
            data, has_error = ret[0], ret[1]
            if data == -1:
                print(f'SERVER_DISCONNECTED RSM {block_number}')
                # continue function: recover the data from other servers and parity for that data strip and return
                data = self.RecoverBlock(block_location)
            if data == -2: 
                print(f'SERVER_TIMED_OUT RSM {block_number}')
            if has_error:
                logging.debug('CHECKSUM_ERROR DETECTED ON RSM: ' + str(block_number))
                print(f'RSM CORRUPTED_BLOCK {block_number}')
                # recover the corrupted block
                data = self.RecoverBlock(block_location)
                # Update the recovered block
                block_number = self.GetPhysicalAddressToVirtualBlock(block_location[0], block_location[1])
                self.Put(block_number, data)
                logging.debug('RECOVERY: PUT: Recovered Corrupt Block: Location: ' + str(block_number))
                
            return bytearray(data)

        logging.debug('ERROR: RSM: Block number larger than TOTAL_NUM_BLOCKS: ' + str(block_number))
        quit()

        ## Acquire and Release using a disk block lock
    def Acquire(self):
        logging.debug('Acquire')
        RSM_BLOCK = self.total_virtual_blocks - 1
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
        RSM_BLOCK = self.total_virtual_blocks - 1
        # Put()s a zero-filled block to release lock
        self.Put(RSM_BLOCK,bytearray(fsconfig.RSM_UNLOCKED.ljust(fsconfig.BLOCK_SIZE, b'\x00')))
        return 0

    def CheckAndInvalidateCache(self):
        LAST_WRITER_BLOCK = self.total_virtual_blocks - 2
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
    def GetServerAndBlock(self,virtual_block_number):
        if (virtual_block_number < 0 or virtual_block_number > fsconfig.TOTAL_NUM_BLOCKS):
            print('block number is out of bounds')
            quit()
        # number of data servers = #total_servers - #parity_servers
        effective_servers = fsconfig.MAX_SERVERS - 1
        block_number = virtual_block_number // effective_servers
        parity_server_number = effective_servers - (block_number % fsconfig.MAX_SERVERS)
        data_server_number = virtual_block_number % effective_servers
        if parity_server_number <= data_server_number:
            data_server_number = data_server_number + 1
        
        logging.debug('V2P RESULTS: Data Server Number: ' + str(data_server_number) + ' Block Number on Disk: ' + str(block_number))
        return data_server_number, block_number

    def GetParityBlock(self,virtual_block_number):
        if (virtual_block_number < 0 or virtual_block_number > fsconfig.TOTAL_NUM_BLOCKS):
            print('block number is out of bounds')
            quit()
        _, block_number = self.GetServerAndBlock(virtual_block_number)
        parity_server_id = fsconfig.MAX_SERVERS - 1 - block_number % fsconfig.MAX_SERVERS

        return parity_server_id, block_number

    def GetOtherStripBlockNumbers(self,virtual_block_number):
        row_index, _ = self.GetServerAndBlock(virtual_block_number)
        row_offset = row_index * (fsconfig.MAX_SERVERS - 1)
        blocks = [row_offset + i for i in range(0, fsconfig.MAX_SERVERS)]
        logging.debug('Other Row Blocks Detected: ' + str(blocks))
        return blocks

    def GetPhysicalAddressToVirtualBlock(self, server_index, block_index):
        offset = block_index * (fsconfig.MAX_SERVERS - 1)
        return offset + server_index
    
    def VirtualToPhysicalAddress(self, virtual_block_number):
        logging.debug('Process Virtual Block Number: ' + str(virtual_block_number))
        server_number, block_number_on_disk = self.GetServerAndBlock(virtual_block_number)
        return server_number, block_number_on_disk
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
    
    def ParityUpdate(self, virtual_block_number, block_idx, new_data):
        logging.debug('Process Parity for Location: ' + str(block_idx))
        old_data = self.Get(virtual_block_number)
        logging.debug('Old Data: ' + str(old_data) + ' \nNew Data: ' + str(new_data))
        # if the block_data and the parity previously was not empty - we could XOR the old_data, new_data and the old_parity to calculate the new parity
        # else when there is no parity - we could calculate the parity by XORing all the participating data blocks in the stripe
        # filter participating_blocks to remove the parity block
        parity_server, parity_block_idx = self.GetParityBlock(virtual_block_number)
        logging.debug('Parity Server: ' + str(parity_server) + ' Parity Block Index: ' + str(parity_block_idx))

        # if the old_data is not empty bytearray - fetch the parity block
        if old_data != bytearray(b'\x00' * fsconfig.BLOCK_SIZE):
            logging.debug('Parity: Update')
            parity_virtual_block_number = self.GetPhysicalAddressToVirtualBlock(parity_server, parity_block_idx)
            ret = self.Get(parity_virtual_block_number)
            old_parity = ret
            logging.debug('Old Parity: ' + str(old_parity))
            data_blocks = [old_data, new_data, old_parity]
        else:
            logging.debug('Parity: Create')
            # fetch participating data blocks excluding the parity server
            participating_blocks = self.GetOtherStripBlockNumbers(block_idx)
            participating_blocks.pop(parity_server)
            # fetch data blocks - where data is available
            data_blocks = [
                self.Get(block_number)
                for block_number in participating_blocks
            ]

        # calculate and return parity 
        new_parity = self.CalculateParity(data_blocks)
        logging.debug('New Parity: ' + str(new_parity))
        return new_parity, parity_server

    def RecoverBlock(self, location):
        corrupt_server = location[0]
        block_idx = location[1]
        corrupt_block_number = self.GetPhysicalAddressToVirtualBlock(corrupt_server, block_idx)
        # TODO:Error: the corrupt block number should be equal to the Get>block_number
        logging.debug('RECOVERY: GET: Corrupt Block: Location: ' + str(corrupt_block_number))
        logging.debug('Started Recovery at Location:' + str(location))

        # Calculate participating blocks excluding the corrupt block
        participating_blocks = self.GetOtherStripBlockNumbers(block_idx)
        participating_blocks.pop(corrupt_server)

        logging.debug('Participating blocks in recovery:' + str(participating_blocks))

        # Fetch data blocks excluding the corrupt block
        data_blocks = [
            self.Get(block_number)
            for block_number in participating_blocks
        ]

        recovered_block_data = self.CalculateParity(data_blocks)        
        logging.debug('Recovered Data: ' + recovered_block_data.decode('utf-8', errors='ignore'))

        return recovered_block_data

    def RepairServer(self, server_id): 
        # TODO: ERROR: virtual to physical will skip the parity servers while mapping virtual block numbers
        blocks_on_server = [int(block_idx) + int(server_id) for block_idx in range(0, self.data_blocks_per_disk)]

        logging.debug('RepairServer: SERVER RECOVERY STARTED: Server ID: ' + str(server_id) + ' Blocks: ' + str(blocks_on_server))
        try: 
            # recover data on the failed server one block at a time
            for block in blocks_on_server:
                recovered_block_data = self.RecoverBlock((int(server_id), block))
                virtual_block_number = self.GetPhysicalAddressToVirtualBlock(int(server_id), block)
                self.Put(virtual_block_number, recovered_block_data)
            logging.debug('RepairServer: SERVER RECOVERY COMPLETED: Server ID: ' + str(server_id))
            return 0
        except Exception as e:
            logging.debug('error: RepairServer: SERVER RECOVERY FAILED: Error ' + str(e))      

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
