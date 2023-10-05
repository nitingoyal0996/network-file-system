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

  def Link(self, target, name, cwd):

    #  validate whether the file exist - 
    target_inode_number = self.PathToInodeNumber(target, cwd)
    if target_inode_number == -1:
      logging.debug("ERROR_LINK_TARGET_DOESNOT_EXIST " + str(target))
      return -1, "ERROR_LINK_TARGET_DOESNOT_EXIST"

    # Ensure Link directory type is directory -
    cwd_inode = InodeNumber(cwd)
    cwd_inode.InodeNumberToInode(self.FileNameObject.RawBlocks)
    if cwd_inode.inode.type != fsconfig.INODE_TYPE_DIR:
      logging.debug("ERROR_LINK_NOT_DIRECTORY " + str(cwd))
      return -1, "ERROR_LINK_NOT_DIRECTORY"

    print(cwd)

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

    return 0, 'SUCCESS'
