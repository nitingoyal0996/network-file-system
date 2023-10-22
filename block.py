import pickle, logging
import fsconfig
import xmlrpc.client, socket, time

#### BLOCK LAYER

# global TOTAL_NUM_BLOCKS, BLOCK_SIZE, INODE_SIZE, MAX_NUM_INODES, MAX_FILENAME, INODE_NUMBER_DIRENTRY_SIZE

class DiskBlocks():
    def __init__(self):
        # initialize the block cache using python dictionary
        self.block = {}
        self.cache = {}

        # initialize clientID
        if fsconfig.CID >= 0 and fsconfig.CID < fsconfig.MAX_CLIENTS:
            self.clientID = fsconfig.CID
        else:
            print('Must specify valid cid')
            quit()

        # initialize XMLRPC client connection to raw block server
        if fsconfig.PORT:
            PORT = fsconfig.PORT
        else:
            print('Must specify port number')
            quit()
        server_url = 'http://' + fsconfig.SERVER_ADDRESS + ':' + str(PORT)
        self.block_server = xmlrpc.client.ServerProxy(server_url, use_builtin_types=True)
        socket.setdefaulttimeout(fsconfig.SOCKET_TIMEOUT)

    ## Put: interface to write a raw block of data to the block indexed by block number
    ## Blocks are padded with zeroes up to BLOCK_SIZE

    def Put(self, block_number, block_data):
        try:
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
                ret = self.block_server.Put(block_number, putdata)
                if ret == -1:
                    logging.error('Put: Server returns error')
                    quit()

                print("CACHE_WRITE_THROUGH {BLOCK_NUMBER}".format(BLOCK_NUMBER=block_number))
                self.cache[block_number] = putdata
                
                # TODO: REFACTOR: merge it with the rest of the method later
                try:
                    # set the current client id for the last updated block
                    self.block_server.Put(fsconfig.TOTAL_NUM_BLOCKS - 2, bytearray([fsconfig.CID]))
                except TimeoutError: 
                    print('SERVER_TIMED_OUT')
                    self.block_server.Put(fsconfig.TOTAL_NUM_BLOCKS - 2, bytearray([fsconfig.CID]))
                
                return 0
            else:
                logging.error('Put: Block out of range: ' + str(block_number))
                quit()
        except TimeoutError:
            print('SERVER_TIMED_OUT')
            # retry the request
            return self.Put(block_number, block_data)


    ## Get: interface to read a raw block of data from block indexed by block number
    ## Equivalent to the textbook's BLOCK_NUMBER_TO_BLOCK(b)

    def Get(self, block_number):
        try:
            logging.debug('Get: ' + str(block_number))
            if block_number in range(0, fsconfig.TOTAL_NUM_BLOCKS):
                block_data = []
                # logging.debug ('\n' + str((self.block[block_number]).hex()))
                # commenting this out as the request now goes to the server
                # return self.block[block_number]
                # call Get() method on the server

                ### Caching ###
                if (block_number != fsconfig.TOTAL_NUM_BLOCKS - 1 and block_number != fsconfig.TOTAL_NUM_BLOCKS - 2) and (block_number in self.cache.keys()):
                    print("CACHE_HIT {BLOCK_NUMBER}".format(BLOCK_NUMBER=block_number))
                    return self.cache[block_number]
                
                if block_number not in self.cache.keys() or (block_number == fsconfig.TOTAL_NUM_BLOCKS - 1 or block_number == fsconfig.TOTAL_NUM_BLOCKS - 2):
                    ret = self.block_server.Get(block_number)
                    print("CACHE_MISS {BLOCK_NUMBER}".format(BLOCK_NUMBER=block_number))
                    if ret == -1:
                        logging.error('Get: Server returns error')
                        quit()
                    block_data = bytearray(ret)
                
                # read_through
                self.cache[block_number] = block_data
                
                return block_data

            logging.error('DiskBlocks::Get: Block number larger than TOTAL_NUM_BLOCKS: ' + str(block_number))
            quit()
            
        except TimeoutError:
            print('SERVER_TIMED_OUT')
            # retry request
            return self.Get(block_number)


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

    def RSM(self, block_number):
        try:
            ret = self.block_server.RSM(block_number)
            if ret == -1:
                logging.error('RSM: Server returns error')
                quit()
        except TimeoutError:
            logging.error('SERVER_TIMED_OUT')
            ret = self.RSM(block_number)
        return ret
        
    def Acquire(self):
        invalid_cache = self.CheckAndInvalidateCache()
        if invalid_cache:
            # set current client id
            print("CACHE_WRITE_THROUGH {BLOCK_NUMBER}".format(BLOCK_NUMBER=fsconfig.TOTAL_NUM_BLOCKS - 2))
        R1 = self.RSM (fsconfig.TOTAL_NUM_BLOCKS - 1)  # read and set RSM block
        while True: 
            if R1 is not fsconfig.RSM_LOCKED: 
                break
            R1 = self.RSM (fsconfig.TOTAL_NUM_BLOCKS - 1)
        return R1

    def Release (self):
        self.Put (fsconfig.TOTAL_NUM_BLOCKS - 1, fsconfig.RSM_UNLOCKED)

    def CheckAndInvalidateCache(self):
        client_id = self.Get(fsconfig.TOTAL_NUM_BLOCKS - 2)
        # if the client id is different, then we invalidate the cache
        if client_id[0] != fsconfig.CID:
            # invalidate the cache
            self.cache = {}
            # log that the cache has been invalidated
            print("CACHE_INVALIDATED")
            return True
        return False
        
    def PrintBlocks(self,tag,min,max):
        print ('#### Raw disk blocks: ' + tag)
        for i in range(min,max):
            print ('Block [' + str(i) + '] : ' + str((self.Get(i)).hex()))
