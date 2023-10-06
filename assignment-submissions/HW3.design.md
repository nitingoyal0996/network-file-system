# HW3 Design

## _LINK()_: Hard Link

We are essentially create a new name for the existing data that's present inside a file at a given context (potentially someplace other than the source directory) -

To acomplish this function should be able to -

### _shell.py_

- add `lnh` command definition with two input - file source and target link name. Since we are creating the hardlink in context of the current working directory, the value for the target directory will be managed by the variable `cwd`

### _absolutepath.py_

0. Performing validations => first priority is to perform validations and implement error handling as required in the porblem.

1. After validation, all we need is - a. inode number of the file (target) we want, b. cwd inode number and then call FileNameObject.InsertFilenameInodeNumber() to insert the new (filename-inode) entry into the directory inode table

2. Finally, we need to increase the reference count for the target file Inode by one.

## _SYMLINK()_: Soft Link

Symbolic links unlike hard links, creates a pointer to the original data directory/file. (they do not even have the same permissions as the original directory/file)

We need a type for the symlink file as 'INODE_TYPE_SYM' as given in the file system.

a. find and create a new inode to hold information about the symlink. - FindAvailableInode()
b. validate whether the total available block_size is sufficient to store the original file path. - replicate checks on the bounds like Write operation. (inode offset + len(original_file_path) < fsconfig.MAX_FILE_SIZE)
c. allocate an available and required number of blocks to store the original file path. and append the allocated blocks to the inode.block_numbers[] array.
d. write the original file path to the allocated blocks. and increment the reference count for the symlink inode.
e. save the symlink inode information into blocks - StoreInode()
f. save the inode <-> symlink_name mapping into the directory table - InsertFilenameInodeNumber()
g. we now increament the directory inode reference count with 1 and save this information. - StoreInode()
e. _Note_: we don't need to increment the value for the original file since the symlink is not referencing but rather pointing towards this.

Along with defining the _symlink()_ function we also need to modify few of the _shell.py_ commands.

## _shell.py_ > ls

ls command to indicate symlinks.

Check if the inode.type == SYM, if true - retrieve data from the blocks for the file_path and create an array to log into the terminal - 

@linkName -> /path/to/target/file

## _shell.py_ > mirror, slice, cat, cd:

we need to update the default `FileNameOperation.FileNameObject.Lookup` to `AbsolutePathNameObject.GeneralPathToInodeNumber`
