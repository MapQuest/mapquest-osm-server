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

"""An interface to the datastore."""

import threading

import apiserver.const as C

from apiserver.osmelement import decode_json, decode_protobuf, encode_json, \
    encode_protobuf
from datastore.lrucache import LRUIOCache
from datastore.slabutil import *

import threading
from Queue import Queue

class DatastoreBase:
    """Base class for accessing a data store."""

    VALID_NAMESPACES = [
        C.CHANGESET, C.GEODOC, C.NODE, C.RELATION, C.WAY
        ]

    def __init__(self, config, usethreads=False, writeback=False):
        "Initialize the datastore."
        encoding = config.get(C.DATASTORE, C.DATASTORE_ENCODING)
        if encoding == C.JSON:
            self.decode = decode_json
            self.encode = encode_json
        elif encoding == C.PROTOBUF:
            self.decode = decode_protobuf
            self.encode = encode_protobuf
        bound = config.getint(C.DATASTORE, C.SLAB_LRU_SIZE)
        if bound <= 0:
            raise ValueError, "Illegal SLAB LRU size %d" % bound
        if writeback:
            if usethreads:
                nthreads = config.getint(C.DATASTORE, C.SLAB_LRU_THREADS)
            else:
                nthreads = 0
            self.nthreads = nthreads
            if nthreads:
                self.threads = []
                self.workqueue = Queue(nthreads)
                for n in xrange(nthreads):
                    t = threading.Thread(target=self._worker)
                    self.threads.append(t)
                    t.daemon = True
                    t.name = "DS-%d" % n
                    t.start()
                callback = self._cbthreaded
            else:
                callback = self._cbwrite
        else:
            callback = None
        self.cache = LRUIOCache(bound=bound, callback=callback)

    def _worker(self):
        "Helper for the threaded case."
        while True:
            slabkey, slabdesc = self.workqueue.get()
            self._cbwrite(slabkey, slabdesc)

    def _cbthreaded(self, slabkey, slabdesc):
        "Call back for the threaded case: add job to the work queue."
        self.workqueue.put((slabkey, slabdesc))


    def _cbwrite(self, slabkey, slabdesc):
        "Write back a slab."
        self.store_slab(slabdesc.namespace, slabkey, slabdesc)
        if self.nthreads:
            assert self.cache.isiopending(slabkey)
            self.workqueue.task_done()
        self.cache.iodone(slabkey)

    def fetch_keys(self, namespace, keys, cacheable=True):
        """Return an iterator returning values for keys.

        Parameters:

        namespace	- element namespace
        keys		- a list of keys to retrieve.
        cacheable       - True if values from the data store are to
                          be cached.
        """

        assert namespace in DatastoreBase.VALID_NAMESPACES

        # Retrieve the requested keys from the cache, if present
        # there.
        keys_to_retrieve = set()
        elements = []

        for k in keys:
            assert isinstance(k, basestring)
            v = self.cache.get(namespace, k)
            if v:               # Status is known.
                assert len(v) == 2
                assert isinstance(v, tuple)
                elements.append(v)
            else:               # Status is unknown.
                keys_to_retrieve.add(k)

        # Return elements that were present in the cache.
        for elem in elements:
            yield elem

        if len(keys_to_retrieve) == 0:
            return

        # Retrieve elements that were not in cache from the backing
        # store.
        if slabutil_use_slab(namespace):
            slabkeyset = slabutil_group_keys(namespace, keys_to_retrieve)

            while len(slabkeyset) > 0:
                elements = []
                sk, keys = slabkeyset.popitem()

                # Read in the slab from the data store.
                items = self.retrieve_slab(namespace, sk)

                # Nothing to do if the entire slab missing.
                if items is None:
                    continue

                # Prepare a slab descriptor, insert its contents into the cache.
                slabdesc = slabutil_make_slab(namespace, items)
                self.cache.insert_slab(slabdesc)

                # Bring in elements.
                for k in keys:
                    try:
                        elements.append(self.cache.get(namespace, k))
                        keys_to_retrieve.remove(k)
                    except KeyError:
                        assert False, "Element %s:%s not in cache" % (sk, k)

                # Return elements from this slab.
                for elem in elements:
                    yield elem
        else:
            for k in keys_to_retrieve:
                elem = self.retrieve_element(namespace, k)
                if elem is None:
                    yield (False, k)
                else:
                    yield (True, elem)
            return

        # Return status information for keys that were missing in the
        # data store.
        for k in keys_to_retrieve:
            yield (False, k)

    def fetch(self, namespace, key):
        """Retrieve one value from the datastore."""

        assert type(key) == str

        if namespace not in DatastoreBase.VALID_NAMESPACES:
            raise KeyError, namespace

        elems = [e for e in self.fetch_keys(namespace, [key])]

        # Only one key should be returned for a given key.
        assert len(elems) == 1, \
            'Multiple values for ns,key="%s","%s": %s' % \
            (namespace, key, elems)

        rstatus, elem = elems[0]
        if rstatus:
            return elem
        else:
            return None

    def store(self, elem):
        "Create a new element in the data store."

        ns = elem.namespace
        elemid = elem.id
        slabdesc = self.cache.get_slab(ns, elemid)
        if slabdesc is None:    # New slab.
            slabdesc = slabutil_make_slab(ns, [(elemid, elem)])
            self.cache.insert_slab(slabdesc)
        else:
            slabdesc.add(elemid, elem)

    def _abort(self, *args, **kw):
        raise TypeError, "Abstract method invoked"

    def finalize(self):
        "Write back caches and finish pending I/Os."
        self.cache.flush()
        if self.nthreads:
            self.workqueue.join()

    # Abstract methods.
    register_threads = _abort
    retrieve_element = _abort
    retrieve_slab = _abort
    store_element = _abort
    store_slab = _abort
