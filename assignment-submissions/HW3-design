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
