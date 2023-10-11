## What to turn in on Canvas ##

Summary and checklist:
All students:

- You must implement at-least-once semantics to deal with server timeouts
- You must implement RSM(), Acquire() and Release() in block.py
- You must support multiple clients and use Acquire() and Release() to ensure before-or-after atomicity for multi-step operations for each command in shell.py
- You must implement a block cache (see below) and CheckAndInvalidateCache() in block.py
- You must ensure your block cache design prints out CACHE_HIT, CACHE_MISS, CACHE_WRITE_THROUGH, and CACHE_INVALIDATE as per below
- You must test your code with the provided test environment and submit the test results
EEL-5737 students only:
- You must characterize the performance of the cache and describe your findings in the report

*PLEASE MAKE SURE TO FOLLOW THE NAMING CONVENTION BELOW* - it significantly speeds up grading. You will be deducted points for using wrong file names.
Upload to Canvas:

- A file HW4.pdf with:
  - a description of your design and implementation
  - a description of how you tested your design
  - answers to questions below
  - [EEL-5737 only] a cache performance evaluation
- A file HW4.zip with:
  - Your modified block.py
  - Your modified shell.py
  - The output of the test environment, diffs_hw4.txt

## Introduction ##

In this design+implementation assignment, you will further extend the file system to support client-server operation, multiple clients, and a simple block cache.
You are given a starting point of a client-server implementation that builds on the HW#3 code and supports RPC calls using Python's XML-RPC and a primitive based on read-and-set memory.

You are given a modified version of the file system that implements a client/server model using XMLRPC (an RPC library available for Python). The key idea behind this implementation is to separate the system into a block server (which actually stored the data and implements the raw block layer, exposing Get() and Put() interfaces via RPC, as well as a RSM() interface to support locks), and a file system client (which implements the layers above the raw layer, e.g. inodes, filename).

1) Block server (blockserver.py)

    The block server holds the file system data - think of it as implementing the raw disk (which in previous assignments was in the DiskBlocks() object) that exposes Put/Get interfaces over RPC. The raw blocks are initialized with zeroes at startup. The server exposes the following methods to the client:

    Get(block_number) returns a block, given its number
    Put(block_number, data) writes a block, given its number and data contents
    RSM(block_number, data) reads a block, sets the block contents to a LOCKED value, and returns the block read. Equivalent of the RSM primitive as discussed in class, but using a disk block instead of a memory location to hold a lock

2) Block client (block.py)

    This block client is a drop-in replacement for the block.py you used in the previous homeworks.
    Here, the key insight is that the DiskBlocks() class is now a XMLRPC client; it no longer holds the actual raw blocks data, but implements instead calls to the Get() and Put() primitives to the RPC server.
    Once Get() and Put() are implemented in this way, all the functionality that we had implemented thus far (inodes, files, etc) work, unmodified - which highlights the power of abstraction, modularity, and layering.

3) Main program

    Note that the main program fsmain.py takes two extra command-line arguments that were unused in previous assignments, but you'll use in this one:
    -cid CLIENT_ID : CLIENT_ID is an integer. It specifies a unique ID to the client. For instance, if you run two clients, you can use the command-line argument -cid 0 for one, and -cid 1 for the other
    -port PORT : PORT is an integer. It specifies to connect to the server in port number PORT. The server address is stored in global variable SERVER_ADDRESS in fsconfig.py and by default is 127.0.0.1 (localhost); there's no need to change this

## Design/implementation ##

1) Implement at-least-once semantics in block.py

    Implement at-least-once semantics for the Get(), Put() and RSM() calls in the client, such that your design is able to recover from timeouts.
    *FOR FULL CREDIT* make sure your implementation prints out the following error message (exactly this strings) when a timeout happens:

    SERVER_TIMED_OUT

2) Implement RSM(), Acquire() and Release() primitives in block.py

    You are given, in blockserver.py, a method that implements the RSM() functionality in a way similar to the textbook description - except here we're dealing with disk blocks, not memory locations.

    Here you need to implement a corresponding RSM() method in block.py that will server as a primitive for implementing locks. In your RSM() implementation, follow this convention:

    - Use the last block in raw block layer (fsconfig.TOTAL_NUM_BLOCKS-1) to store the lock. There's a single lock for the entire raw block array.
    - Use a byte value "0" as the first byte of the block to signify the lock is released
    - Use a byte value "1" as the first byte of the block to signify the lock is acquired

    Once you implement and test the client's RSM(), implement the Acquire() and Release() primitives for locking.
    Acquire() must spin-block until the lock is acquired.

