# HW#4 #

Running the project:
Server: `python3 ./blockserver.py -nb 256 -bs 128 -port 8000`
client: `python3 ./fsmain.py -port 8000 -cid 0`

## `block.py` ##

### Implement Locking [DONE] ##

1. `RSM (self, block_number)`

   1. Primitive to invoke `blockserver.py` and implement locks
   2. There is going to be a single lock for the enire block array

   ```python
   ...
   block = block_server.Get(fsconfig.Total_Num_Blocks - 1)
   ...
   ```

2. `Acquire (block_number)`

   1. before performing the operation and acquiring the lock - call `CheckAndInvalidateCache ()`.
   2. Book's implementation is referred.
   3. `RSM` on block.
   4. if block is already locked - wait until it's unlocked and grab the lock.

3. `Release ()`

   1. set the block to unlocked - `RSM` block value to `0`

## Implement _at-least-once RPC_ semantic [DONE] ##

- Client resends request until receiving a response from the service, ensuring the request is processed at least once and design recover from timeouts
- setup retry mechanism for all `block.py` functions.

**Implementation:**

1. Modify `Put, Get, and RSM` definitions to implement exception handling with `try-except` block.
2. Catch `TimeoutError`
3. log `SERVER_TIMED_OUT`.
4. Setup retry - add recursive call into the `Except TimeoutError` block until call succeeds.

## Client Side _write-through_ Cache ##

1. initialize cache into `DiskBlocks ()` Constructor

```python
def __init__(self):
    ...
    self.cache: {}
    ...
    pass
```

### Write `CheckAndInvalidateCache ()` ###

1. Pull the latest CID blocks from the server
2. Compare it with the `fsconfig.CID`
3. Incase both are different - invalidate cache `cache = {}`
4. Print `CACHE_INVALIDATED`

### Refactor `Get (), Put (), RSM ()` ###

1. Refactor current function definition and implement server calls
2. Incorporate at-least-once semantics.

### Additionally - ###

#### Refactor `PUT ()` ####

1. Call server to update datablock
2. Update the client cache with data - `cache[block_number] = block_data`
3. Log `CACHE_WRITE_THROUGH`
4. Update server `CID` with `fsconfig.CID` to indicate the last update

#### `GET ()` ####

1. If the block_number is available in the cache, return `cache[block_number]`
2. Log `CACHE_HIT {BLOCK_NUMBER}`
3. If block is not in the cache OR if request is for RSM or CID block fetch it from the server.
4. Log `CACHE_MISS {BLOCK_NUMBER}`
5. Read through the unavailable data `cache[unavailable_block_number]=fetched_block_data`

## `shell.py` ##

**To Implement the _before-or-after_ atomicity:**

- Ensures that the result of every read or write operation appears as if it occurred entirely before or entirely after any other read or write operation.
- Any operation that is leading a write on the server will be eligible to update the content available on the server. This also applied to operations where we are reaching out to the server to fetch data blocks.
- Wrap the operations with locking with `Acquire()` and `Release()`

## Testing ##

- `Acquire(), Release()` were tested by manually calling them and reading the `RSM` block right after that making sure that the value is `1` in case of locked `0` in case of unlocked data block.
- `RSM()` primitive was tested individually by putting a log over `blockserver.py` and making sure that it's being called.
- Intially the challenge was to be able to implement the cache invalidation and

## Assignment Questions ##

**Solution**: profile the number of server hit before and after the cache.

1. If you implement Acquire() and Release() correctly, multi-step operations run exclusively in one client at a time to enforce before-or-after atomicity. Suppose you didn't implement Acquire()/Release(). What is one example of a race condition that can happen without the lock? Simulate a race condition in the code (comment out the lock Acquire()/Release() in the cat and append functions, and place sleep statement(s) strategically) to verify, and describe how you did it.

