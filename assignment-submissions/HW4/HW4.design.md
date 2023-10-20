# HW#4 #

Running the project: 
Server: `python3 ./blockserver.py -nb 256 -bs 128 -port 8000`
client: `python3 ./fsmain.py -port 8000 -cid 0`

## `block.py` ##

### Implement Locking [DONE] ##

1. `RSM (self, block_number)`

   - Primitive to invoke `blockserver.py` and implement locks
   - There is going to be a single lock for the enire block array
   - Add logs to log information about the file operations

   ```python
   ...
   last_block_number = fsconfig.Total_Num_Blocks - 1
   block = Get(last_block_number)
   ...
   # get last bit of the block - that's the lock value
   # set it to locked
   # return read block information
   ```

2. `Acquire (block_number)`

   - RSM on block
   - if block is already locked - wait for it to unlock and lock it again.
   - we get the block value and set the lock over the block

3. `Release ()`

   - set the block to unlocked

## Implement _at-least-once RPC_ semantic [DONE] ##

- Client resends request until receiving a response from the service, ensuring the request is processed at least once and design recover from timeouts
- setup retry mechanism for all `block.py` functions.

Implement:

1. Modify all function definitions to implement `try-except` block.
2. Catch `TimeoutError` and log error message - `SERVER_TIMED_OUT`.
3. Retry sending the request to the client and repeat until we get a successful result

## Client Side _write-through_ Cache ##

- Update `DiskBlocks ()` Constructor

initialize the cache python lookup variable using a dictionary

```python
def __init__():
    ...
    cache: {}
    ...
    pass
```

### Write `CheckAndInvalidateCache ()` ###

1. pull the latest RSM & CID blocks from the server
2. check if any other client has written on the server
3. if yes - invalidate => reset the cached block data to NONE (how?) and log `CACHE_INVALIDATED`

### Refactor `Get (), Put (), RSM ()` ###

1. Refactor current function definition and implement server calls
2. Add locking
3. Incorporate at-least-once semantics.
4. implement cache (as follows) - `GET, PUT`

#### `PUT ()` ####

- updates both the cache and the server and log `CACHE_WRITE_THROUGH`
- updates the CID block on the server to enter the last update information
- when you Put() data into the server, the server expects the data to be a bytearray of size `fsconfig.BLOCK_SIZE`. If you only want to store one byte or integer in the first location, you still need to create a full bytearray before sending to the server. This can be done by following this pattern:

```python
...
full_block = bytearray(fsconfig.BLOCK_SIZE)
full_block[0] = someinteger
...
```

#### `GET ()` ####

- check the cache if it has the block data available on the client
- if yes, return and log `CACHE_HIT {BLOCK_NUMBER}`
- if not, fetch from the server, save it in the cache and log `CACHE_MISS {BLOCK_NUMBER}`

## TODO: `shell.py` ##

- Add Acquire() if needed
- Add Release() if needed (in some of the functions - think about which command is going to need these )

### Implementing the before-or-after atomicity ###

Reference: Chapter - 2.1.1.1

- Ensures that the result of every read or write operation appears as if it occurred entirely before or entirely after any other read or write operation.

   TODO: Design for implementing before-or-after atomicity

### Identify the multi-step operations and refactor ###

   TODO: What are they?

## Assignment Questions ##

1. Characterize the performance of the cache and findings in the report.

## Assignment questions ##

1. If you implement Acquire() and Release() correctly, multi-step operations run exclusively in one client at a time to enforce before-or-after atomicity. Suppose you didn't implement Acquire()/Release(). What is one example of a race condition that can happen without the lock? Simulate a race condition in the code (comment out the lock Acquire()/Release() in the cat and append functions, and place sleep statement(s) strategically) to verify, and describe how you did it.

2. Describe, in your own words, what are the changes that were made to the Get() and Put() methods in the client, compared to the HW#3 version of the code?

3. At-least-once semantics may at some point give up and return (e.g. perhaps the server is down forever). How would you implement this in the code (you don't need to actually implement; just describe in words)

4. [EEL5737 students only] Discuss in what respects this implementation is similar to NFS, and in what respects it is fundamentally different from NFS

5. [EEL5737 students only] Evaluate the performance of the cache you implemented. Create three test benchmarks, describe the reasoning behind your tests, and evaluate: 1) the cache hit rate, and 2) the expected improvement in average latency due to the cache, assuming that the hit time is 1ms and the miss time is 100ms
