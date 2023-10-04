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