2. Describe, in your own words, what are the changes that were made to the Get() and Put() methods in the client, compared to the HW#3 version of the code?

   - Homework 4 divided the FS into two layers - 1. server and clients. The data now resides on the server which exposes RPCs to provide an interface for the clients to connect.
   - This required a change in `Get and Put` method to call the RPCs to fetch or update the data.
   - Caching, allowed us to reduce the number of RPCs happening to re-fetch a block of data.
   - `Put` method, after it fetches the latest data block from the server, update the cache.
   - `Get` method, before calling the RPC, checks the cache for the data block. If the block is not present it fetches the data from server and again store it in the cache.

3. At-least-once semantics may at some point give up and return (e.g. perhaps the server is down forever). How would you implement this in the code (you don't need to actually implement; just describe in words)

   - To be able to give-up or not run retry forever and get out of the retry "loop", we need a break-out condition.
   - Condition could be setup by setting up a _retry limit_.
   - This will require us keep track of retry count and use it to return eventually.
   - To implement this -
     - We would need to set up variables called `retry_limit` and `retry_count`
     - Each recursive call will increase `retry_count` by `1`
     - Update the `Except` block to include a `if` condition - `if retry_count < retry_limit` before making the call.
     - This set up will stop retrying once the `retry_limit` is reached.

4. [EEL5737 students only] Discuss in what respects this implementation is similar to NFS, and in what respects it is fundamentally different from NFS

   **Similarities:**
   - Like NFS, this implementation is a networked file system, where multiple clients could connect to a file system server.
   - This implmentation too supports and uses RPC protocols to invoke file operations on the server.

   **Differences:**
   - The main difference is the statelessness of NFS, which means that NFS does not store any information about the connected clients including - client-id. But this implementation stores it. (later version do track this but I think that's not the reference for this implementation).
   - Server Client ID here, enables us to implementation caching policies, which reduces the number of server hit rates, also reduces conflicts when server has multiple active clients.
   - This implementation locks the entire block while the NFS could support locking a file.

5. [EEL5737 students only] Evaluate the performance of the cache you implemented. Create three test benchmarks, describe the reasoning behind your tests, and evaluate: 1) the cache hit rate, and 2) the expected improvement in average latency due to the cache, assuming that the hit time is 1ms and the miss time is 100ms

      [ TODO: Ask TA ]

      **Cache Performance Evaluation:**
      Tests -

      Test 1: Writes
      Main function is to write, by doing these we see whether or not caching improves the performance by skipping the Get server hits for data.

      ```shell
         create f1 => 12 Hits, 1 Miss
               # CACHE_MISS 254
               # CACHE_HIT 4
               # CACHE_HIT 4
               # CACHE_HIT 4
               # CACHE_HIT 4
               # CACHE_HIT 4
               # CACHE_HIT 4
               # CACHE_HIT 6
               # CACHE_HIT 4
               # CACHE_HIT 4
               # CACHE_WRITE_THROUGH 4
               # CACHE_HIT 6
               # CACHE_WRITE_THROUGH 6
               # CACHE_HIT 4
               # CACHE_WRITE_THROUGH 4
               # CACHE_HIT 4
               # CACHE_WRITE_THROUGH 4
               # CACHE_WRITE_THROUGH 255
         mkdir dir => 17 Hits, 1 Miss
               # CACHE_MISS 254
               # CACHE_HIT 4
               # CACHE_HIT 4
               # CACHE_HIT 4
               # CACHE_HIT 4
               # CACHE_HIT 4
               # CACHE_HIT 4
               # CACHE_HIT 6
               # CACHE_HIT 4
               # CACHE_HIT 2
               # CACHE_HIT 2
               # CACHE_WRITE_THROUGH 2
               # CACHE_HIT 4
               # CACHE_WRITE_THROUGH 4
               # CACHE_HIT 6
               # CACHE_WRITE_THROUGH 6
               # CACHE_HIT 4
               # CACHE_WRITE_THROUGH 4
               # CACHE_MISS 7
               # CACHE_WRITE_THROUGH 7
               # CACHE_HIT 4
               # CACHE_WRITE_THROUGH 4
               # CACHE_HIT 7
               # CACHE_WRITE_THROUGH 7
               # CACHE_HIT 4
               # CACHE_WRITE_THROUGH 4
               # CACHE_HIT 4
               # CACHE_WRITE_THROUGH 4
               # CACHE_WRITE_THROUGH 255
         create f1: client 0 > append f1 withdata: client 1
            # Different client (appended from a different client) -> 9 Hits, 5 Miss
               # CACHE_MISS 254
               # CACHE_INVALIDATED
               # CACHE_WRITE_THROUGH 254
               # CACHE_MISS 4
               # CACHE_HIT 4
               # CACHE_MISS 9
               # CACHE_HIT 4
               # CACHE_HIT 4
               # CACHE_HIT 4
               # CACHE_MISS 2
               # CACHE_HIT 2
               # CACHE_HIT 2
               # CACHE_HIT 2
               # CACHE_HIT 2
               # CACHE_WRITE_THROUGH 2
               # CACHE_MISS 10
               # CACHE_WRITE_THROUGH 10
               # CACHE_HIT 4
               # CACHE_WRITE_THROUGH 4
               # Successfully appended 8 bytes.
               # CACHE_WRITE_THROUGH 255
            # Same client -> 9 Hits, 2 Miss
               # CACHE_MISS 254
               # CACHE_HIT 4
               # CACHE_HIT 4
               # CACHE_HIT 6
               # CACHE_HIT 4
               # CACHE_HIT 4
               # CACHE_HIT 4
               # CACHE_HIT 2
               # CACHE_HIT 2
               # CACHE_WRITE_THROUGH 2
               # CACHE_MISS 7
               # CACHE_WRITE_THROUGH 7
               # CACHE_HIT 4
               # CACHE_WRITE_THROUGH 4
               # Successfully appended 11 bytes.
               # CACHE_WRITE_THROUGH 255    
      ```

      Test 2: Reads + Writes
      operation performs, read and write operations on the server. This test is to see if caching improves the performance by skipping the Get server hits for data. Or if it's adding additional steps for these functions and not being helpful.

      ```shell
         slice f1 0 2 
            # Same Client (sliced on the same client) -> 11 Hits, 1 Miss
               # CACHE_MISS 254
               # CACHE_HIT 4
               # CACHE_HIT 4
               # CACHE_HIT 6
               # CACHE_HIT 4
               # CACHE_HIT 4
               # CACHE_HIT 4
               # CACHE_HIT 4
               # CACHE_HIT 7
               # CACHE_HIT 4
               # CACHE_HIT 7
               # CACHE_WRITE_THROUGH 7
               # CACHE_HIT 4
               # CACHE_WRITE_THROUGH 4
               # CACHE_WRITE_THROUGH 255
            # Different Client -> 4 Miss, 8 Hits
               # CACHE_MISS 254
               # CACHE_INVALIDATED
               # CACHE_WRITE_THROUGH 254
               # CACHE_MISS 4
               # CACHE_HIT 4
               # CACHE_MISS 8
               # CACHE_HIT 4
               # CACHE_HIT 4
               # CACHE_HIT 4
               # CACHE_HIT 4
               # CACHE_MISS 9
               # CACHE_HIT 4
               # CACHE_HIT 9
               # CACHE_WRITE_THROUGH 9
               # CACHE_HIT 4
               # CACHE_WRITE_THROUGH 4
               # CACHE_WRITE_THROUGH 255
      ```

      Test 3: Lookups & Links
      Lookups are recursive in nature and it will be interesting to see how much caching helps in this case.

      ```shell
         create f1 > append f1 withdata > cat f1
         mkdir dir > cd dir > ls
         create f1 > lnh f1 f1h
         create f1 > lns f1 f1s
      ```

      **Note:**
      1. Tests do not take cache hits/misses at while establishing the connection (the initial set of operation when we connect a client to the server) into account as they will be common for all operations.
      2. To be fair in the evaluation - for each test the server is restarted and the client is connected again.

      **Results:**
      | Test Name | Cache Hit Ratio | Latency |
      | --------- | --------------- | ------- |
      | Test 1 |                 |         |
      | Test 2 |                 |         |
      | Test 3 |                 |         |