3) Implement before-or-after atomicity for multi-step operations in fsshell.py

    Ensure all shell operations execute before-or-after using the primitives above. Make sure Get, Put, and RSM work properly with at-least-once semantics. Test with multiple clients.

4) Implement a client-side cache for raw blocks block.py

    Extend your client.py to support client-side caching of raw blocks for improved performance.

    Here, the idea is that if a client has fetched block(s) from the server, and while the client is guaranteed to be the only active client using the system, that it is able to keep data in a memory cache, when a block in the memory cache is references, Get() will pull data from the memory cache instead of the server - avoiding an RPC call and a round-trip over the network

    Caching in a distributed system can get very complicated, but in HW#4 you will implement a simple caching as follows:

    - Leverage Python's dict data structure to extend your DiskBlocks() class with a cache
    - This cache must be write-through - i.e., all Put()s update *both* the cache *and* the server
    - Use the next-to-last block in the raw block layer (fsconfig.TOTAL_NUM_BLOCKS-2) to store the client ID (CID) of the last writer to disk
    - Do *NOT* use lookup the cache for the last two raw blocks (RSM, CID) - always pull those values from the server
    - Implement a simple (but heavy-handed) cache invalidation policy that invalidates the *entire* client's cache at once if the client's ID is not the same as the ID of the last writer to disk

    *FOR FULL CREDIT* make sure your implementation prints out the following status messages to the screen (exactly these strings) when *each* block is found in the cache (HIT), not found (MISS), written through, and and when the cache is invalidate, respectively:

    In the messages below, replace BN with the corresponding block number

    CACHE_HIT BN
    CACHE_MISS BN
    CACHE_WRITE_THROUGH BN
    CACHE_INVALIDATED

## Assignment questions ##

Q1) If you implement Acquire() and Release() correctly, multi-step operations run exclusively in one client at a time to enforce before-or-after atomicity. Suppose you didn't implement Acquire()/Release(). What is one example of a race condition that can happen without the lock? Simulate a race condition in the code (comment out the lock Acquire()/Release() in the cat and append functions, and place sleep statement(s) strategically) to verify, and describe how you did it.

Q2) Describe, in your own words, what are the changes that were made to the Get() and Put() methods in the client, compared to the HW#3 version of the code?

Q3) At-least-once semantics may at some point give up and return (e.g. perhaps the server is down forever). How would you implement this in the code (you don't need to actually implement; just describe in words)

Q4) [EEL5737 students only] Discuss in what respects this implementation is similar to NFS, and in what respects it is fundamentally different from NFS

Q5) [EEL5737 students only] Evaluate the performance of the cache you implemented. Create three test benchmarks, describe the reasoning behind your tests, and evaluate: 1) the cache hit rate, and 2) the expected improvement in average latency due to the cache, assuming that the hit time is 1ms and the miss time is 100ms

## Hints: ##

- to deal with retries, use Python try/except clauses. In the example below, Python will try to run the [some action] code sequence. If the execution of [some action] raises [exception A] (e.g. a timeout), Python will run the code sequence [handle exception A]. Similarly, if a different[exception B] occurs, it will run the code sequence [handle exception B]
    ```
    try:
        [some action]
    except [exception A]:
        [handle exception A]
    except [exception B]:
        [handle exception B]
    ```

- there is one exception you want to look into: and socket.timeout (the server took longer than SOCKET_TIMEOUT to respond; make sure you use 10s, the SOCKET_TIMEOUT value in fsconfig.py).

- to test, you can open one terminal to run the server, and multiple terminals, each for a different client.

- test one feature at a time extensively before you move to the next one, in the order in which they are described above - i.e., make sure you test extensively 1) before you move on to implement 2), and so on

- for the cache, you can extend the DiskBlocks() method to store a dict for the block cache. A dict stores key/value pairs

- you don't need to change any other files if you implement everything correctly in block.py and shell.py

- in addition to the assignment files, you are given two simple example code files (test_putget_client.py and test_putget_server.py) as a reference to help you understand how XMLRPC works.

- when you Put() data into the server, the server expects the data to be a bytearray of size fsconfig.BLOCK_SIZE. If you only want to store one byte or integer in the first location, you still need to create a full bytearray before sending to the server. This can be done by following this pattern:
full_block = bytearray(fsconfig.BLOCK_SIZE)
full_block[0] = someinteger
