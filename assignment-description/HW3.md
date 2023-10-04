## What to turn in on Canvas ##

Summary and checklist:
All students:
- You must implement Link(), Symlink() in absolutepath.py
- You must implement the commands lns, lnh in the shell
- You must extend the implementation of cd, cat, append, mirror, and slice in the shell to resolve path names
- You must extend the implementation of ls in the shell to show symlinks
- You must test your code with the provided test environment and submit the test results
EEL-5737 students only:
- You must implement PathNameToInodeNumber() in absolutepath.py and use it to resolve all paths for cd, cat, append, mirror, slice

*PLEASE MAKE SURE TO FOLLOW THE NAMING CONVENTION BELOW* - it significantly speeds up grading. You will be deducted points for using wrong file names.
Upload to Canvas:
- A file HW3.pdf with:
  - a description of your design and implementation
  - a description of how you tested your design
- A file HW3.zip with:
  - Your modified absolutepath.py
  - Your modified shell.py
  - Your modified fsmain.py
  - The output of the test environment, diffs_hw3.txt

## Introduction ##

In this design+implementation assignment, you will further extend the file system and shell to support "hard" and "soft" (symbolic) links, as described below. A starting point for the code is provided to you in the HW#2 solution distributed in Canvas.

## Design/implementation ##

The code absolutepath.py starting point provided to you includes two additional functions not present in HW#2 that deal with path name resolution, and follow the template described in the textbook:

def PathToInodeNumber(self, path, dir):
Issues recursive Lookup() calls as necessary to resolve a relative path name (including / to resolve subdirectories, and .. to go up a level - just as in the UNIX file system) to an inode number

def GeneralPathToInodeNumber(self, path, cwd):
Resolves both relative and absolute paths (starting with /) by calling PathToInodeNumber)


1) Implement hard links: extend the design of absolutepath.py to support a Link() method for the AbsolutePathName class, and extend shell.py to support the lnh shell command, as follows:

def Link(self, target, name, cwd):
Creates a "hard" link in the context of current working directory with inode number "cwd".
"name" is a string describing the name of the link, and "target" is a string describing the path to the target.

lnh target name
Shell command that calls Link() with the shell's cwd

The Link() function must handle the following errors and return these *EXACT STRINGS* (please ensure you return these EXACT STRINGS, or points will be deducted):

ERROR_LINK_TARGET_DOESNOT_EXIST
The target does not exist in the file system

ERROR_LINK_NOT_DIRECTORY
The cwd is not an inode number of a directory

ERROR_LINK_DATA_BLOCK_NOT_AVAILABLE
There is not enough room left in the data blocks of the cwd to add another binding for this link

ERROR_LINK_ALREADY_EXISTS
There is already a binding for "name" in the cwd

ERROR_LINK_TARGET_NOT_FILE
The target must be a file (INODE_TYPE_FILE)


2) Implement soft links: extend the design of absolutepath.py to support a Symlink() method for FileName class, and extend shell.py to support the lns shell command, as follows:

def Symlink(self, target, name, cwd):
Creates a "soft" link in the context of current working directory with inode number "cwd". "name" is a string describing the name of the link, and "target" is a string describing the path to the target.

lns target name
Shell command that calls Symlink() with the shell's cwd

The Symlink() function must handle the following errors and return these *EXACT STRINGS* (please ensure you return these EXACT STRINGS, or points will be deducted):

ERROR_SYMLINK_TARGET_DOESNOT_EXIST
The target does not exist in the file system

ERROR_SYMLINK_NOT_DIRECTORY
The cwd is not an inode number of a directory

ERROR_SYMLINK_DATA_BLOCK_NOT_AVAILABLE
There is not enough room left in the data blocks of the cwd to add another binding for this link

ERROR_SYMLINK_ALREADY_EXISTS
There is already a binding for "name" in the cwd

ERROR_SYMLINK_INODE_NOT_AVAILABLE
There is no more free inodes to use to create the symlink

ERROR_SYMLINK_TARGET_EXCEEDS_BLOCK_SIZE
The name of the target is larger than the block size

Representing the symlink in the file system:
- use the INODE_TYPE_SYM for the inode created for the symlink
- allocate an inode and store the target string in the first data block (only) referenced by the inode - i.e. symlink_inode.inode.block_numbers[0]


Hint: you may want to familiarize yourself with how the UNIX file system works with links to build your intuition/confidence. In Linux, "ln" creates a hard link, and "ln -s" creates a soft link. Using "ls -alF" shows you a detailed view of the file system, including number of links in the second column

Hint: the FileNameObject.Lookup(), FileNameObject.FindAvailableFileEntry(), FileNameObject.InodeNumberToInode(), FileNameObject.StoreInode(), FileNameObject.InsertFilenameInodeNumber(), FileNameObject.FindAvailableInode() methods will be helpful

Hint: to convert the target string to a bytearray for insertion into a RawBlock, use the pattern:
    stringbyte = bytearray(target,"utf-8")
    block[0:len(target)] = stringbyte

Hint: ensure you update all refcnt values (file and directory) as appropriate for each kind of link

Hint: like in HW#2, the solution to this problem does not involve a large amount of code.
The keys to solve this problem are:
1) make sure you clearly understand how data is stored in RawBlocks (see HW#1) and how to copy data from/to the RawBlocks class (which represents the actual disk storage in a real file system implementation) to the higher-level Python classes (such as InodeNumber() and Inode(); these represent what a kernel would work with in main memory in a real file system implementation);
2) work on one sub-problem at a time, and make sure you test each sub-problem before moving to the next;
3) test iteratively: the showinode, showblock and showblockslice in the shell will help you debug and ensure your implementation is doing what you intended it to do and that you are storing data in the right format/place;
4) complement the existing debugging information with your own print statements while you develop (comment these out before submission) to help in the process

3) Enhance the "ls" implementation in memoryfs_shell.py to display soft links
You must display soft links by appending "@ -> target" to the symlink name with ls. For instance, if synmlink named "mylink" points to target "/dir1/dir2/somefile", ls must show:

    [1]:mylink@ -> /dir1/dir2/somefile

3) [EEL5737 students only]: Implement in absolutepath.py function PathNameToInodeNumber() to resolve a symlink.
For simplicity, you only need to consider the case of a symlink in the same directory, as in f2 in the example below

    Hint: think about what happens if the inode number returned by a Lookup() is INODE_TYPE_SYM