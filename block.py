import pickle, logging
import fsconfig
import xmlrpc.client, socket, time

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
        # RAID-0: port number for the block server
        # if fsconfig.START_PORT_NUM:
        # RAID-1: starting port number for block server array
        if fsconfig.START_PORT_NUM:
            START_PORT_NUM = fsconfig.START_PORT_NUM
        else:
            print('Must specify a starting port number')
            quit()


        # Base implementation - single server
        # self.block_servers = xmlrpc.client.ServerProxy('http://' + fsconfig.SERVER_ADDRESS + ':' + str(PORT), use_builtin_types=True)
        
        # RAID-0/1: initialize the server address array
        self.server_addresses = []
        for i in range(0, fsconfig.MAX_SERVERS):
            self.server_addresses.append('http://' + fsconfig.SERVER_ADDRESS + ':' + str(START_PORT_NUM + i))
        
        # Base implementation - single server
        # self.block_server = xmlrpc.client.ServerProxy(self.server_addresses[0], use_builtin_types=True)

        # RAID-0/1: initialize block_server connections array
        self.block_servers = []
        for i in range(0, fsconfig.MAX_SERVERS):
            self.block_servers.append(xmlrpc.client.ServerProxy(self.server_addresses[i], use_builtin_types=True))

        # RAID-0/1: single block_server to store RSM information
        self.rsm_block_server = self.block_servers[fsconfig.MAX_SERVERS-1]

        # RAID-0: round-robin index for block_server writes
        # last server used
        # self.last_block_server_idx = 0
        # map of block number to block server
        # self.block_server_map = {}

        socket.setdefaulttimeout(fsconfig.SOCKET_TIMEOUT)
        # initialize block cache empty
        self.blockcache = {}


    ## Put: interface to write a raw block of data to the block indexed by block number
    ## Blocks are padded with zeroes up to BLOCK_SIZE

    # overload print method to check for cache log enabled or not before printing
    def print_log(self, *args, **kwargs):
        if fsconfig.LOG_CACHE:
            print(*args, **kwargs)

    def Put(self, block_number, block_data):

        logging.debug(
            'Put: block number ' + str(block_number) + ' len ' + str(len(block_data)) + '\n' + str(block_data.hex()))
        if len(block_data) > fsconfig.BLOCK_SIZE:
            logging.error('Put: Block larger than BLOCK_SIZE: ' + str(len(block_data)))
            quit()

        if block_number in range(0, fsconfig.TOTAL_NUM_BLOCKS):
            # ljust does the padding with zeros
            putdata = bytearray(block_data.ljust(fsconfig.BLOCK_SIZE, b'\x00'))
            # Write block
            # commenting this out as the request now goes to the server
            # self.block[block_number] = putdata
            # call Put() method on the server; code currently quits on any server failure
            rpcretry = True
            while rpcretry:
                rpcretry = False
                try:
                    print('-------------PUT B-------------'+ str(block_number))
                    if block_number == fsconfig.TOTAL_NUM_BLOCKS - 1:
                        # RAID-0/1: only last server will have RSM information
                        ret = self.rsm_block_server.Put(block_number, putdata)

                    else:
                        # Base implementation - single server
                        # ret = self.block_server.Put(block_number, putdata)

                        # RAID-0: Round Robin storage over the servers
                        # if block_number not in self.block_server_map:
                        #     self.block_server = self.block_servers[self.last_block_server_idx]
                        #     self.block_server_map[block_number] = self.block_server
                        #     self.last_block_server_idx = (self.last_block_server_idx + 1) % fsconfig.MAX_SERVERS
                        #     ret = self.block_server.Put(block_number, putdata)
                        # else:
                        #     ret = self.block_server_map[block_number].Put(block_number, putdata)

                        # RAID-1: send the request to all the servers
                        for i in range(0, fsconfig.MAX_SERVERS):
                            ret = self.block_servers[i].Put(block_number, putdata)
                except socket.timeout:
                    print("SERVER_TIMED_OUT")
                    time.sleep(fsconfig.RETRY_INTERVAL)
                    rpcretry = True
            # update block cache
            self.print_log('CACHE_WRITE_THROUGH ' + str(block_number))
            self.blockcache[block_number] = putdata
            # flag this is the last writer
            # unless this is a release - which doesn't flag last writer
            if block_number != fsconfig.TOTAL_NUM_BLOCKS - 1:
                LAST_WRITER_BLOCK = fsconfig.TOTAL_NUM_BLOCKS - 2
                updated_block = bytearray(fsconfig.BLOCK_SIZE)
                updated_block[0] = fsconfig.CID
                rpcretry = True
                while rpcretry:
                    rpcretry = False
                    try:
                        # Base implementation - single server
                        # ret = self.block_server.Put(LAST_WRITER_BLOCK, updated_block)  

                        # RAID-0: Round Robin storage over the servers
                        # if LAST_WRITER_BLOCK not in self.block_server_map:
                        #     self.block_server = self.block_servers[self.last_block_server_idx]
                        #     self.block_server_map[LAST_WRITER_BLOCK] = self.block_server
                        #     self.last_block_server_idx = (self.last_block_server_idx + 1) % fsconfig.MAX_SERVERS
                        #     ret = self.block_server.Put(LAST_WRITER_BLOCK, updated_block)
                        # else:
                        #     ret = self.block_server_map[LAST_WRITER_BLOCK].Put(LAST_WRITER_BLOCK, updated_block)
                        
                        # RAID-1: send the request to all the servers
                        for i in range(0, fsconfig.MAX_SERVERS):
                            self.block_servers[i].Put(LAST_WRITER_BLOCK, updated_block)  
                    except socket.timeout:
                        print("SERVER_TIMED_OUT")
                        time.sleep(fsconfig.RETRY_INTERVAL)
                        rpcretry = True
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
            # logging.debug ('\n' + str((self.block[block_number]).hex()))
            # commenting this out as the request now goes to the server
            # return self.block[block_number]
            # call Get() method on the server
            # don't look up cache for last two blocks
            if (block_number < fsconfig.TOTAL_NUM_BLOCKS-2) and (block_number in self.blockcache):
                self.print_log('CACHE_HIT '+ str(block_number))
                data = self.blockcache[block_number]
            else:
                self.print_log('CACHE_MISS ' + str(block_number))
                rpcretry = True
                while rpcretry:
                    rpcretry = False
                    try:
                        # Base implementation - single server
                        # data = self.block_server.Get(block_number)

                        # RAID-0: Since Round Robin storage over all the servers
                        # if block_number not in self.block_server_map:
                        #     self.block_server = self.block_servers[self.last_block_server_idx]
                        #     self.block_server_map[block_number] = self.block_server
                        #     self.last_block_server_idx = (self.last_block_server_idx + 1) % fsconfig.MAX_SERVERS
                        #     data = self.block_server.Get(block_number)
                        # else:
                        #     data = self.block_server_map[block_number].Get(block_number)

                        # RAID-1: get: response from one of the server, if it's a failure, retry from another one
                        for i in range(0, fsconfig.MAX_SERVERS):
                            data = self.block_servers[i].Get(block_number)
                            if data != -1:
                                break
                    except socket.timeout:
                        print("SERVER_TIMED_OUT")
                        time.sleep(fsconfig.RETRY_INTERVAL)
                        rpcretry = True
                # add to cache
                self.blockcache[block_number] = data
            # return as bytearray
            return bytearray(data)

        logging.error('DiskBlocks::Get: Block number larger than TOTAL_NUM_BLOCKS: ' + str(block_number))
        quit()

    ## RSM: read and set memory equivalent

    def RSM(self, block_number):
        logging.debug('RSM: ' + str(block_number))
        if block_number in range(0, fsconfig.TOTAL_NUM_BLOCKS):
            rpcretry = True
            while rpcretry:
                rpcretry = False
                try:
                    # Base implementation - single server
                    # data = self.block_server.RSM(block_number)

                    # RAID-0/1: only last server will have RSM information
                    data = self.rsm_block_server.RSM(block_number)
                except socket.timeout:
                    print("SERVER_TIMED_OUT")
                    time.sleep(fsconfig.RETRY_INTERVAL)
                    rpcretry = True

            return bytearray(data)

        logging.error('RSM: Block number larger than TOTAL_NUM_BLOCKS: ' + str(block_number))
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
        LAST_WRITER_BLOCK = fsconfig.TOTAL_NUM_BLOCKS - 2
        last_writer = self.Get(LAST_WRITER_BLOCK)
        # if ID of last writer is not self, invalidate and update
        if last_writer[0] != fsconfig.CID:
            print("CACHE_INVALIDATED")
            self.blockcache = {}
            updated_block = bytearray(fsconfig.BLOCK_SIZE)
            updated_block[0] = fsconfig.CID
            self.Put(LAST_WRITER_BLOCK,updated_block)

    ## Serializes and saves the DiskBlocks block[] data structure to a "dump" file on your disk

    def DumpToDisk(self, filename):

        logging.info("DiskBlocks::DumpToDisk: Dumping pickled blocks to file " + filename)
        file = open(filename,'wb')
        file_system_constants = "BS_" + str(fsconfig.BLOCK_SIZE) + "_NB_" + str(fsconfig.TOTAL_NUM_BLOCKS) + "_IS_" + str(fsconfig.INODE_SIZE) \
                            + "_MI_" + str(fsconfig.MAX_NUM_INODES) + "_MF_" + str(fsconfig.MAX_FILENAME) + "_IDS_" + str(fsconfig.INODE_NUMBER_DIRENTRY_SIZE)
        pickle.dump(file_system_constants, file)
        pickle.dump(self.block, file)

        file.close()

    ## Loads DiskBlocks block[] data structure from a "dump" file on your disk

    def LoadFromDump(self, filename):

        logging.info("DiskBlocks::LoadFromDump: Reading blocks from pickled file " + filename)
        file = open(filename,'rb')
        file_system_constants = "BS_" + str(fsconfig.BLOCK_SIZE) + "_NB_" + str(fsconfig.TOTAL_NUM_BLOCKS) + "_IS_" + str(fsconfig.INODE_SIZE) \
                            + "_MI_" + str(fsconfig.MAX_NUM_INODES) + "_MF_" + str(fsconfig.MAX_FILENAME) + "_IDS_" + str(fsconfig.INODE_NUMBER_DIRENTRY_SIZE)

        try:
            read_file_system_constants = pickle.load(file)
            if file_system_constants != read_file_system_constants:
                print('DiskBlocks::LoadFromDump Error: File System constants of File :' + read_file_system_constants + ' do not match with current file system constants :' + file_system_constants)
                return -1
            block = pickle.load(file)
            for i in range(0, fsconfig.TOTAL_NUM_BLOCKS):
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