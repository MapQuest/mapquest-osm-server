# Copyright (c) 2011 AOL Inc.  All Rights Reserved.
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""A single-threaded cache supporting:
   - slab-based insertion of elements,
   - multiple namespaces,
   - lookups of individual elements in slabs,
   - LRU overflow of slabs.
"""

import collections
import threading
import types

from .slabutil import slabutil_make_slabkey

class BoundedLRUBuffer(collections.MutableMapping):
    """A bounded buffer with least-recently-used semantics.

    This buffer acts like a mapping with a bounded size.  Key/value
    pairs can be added to the buffer as with a conventional mapping.
    Once the buffer reaches its size bound, additional inserts of
    key/value pairs will cause the least recently used key/value pair
    contained in the buffer to be ejected.

    The size of the bound and an optional callback for handling
    ejected items may be specified at buffer creation time.

    >>> b = BoundedLRUBuffer(bound=16, callback=None)

    Key/value pairs are added to buffer as for a conventional mapping.

    >>> b['key'] = 'value'
    >>> len(b)
    1

    Normal mapping operations are supported.

    >>> 'key' in b
    True

    The 'pop()' method retrieves the least recently used key/value
    pair from the buffer.

    >> (k,v) = b.pop()          # Returns the least recently used pair.

    Lookups and assignments of keys mark them as being most recently
    used.

    >>> v = b['key']            # 'key' becomes most recently used.
    >>> b['key'] = 'newvalue'   # 'key' becomes most recently used.

    If a 'callback' had been specified at object creation time, it
    will be invoked with the ejected key/value pair as arguments.

    >>> def handle_overflow(key, value):
    ...     # Handle overflow here.
    ...     pass
    >>> b = BoundedLRUBuffer(callback=handle_overflow)

    The 'flush()' method may be used to empty the buffer.

    >>> b.flush()
    >>> len(b)
    0
    """

    # Methods implementing the mapping protocol.

    def __init__(self, bound=65536, callback=None):

        assert type(bound) is types.IntType
        self.bound = bound      # Max size.

        self.callback = callback
        self.indices = {}       # Map of keys to indices
        self.values = {}        # Map of indices to values.
        self.count = 0          # The number of entries in the buffer.
        self.first = -1          # Smallest index in use.
        self.next = 0  # Next index to use.

    def __str__(self):
        return "BoundedLRUBuffer(%d){%s}" % \
            (self.bound, ",".join(self.indices.keys()))

    def __contains__(self, key):
        return key in self.indices

    def __delitem__(self, key):
        index = self.indices[key]
        self._remove(index)

    def __getitem__(self, key):
        """Retrieve the item named by 'key' from the buffer.

        The value returned is pushed to the head of the buffer."""

        entry_index = self.indices[key]

        (_, entry) = self._remove(entry_index)

        next_index = self._next_index(entry_index)
        self._insert(key, entry, next_index)

        return entry

    def __iter__(self):
        return iter(self.indices)

    def __len__(self):
        "Compute the number of items in the buffer."
        v = self.count
        assert v == len(self.indices)
        assert v == len(self.values)
        return v

    def __setitem__(self, key, value):
        """Store an item indexed by argument 'key'."""

        if key in self.indices:
            index = self.indices[key]
            self._remove(index)
        else:
            index = None
        next_index = self._next_index(index)
        self._insert(key, value, next_index)
        ejected = self._maybe_eject()

        if self.callback and ejected is not None:
            self.callback(*ejected)

    def pop(self):
        "Return the first item in the LRU buffer."
        k, v = self._pop()
        return (k, v)


    # Additional method.

    def flush(self):
        "Write back the contents of the LRU buffer."
        while self.count > 0:
            k, v = self._pop()
            if self.callback:
                self.callback(k, v)


    # Internal helper functions.

    def _insert(self, key, value, lru):
        "Insert a key/value pair at the specified LRU index."
        self.values[lru] = (key, value)
        self.indices[key] = lru
        self.count += 1

    def _remove(self, index):
        "Remove the entry for key 'key'."
        key, value = self.values.pop(index)
        assert index == self.indices[key]
        self.indices.pop(key)
        self.count -= 1
        return (key, value)

    def _maybe_eject(self):
        if self.count <= self.bound:
            return None

        # Find the least recently used item.
        while self.first < self.next and not (self.first in self.values):
            self.first += 1
        assert self.first < self.next, "Empty buffer"
        return self._remove(self.first)

    def _next_index(self, index=None):
        "Compute an optimal index number for storing an element."
        # Optimize the case where we overwrite the most recently added
        # value.
        if index is not None and index == self.next - 1:
            return index
        index = self.next
        self.next += 1
        return index

    def _pop(self):
        "Helper function."
        # First the first index
        while not (self.first in self.values) and \
                self.first < self.next:
            self.first += 1
        # Look for an empty buffer.
        if self.first == self.next:
            raise IndexError, "pop from empty buffer"
        return self._remove(self.first)


class LRUCache:
    """...description here..."""

    def __init__(self, bound=65536, callback=None):
        self.bound = bound
        self.lru_cache = BoundedLRUBuffer(bound, self._lrucb)
        self.lru_key = {}
        self.callback = callback

    def __len__(self):
        return len(self.lru_key)

    def _lrucb(self, slabkey, slabdesc):
        assert slabkey not in self.lru_cache
        self._remove_slab_items(slabdesc)
        if self.callback:
            self.callback(slabkey, slabdesc)

    def _remove_slab_items(self, slabdesc):
        ns = slabdesc.namespace
        for k in slabdesc.keys():
            del self.lru_key[(ns,k)]

    def get(self, namespace, key):
        try:
            lrukey = self.lru_key[(namespace,key)]
        except KeyError:        # No such slab.
            return None
        slabdesc = self.lru_cache.get(lrukey)
        if slabdesc:
            return slabdesc.get(key) # Get item in the slab.
        else:
            return (False, key) # No such slab.

    def get_slab(self, namespace, key):
        "Return the slab descriptor for a key."
        try:
            slabkey = self.lru_key[(namespace, key)]
        except KeyError:
            return None
        return self.lru_cache[slabkey]


    def insert_slab(self, slabdesc):
        "Insert items from a slab."
        slabkey = slabdesc.slabkey
        if slabkey in self.lru_cache:
            raise ValueError, "Duplicate insertion of slab: %s" % str(slabkey)
        self.lru_cache[slabkey] = slabdesc
        ns = slabdesc.namespace
        for k in slabdesc.keys():
            itemkey = (ns,k)
            if itemkey in self.lru_key:
                raise KeyError, "Duplicate insertion of (%s,%s)" % (ns,k)
            self.lru_key[itemkey] = slabkey

    def remove_slab(self, slabdesc):
        "Remove a slab from the cache."

        slabkey = slabdesc.slabkey
        assert slabkey in self.lru_cache
        self._remove_slab_items(slabdesc)
        del self.lru_cache[slabkey]

    def flush(self):
        "Flush the contents of the cache."

        self.lru_cache.flush()

        assert len(self.lru_cache) == 0
        assert len(self.lru_key) == 0


class LRUIOCache(LRUCache):
     """An LRU cache that tracks I/O-in-flight progress of items."""

     def __init__(self, bound=65536, callback=None):
         LRUCache.__init__(self, bound, self._iocb)
         self.iocallback = callback
         self.iocond = threading.Condition()
         self.iopending = []

     def _iocb(self, slabkey, slabdesc):
         assert slabkey == slabdesc.slabkey
         with self.iocond:
             assert slabkey not in self.iopending
             self.iopending.append(slabkey)
         if self.iocallback:
             self.iocallback(slabkey, slabdesc)

     def get(self, namespace, key):
         """Retrieve an item from the cache.

         If an item is missing from the cache, wait for pending I/O to
         complete.
         """
         v = LRUCache.get(self, namespace, key)
         if v is None:
             slabkey = slabutil_make_slabkey(namespace, key)
             with self.iocond:
                 while slabkey in self.iopending:
                     self.iocond.wait()
         return v

     def isiopending(self, slabkey):
         "Return True if I/O is pending on a slab."
         with self.iocond:
             status = slabkey in self.iopending
         return status

     def iodone(self, slabkey):
         "Mark I/O on a slabkey as completed."
         with self.iocond:
             assert slabkey in self.iopending
             self.iopending.remove(slabkey)
             self.iocond.notifyAll()
