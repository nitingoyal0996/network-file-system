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
        # self.failureMode = False
        
    # validates whether the cache logging is enabled by the user or not
    def print_cache_logs(self, message):
        if fsconfig.LOG_CACHE != False:
            print(message)

    ## Put: interface to write a raw block of data to the block indexed by block number
    ## Blocks are padded with zeroes up to BLOCK_SIZE
    def Put(self, block_number, block_data):

        logging.debug(
            'Put: block number ' + str(block_number) + ' len ' + str(len(block_data)) + '\n' + str(block_data.hex()))
        if len(block_data) > fsconfig.BLOCK_SIZE:
            logging.error('Put: Block larger than BLOCK_SIZE: ' + str(len(block_data)))
            quit()

        if block_number in range(0, fsconfig.TOTAL_NUM_BLOCKS):
            # ljust does the padding with zeros
            putdata = bytearray(block_data.ljust(fsconfig.BLOCK_SIZE, b'\x00'))
            
            # at-most-once semantics
            location = self.VirtualToPhysicalAddress(block_number)
            try:
                old_data = self.Get(block_number)
                ret = self.SinglePut(location[0], location[1], putdata)
                logging.debug('DATA PUT: ' + str(putdata) + ' \nServer ID: ' + str(location[0]) + ' \nBlock Number: ' + str(location[1]))
                # if the location is not updating the rsm 
                if block_number != self.total_virtual_blocks - 1:
                    parity = self.ParityUpdate(location, putdata, old_data)
                    logging.debug('Initiate Parity Update At: ' + str(location[1]) + ' Parity Server: ' + str(self.parity_server_idx))
                    ret = self.SinglePut(self.parity_server_idx, location[1], parity)
                    logging.debug('PARITY PUT: ' + str(location[1]) + ' \nParity Server ID: ' + str(self.parity_server_idx) + ' \nParity: ' + str(parity))
            except Exception as e:
                logging.error('PUT: SERVER_DISCONNECTED: Error ' + str(e))
                print("SERVER_DISCONNECTED")
            
            # update block cache
            self.print_cache_logs('CACHE_WRITE_THROUGH ' + str(block_number))
            self.blockcache[block_number] = putdata
            
            # flag this is the last writer
            # unless this is a release - which doesn't flag last writer
            if block_number != self.total_virtual_blocks - 1:
                LAST_WRITER_BLOCK = self.total_virtual_blocks - 2
                location = self.VirtualToPhysicalAddress(LAST_WRITER_BLOCK)
                updated_block = bytearray(fsconfig.BLOCK_SIZE)
                updated_block[0] = fsconfig.CID
                try:                    
                    ret = self.SinglePut(location[0], location[1], updated_block)
                    # TODO: Rethink: we don't need parity updates for the last writer block
                   
                except Exception as e:
                    logging.error('PUT: SERVER_DISCONNECTED: Error ' + str(e))
                    print("SERVER_DISCONNECTED")
                
            if ret == -1:
                logging.error('Put: Server returns error')
                quit()
        
            return 0
        else:
            logging.error('Put: Block out of range: ' + str(block_number))
            quit()

    ## Get: interface to read a raw block of data from block indexed by block number
    ## Equivalent to the textbook's BLOCK_NUMBER_TO_BLOCK(b)
    def Get(self, block_number):

        logging.debug('Get: ' + str(block_number))
        if block_number in range(0, fsconfig.TOTAL_NUM_BLOCKS):
            data = None
            # except data and parity blocks - do not use cache
            if (block_number < self.total_virtual_blocks - 2 or block_number > self.total_virtual_blocks) and (block_number in self.blockcache):
                self.print_cache_logs('CACHE_HIT '+ str(block_number))
                data = self.blockcache[block_number]
            else:
                self.print_cache_logs('CACHE_MISS ' + str(block_number))
                try:
                    # data = self.block_server.Get(block_number)
                    location = self.VirtualToPhysicalAddress(block_number)
                    data = self.SingleGet(location[0], location[1])
                    # if (block_number != self.total_virtual_blocks - 1 and self.failureMode):
                        # self.failureMode = False
                    # data == -2 means the block is corrupted
                    if (data == -2):
                        recovery = self.RecoverCorruptedBlock(location)
                        if recovery != None:
                            self.SinglePut(location[0], location[1], recovery)
                            logging.debug('Recovered Data: ' + str(recovery.decode('utf-8', errors='ignore')))
                            quit()
                except Exception as e:
                    logging.error('GET: SERVER_DISCONNECTED: Error ' + str(e))
                    print("SERVER_DISCONNECTED")
                # add to cache
                self.blockcache[block_number] = data
            return bytearray(data)

        logging.error('DiskBlocks::Get: Block number larger than TOTAL_NUM_BLOCKS: ' + str(block_number))
        quit()

    ## RSM: read and set memory equivalent
    def RSM(self, block_number):
        logging.debug('RSM: ' + str(block_number))

        if block_number in range(0, self.total_virtual_blocks):
            # rsm BLOCK and server is going to be fixed - last virtual block
            location = self.VirtualToPhysicalAddress(block_number)
            try:
                # data = self.block_server.RSM(block_number)
                data = self.SingleRSM(location[0], location[1])
            except Exception as e:
                logging.error('RSM: SERVER_DISCONNECTED: Error ' + str(e))
                print("SERVER_DISCONNECTED")

            return bytearray(data)

        logging.error('RSM: Block number larger than TOTAL_NUM_BLOCKS: ' + str(block_number))
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

    ## Prints to screen block contents, from min to max
    def PrintBlocks(self,tag,min,max):
        print ('#### Raw disk blocks: ' + tag)
        for i in range(min,max):
            print ('Block [' + str(i) + '] : ' + str((self.Get(i)).hex()))

    def Repair(self, server_id):
        '''
        TODO
        Must implement simple process of repairing/recovery.

        1. When a server is crashed is replaced by a new server with blank blocks.
        2. Repair procedure:
            1. command `repair server_id`
            2. client locks access to the disk
            3. reconnects to `server_id`
            4. regenerates all blocks for `server_id` using data from other servers in the array.
        '''
        pass

    def VirtualToPhysicalAddress(self, virtual_block_number):
        logging.debug('Process Virtual Block Number: ' + str(virtual_block_number))
        if virtual_block_number > (fsconfig.TOTAL_NUM_BLOCKS):
            logging.error('Block number is out of bounds')
            quit()

        # Calculate the total number of data blocks per disk (excluding parity blocks)
        # data_blocks_per_disk = (fsconfig.TOTAL_NUM_BLOCKS - self.data_blocks_per_disk) // (fsconfig.MAX_SERVERS - 1)
        # total_blocks_per_section = data_blocks_per_disk * (fsconfig.MAX_SERVERS - 1)

        # # Determine the data disk or the parity disk for the given virtual block number
        # if virtual_block_number % total_blocks_per_section == 0:
        #     # If the block belongs to the parity disk
        #     server_number = fsconfig.MAX_SERVERS - 1  # Parity disk is the last disk
        #     block_number_on_disk = virtual_block_number // total_blocks_per_section
        # else:
        #     # For data disks
        #     server_number = virtual_block_number % (fsconfig.MAX_SERVERS - 1)
            
        #     # Calculate the block number within the section for the identified data disk
        #     block_within_section = virtual_block_number % total_blocks_per_section
        #     block_number_on_disk = block_within_section // (fsconfig.MAX_SERVERS - 1)

        # Output the identified data disk/parity disk and the block number on that disk
        # print('virtual block number: ', virtual_block_number, ' data_disk: ', server_number, 'block_number_on_disk:', block_number_on_disk)
        
        server_number = virtual_block_number % (fsconfig.MAX_SERVERS - 1)
        block_number_on_disk = virtual_block_number % self.data_blocks_per_disk
        logging.debug('virtual block number: ' + str(virtual_block_number) + ' data_disk: ' + str(server_number) + ' block_number_on_disk: ' + str(block_number_on_disk))
        return server_number, block_number_on_disk
    
    def CalculateParity(self, data_blocks):
        logging.debug('Calculate Parity for Data Blocks: ' + str(data_blocks))
        parity = bytearray(data_blocks[0])
        # XOR operation across all data blocks in the stripe
        for block in data_blocks[1:]:
            for i in range(len(parity)):
                parity[i] ^= block[i]
        return parity
    
    def ParityUpdate(self, block_location, new_data, old_data):
        logging.debug('Process Parity for Location: ' + str(block_location) + '\nOld Data:' + str(old_data) + ' \nNew Data: ' + str(new_data) + ' \nOld Parity: ' + str(old_data))
        # if the block_data and the parity previously was not empty - we could XOR the old_data, new_data and the old_parity to calculate the new parity
        # else when there is no parity - we could calculate the parity by XORing all the participating data blocks in the stripe
        block_server = block_location[0]
        offset = block_location[1]
        # if the old_data is not empty bytearray - fetch the parity
        if old_data != bytearray(b'\x00' * fsconfig.BLOCK_SIZE):
            logging.debug('Parity: Update')
            old_parity = self.SingleGet(self.parity_server_idx, offset)
            # calculate the new parity
            new_parity = self.CalculateParity([old_data, new_data, old_parity])
            # self.failureMode = True
        else:
            logging.debug('Parity: Create')
            # fetch participating data blocks
            participating_blocks = [i * self.data_blocks_per_disk + offset for i in range(0, fsconfig.MAX_SERVERS) if i != self.parity_server_idx and i != block_server]
            data_blocks = [
                self.Get(block_number)
                for block_number in participating_blocks 
            ]
            data_blocks.append(new_data)
            # calculate parity over - parity + correct data blocks >> corrupted block
            new_parity = self.CalculateParity(data_blocks)
        logging.debug('New Parity: ' + str(new_parity))
        return new_parity

    def RecoverCorruptedBlock(self, location):
        corrupt_server_id = location[0]
        offset = location[1]
        corrupt_block_id = (corrupt_server_id - 1) * self.data_blocks_per_disk + offset

        logging.debug('Started Recovery at Location:' + str(location) + ' Corrupt Block Virtual ID: ' + str(corrupt_block_id))

        # Calculate participating blocks excluding the corrupt block
        participating_blocks = []
        for i in range(fsconfig.MAX_SERVERS):
            block_number = i * self.data_blocks_per_disk + offset 
            participating_blocks.append(block_number)
        
        participating_blocks.remove(corrupt_block_id)
        logging.debug('Participating blocks in recovery:' + str(participating_blocks))

        # Fetch data blocks excluding the corrupt block
        data_blocks = []
        for block_number in participating_blocks:
            logging.debug('Fetch block: ' + str(block_number))
            block_data = self.Get(block_number)
            logging.debug('Block Data: ' + str(block_data))
            data_blocks.append(block_data)

        recovered_data = self.CalculateParity(data_blocks)
        logging.debug('Recovered Data:' + str(recovered_data))

        return recovered_data

    def SingleGet(self, server_id, block_id):

        block_server = self.block_servers[server_id]
        ret = block_server.Get(block_id)

        return ret

    def SinglePut(self, server_id, block_id, block_data):
        # print('PUT: ', block_id, server_id)
        block_server = self.block_servers[server_id]
        ret = block_server.Put(block_id, block_data)
       
        return ret

    def SingleRSM(self, server_id, block_id):

        rsm_server = self.block_servers[server_id]
        ret = rsm_server.RSM(block_id)
        
        return ret
