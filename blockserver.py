import pickle, logging
import argparse
import time
import fsconfig
import hashlib

from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler

# Restrict to a particular path.
class RequestHandler(SimpleXMLRPCRequestHandler):
  rpc_paths = ('/RPC2',)

# add checksum implementation
class DiskBlocks():
  md5 = hashlib.md5()
  
  def __init__(self, total_num_blocks, block_size, delayat):
    # This class stores the raw block array
    self.block = []
    # initialize request counter
    self.counter = 0
    self.delayat = delayat
    self.checksum = {} # block_number: checksum dict
    self.make_corrupt = True
    # Initialize raw blocks
    for i in range (0, total_num_blocks):
      putdata = bytearray(block_size)
      self.block.insert(i,putdata)

  def Sleep(self):
    self.counter += 1
    if (self.counter % self.delayat) == 0:
      time.sleep(10)

if __name__ == "__main__":

  # Construct the argument parser
  ap = argparse.ArgumentParser()

  ap.add_argument('-nb', '--total_num_blocks', type=int, help='an integer value')
  ap.add_argument('-bs', '--block_size', type=int, help='an integer value')
  ap.add_argument('-port', '--port', type=int, help='an integer value')
  ap.add_argument('-delayat', '--delayat', type=int, help='an integer value')
  ap.add_argument('-cblk', '--corrupted_block_number', type=int, help='block number')

  args = ap.parse_args()

  if args.total_num_blocks:
    TOTAL_NUM_BLOCKS = args.total_num_blocks
  else:
    print('Must specify total number of blocks')
    quit()

  if args.block_size:
    BLOCK_SIZE = args.block_size
  else:
    print('Must specify block size')
    quit()

  if args.port:
    PORT = args.port
  else:
    print('Must specify port number')
    quit()

  if args.delayat:
    delayat = args.delayat
  else:
    # initialize delayat with artificially large number
    delayat = 1000000000
  
  cblk = None
  if args.corrupted_block_number:
    cblk = args.corrupted_block_number

  # initialize blocks
  RawBlocks = DiskBlocks(TOTAL_NUM_BLOCKS, BLOCK_SIZE, delayat)

  # Create server
  server = SimpleXMLRPCServer(("127.0.0.1", PORT), requestHandler=RequestHandler)


  def Get(block_number):
    print('GET: ' + str(PORT) + ' ' + str(block_number))
    has_error = False
    result = RawBlocks.block[block_number]
    current_checksum = hashlib.md5(result).hexdigest()
    # fetch checksum from cache
    block_checksum = RawBlocks.checksum.get(block_number)
    # print('>>> Checksum Returned From GET Server ', block_checksum)
    if block_checksum != None and current_checksum != block_checksum:
      print('>>> Corrupt Block Detected: Checksum Mismatch')
      has_error = True
    RawBlocks.Sleep()
    return result, has_error

  server.register_function(Get)

  def Put(block_number, data):
    print('PUT: ' + str(PORT) + ' ' + str(block_number))
    RawBlocks.block[block_number] = data.data
    block_checksum = hashlib.md5(data.data).hexdigest()
    # emulating corruption
    print('>>> Checksum Returned From PUT Server ', cblk, block_number)
    if block_number == cblk and RawBlocks.make_corrupt: 
      RawBlocks.make_corrupt = False
      block_checksum = block_checksum[:5] + '12345'
    RawBlocks.checksum[block_number] = block_checksum
    RawBlocks.Sleep()
    # print('>>> Returned From PUT Server: Stored Checksum ', block_checksum)
    return 0

  server.register_function(Put)

  def RSM(block_number):
    RSM_LOCKED = bytearray(b'\x01') * 1
    has_error = False
    result = RawBlocks.block[block_number]
    # current_checksum = hashlib.md5(result).hexdigest()
     # fetch checksum from cache
    # block_checksum = RawBlocks.checksum.get(block_number)
    # print('>>> Checksum Returned From GET Server ', block_checksum)
    # if block_checksum != None and current_checksum != block_checksum:
    #   print('>>> Corrupt Block Detected: Checksum Mismatch')
    #   has_error = True
    RawBlocks.block[block_number] = bytearray(RSM_LOCKED.ljust(BLOCK_SIZE,b'\x01'))
    # RawBlocks.checksum[block_number] = hashlib.md5(RSM_LOCKED).hexdigest()
    # RawBlocks.Sleep()
    return result, has_error

  server.register_function(RSM)

  # Run the server's main loop
  print ("Running block server with nb=" + str(TOTAL_NUM_BLOCKS) + ", bs=" + str(BLOCK_SIZE) + " on port " + str(PORT))
  server.serve_forever()