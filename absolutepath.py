import fsconfig
import logging
from block import *
from inode import *
from inodenumber import *
from filename import *

## This class implements methods for absolute path layer

class AbsolutePathName():
  def __init__(self, FileNameObject):
    self.FileNameObject = FileNameObject

  def PathToInodeNumber(self, path, dir):

    logging.debug("AbsolutePathName::PathToInodeNumber: path: " + str(path) + ", dir: " + str(dir))

    if "/" in path:
      split_path = path.split("/")
      first = split_path[0]
      del split_path[0]
      rest = "/".join(split_path)
      logging.debug("AbsolutePathName::PathToInodeNumber: first: " + str(first) + ", rest: " + str(rest))
      d = self.FileNameObject.Lookup(first, dir)
      if d == -1:
        return -1
      return self.PathToInodeNumber(rest, d)
    else:
      return self.FileNameObject.Lookup(path, dir)


  def GeneralPathToInodeNumber(self, path, cwd):

    logging.debug ("AbsolutePathName::GeneralPathToInodeNumber: path: " + str(path) + ", cwd: " + str(cwd))

    if path[0] == "/":
      if len(path) == 1: # special case: root
        logging.debug ("AbsolutePathName::GeneralPathToInodeNumber: returning root inode 0")
        return 0
      cut_path = path[1:len(path)]
      logging.debug ("AbsolutePathName::GeneralPathToInodeNumber: cut_path: " + str(cut_path))
      return self.PathToInodeNumber(cut_path,0)
    else:
      return self.PathToInodeNumber(path,cwd)
    
  def PathNameToInodeNumber(self, name, cwd):
    logging.debug("AbsolutePathName:: PathNameToInodeNumber: pathname: " + str (name))
    inode_number = self.GeneralPathToInodeNumber(name, cwd)
    inobj = InodeNumber(inode_number)
    inobj.InodeNumberToInode(self.FileNameObject.RawBlocks)
    if inobj.inode.type == fsconfig.INODE_TYPE_SYM:
      # get path from the inobj blocknumbers.
      file_path = ""
      read_bytes = 0
      # print('>> block array: ', inobj.inode.block_numbers)
      for b in inobj.inode.block_numbers:
        file_path_raw = self.FileNameObject.RawBlocks.Get(b)
        # file_path += file_path_raw.decode()
        file_size = inobj.inode.size
        logging.debug('AbsolutePathName:: PathNameToInodeNumber:: File Size: ' + str(file_size) + "XXXXXXXXXXXX")
        logging.debug('AbsolutePathName:: PathNameToInodeNumber:: Read Raw File Path: ' + str(file_path_raw) + "XXXXXXXXXXXX")
        # if filesize is less than a block's size, read the file size
        if (file_size < fsconfig.BLOCK_SIZE):
          file_path += file_path_raw[0: file_size].decode()
          read_bytes += file_size
        else:
          # otherwise read the block size
          file_path += file_path_raw.decode()
          read_bytes += fsconfig.BLOCK_SIZE
        logging.debug('AbsolutePathName:: PathNameToInodeNumber:: Read Raw File Decoded: ' + str(file_path.strip())+ "XXXXXXXXXXXX")
        # print('>> file_path: ', file_path)
      inode_number = self.GeneralPathToInodeNumber(file_path, cwd)
    logging.debug("AbsolutePathName:: PathNameToInodeNumber: return inode_number: " + str(inode_number))
    return inode_number


  def Link(self, target, name, cwd):

    #  validate whether the file exist - 
    target_inode_number = self.PathNameToInodeNumber(target, cwd)
    if target_inode_number == -1:
      logging.debug("ERROR_LINK_TARGET_DOESNOT_EXIST " + str(target))
      return -1, "ERROR_LINK_TARGET_DOESNOT_EXIST"

    # Ensure Link directory type is directory -
    cwd_inode = InodeNumber(cwd)
    cwd_inode.InodeNumberToInode(self.FileNameObject.RawBlocks)
    if cwd_inode.inode.type != fsconfig.INODE_TYPE_DIR:
      logging.debug("ERROR_LINK_NOT_DIRECTORY " + str(cwd))
      return -1, "ERROR_LINK_NOT_DIRECTORY"

    # Find available slot in directory data block
    linkentry_position = self.FileNameObject.FindAvailableFileEntry(cwd)
    if linkentry_position == -1:
      logging.debug("ERROR_LINK_DATA_BLOCK_NOT_AVAILABLE")
      return -1, "ERROR_LINK_DATA_BLOCK_NOT_AVAILABLE"

    # Ensure it's not a duplicate - if Lookup returns anything other than -1
    if self.FileNameObject.Lookup(name, cwd) != -1:
      logging.debug("ERROR_LINK_ALREADY_EXISTS " + str(name))
      return -1, "ERROR_LINK_ALREADY_EXISTS"

    # Ensure the target is infact a file
    target_inode = InodeNumber(target_inode_number)
    target_inode.InodeNumberToInode(self.FileNameObject.RawBlocks)
    if target_inode.inode.type != fsconfig.INODE_TYPE_FILE:
      logging.debug("ERROR_LINK_TARGET_NOT_FILE " + str(target_inode_number))
      return -1, "ERROR_LINK_TARGET_NOT_FILE"

    logging.debug("FileOperations::Link: link_name: " + str(name) + ", filename: " + str(target) + ", cwd: " + str(cwd))
    
    # Insert file name information from source file inode to available entry
    self.FileNameObject.InsertFilenameInodeNumber(cwd_inode, name, target_inode_number)

    # Increase Reference count for the source file Inode by one
    target_inode.inode.refcnt = target_inode.inode.refcnt + 1
    target_inode.StoreInode(self.FileNameObject.RawBlocks)

    # Increase reference count for the cwd by one
    cwd_inode.inode.refcnt = cwd_inode.inode.refcnt + 1
    cwd_inode.StoreInode(self.FileNameObject.RawBlocks)

    return 0, 'SUCCESS'

  def Symlink (self, target, name, cwd):
    # print(">>>> run symlink")

    # ensure we have a valid target 
    target_inode_number = self.GeneralPathToInodeNumber(target, cwd)
    if target_inode_number == -1:
      logging.debug("ERROR_SYMLINK_TARGET_DOESNOT_EXIST " + str(target))
      return -1, "ERROR_SYMLINK_TARGET_DOESNOT_EXIST"
    
    target_inode = InodeNumber(target_inode_number)
    target_inode.InodeNumberToInode(self.FileNameObject.RawBlocks)

    cwd_inode = InodeNumber(cwd)
    cwd_inode.InodeNumberToInode(self.FileNameObject.RawBlocks)
    if cwd_inode.inode.type != fsconfig.INODE_TYPE_DIR:
      logging.debug('ERROR_SYMLINK_NOT_DIRECTORY', cwd)
      return -1, "ERROR_SYMLINK_NOT_DIRECTORY"

    fileentry_position = self.FileNameObject.FindAvailableFileEntry(cwd)
    if fileentry_position == -1:
      logging.debug('ERROR_SYMLINK_DATA_BLOCK_NOT_AVAILABLE')
      return -1, "ERROR_SYMLINK_DATA_BLOCK_NOT_AVAILABLE"

    # validate for duplicate symlink
    if self.FileNameObject.Lookup(name, cwd) != -1:
      logging.debug('ERROR_SYMLINK_ALREADY_EXISTS' + str(target))
      return -1, "ERROR_SYMLINK_ALREADY_EXISTS"
    
    # ERROR_SYMLINK_INODE_NOT_AVAILABLE
    # Find if there is an available inode
    inode_position = self.FileNameObject.FindAvailableInode()
    if inode_position == -1:
        logging.debug("ERROR_SYMLINK_INODE_NOT_AVAILABLE")
        return -1, "ERROR_SYMLINK_INODE_NOT_AVAILABLE"
      
    new_inode = InodeNumber(inode_position)
    new_inode.InodeNumberToInode(self.FileNameObject.RawBlocks)

    file_path_byte_array = bytearray(target, "utf-8")
    inode_offset = new_inode.inode.size
    
    if inode_offset + len(file_path_byte_array) > fsconfig.MAX_FILE_SIZE:
      logging.debug("ERROR_SYMLINK_TARGET_EXCEEDS_BLOCK_SIZE. Available max: " + str(fsconfig.MAX_FILE_SIZE) + ", path size: " + str(file_path_byte_array))
      return -1, "ERROR_SYMLINK_TARGET_EXCEEDS_BLOCK_SIZE"
    
    # update symlink inode configurations - 
    new_inode.inode.type = fsconfig.INODE_TYPE_SYM
    new_inode.inode.refcnt = 1

    # print('num of blocks required: ', num_of_blocks_required)

    bytes_written = 0
    current_offset = inode_offset
    data = file_path_byte_array
    # the data to be written may span multiple blocks
    # this loop iterates through one or more blocks, ending when all data is written
    while bytes_written < len(data):
        # determine block index corresponding to the current offset where the write should take place
        current_block_index = current_offset // fsconfig.BLOCK_SIZE

        # determine the next block's boundary (in Bytes relative to the file's offset 0)
        next_block_boundary = (current_block_index + 1) * fsconfig.BLOCK_SIZE
        write_start = current_offset % fsconfig.BLOCK_SIZE
        if (inode_offset + len(data)) >= next_block_boundary:
            write_end = fsconfig.BLOCK_SIZE
        else:
            # otherwise, the data is truncated within this block
            write_end = (inode_offset + len(data)) % fsconfig.BLOCK_SIZE

        logging.debug('AbsolutePathName::Create Symlink: write_start: ' + str(write_start) + ' , write_end: ' + str(write_end))

        # retrieve index of block to be written from inode's list
        block_number = new_inode.inode.block_numbers[current_block_index]

        # if the data block to be written is not allocated (i.e. the block_numbers list in the inode is zero at
        # current_block_index), we need to allocate it
        if block_number == 0:
            # allocate new data block
            new_block = self.FileNameObject.AllocateDataBlock()
            # update inode's block number list (it will be written to raw storage before the method returns)
            new_inode.inode.block_numbers[current_block_index] = new_block
            block_number = new_block

        # load existing block data from the disk
        block = self.FileNameObject.RawBlocks.Get(block_number)
        # copy slice of data into the right position in this block
        logging.debug('AbsolutePathName:: Create Symlink: Write Data: '+ str(data.decode()) + ", "+ str(data))
        block[write_start:write_end] = data[bytes_written:bytes_written + (write_end - write_start)]
        # write modified block back to disk
        self.FileNameObject.RawBlocks.Put(block_number, block)
        # update offset, bytes written
        current_offset += write_end - write_start
        bytes_written += write_end - write_start

        logging.debug('AbsolutePathName::Create Symlink: current_offset: ' + str(current_offset) + ' , bytes_written: ' + str(
            bytes_written) + ' , len(data): ' + str(len(data)))

    # save symlink inode information
    new_inode.inode.size = inode_offset + bytes_written
    new_inode.StoreInode(self.FileNameObject.RawBlocks)

    # Insert file name information from source file inode to available entry
    self.FileNameObject.InsertFilenameInodeNumber(cwd_inode, name, new_inode.inode_number)

    # increment cwd reference count 
    cwd_inode.inode.refcnt = cwd_inode.inode.refcnt + 1
    cwd_inode.StoreInode(self.FileNameObject.RawBlocks)

    return 0, 'SUCCESS'