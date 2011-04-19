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

"""Group OSM nodes by their (lat, lon) coordinates.

Exported classes:

  class GeoGroupTable -- track a set of geographical groupings.

Usage:

    1. Allocate a new table
    >>> gt = GeoGroupTable()

    2. Add nodes to the table
    >>> for n in nodelist: gt.add(n)

    3. Iterate over the unique groups
    >>> for k in gt.keys():
    ...     print "Key:", k, "nodes:", gt[k]
    >>>
"""

import geohash
import collections
import threading
from Queue import Queue

import apiserver.const as C
from apiserver.osmelement import new_osm_element
from datastore.lrucache import BoundedLRUBuffer
from datastore.ds_geohash import geohash_key_for_element

class GeoGroupTable:
    '''Group OSM nodes by their geographical coordinates.

    The coordinates of the globe are partitioned into disjoint areas.
    Each partition is named by the geohash code of its (n,w) corner.

    Grouping of nodes is implemented by restricting the length of
    the geohash codes used.
    '''

    def __init__(self, config, options, db):
        '''Initialize the table.

        Keyword arguments:
        config        - A ConfigParser instance.
        options       - An optparse.OptionParser structure.
        db            - A DB object supporting 'get()' and 'store()'
                        methods.
        '''
        self.geodb = collections.defaultdict(set)
        self.db = db

        lrusize = config.getint(C.DATASTORE, C.GEODOC_LRU_SIZE)
        self.lru = BoundedLRUBuffer(bound=lrusize, callback=self._cb)

        if options.nothreading:
            nthreads = 0
        else:
            nthreads = config.getint(C.DATASTORE, C.GEODOC_LRU_THREADS)
        self.nthreads = max(0, nthreads)
        if self.nthreads:
            self.wrthreads = []
            self.wrqueue = Queue(self.nthreads)
            self.wrcond = threading.Condition()
            self.wrpending = []
            for n in range(self.nthreads):
                t = threading.Thread(target=self._worker)
                t.name = "GeoWB-%d" % n
                t.daemon = True
                self.wrthreads.append(t)
                t.start()

            db.register_threads(self.wrthreads)

    def _cb(self, key, value):
        "Callback called when an LRU item is ejected."
        nodeset = self.geodb.pop(key)
        if self.nthreads:       # Defer processing to a worker thread.
            self.wrqueue.put((key, nodeset))
        else:                   # Synchronous operation.
            self._write_geodoc(key, nodeset)

    def _worker(self):
        "Helper method, used by worker threads."
        while True:
            # Retrieve a work item.
            v = self.wrqueue.get()
            if v is None:     # Exit the thread.
                self.wrqueue.task_done()
                return

            # Unpack the work item.
            key, nodeset = v

            # Mark the item as "I/O in progress".
            with self.wrcond:
                while key in self.wrpending:
                    self.wrcond.wait()

                assert key not in self.wrpending
                self.wrpending.append(key)

            # Process this node set.
            self._write_geodoc(key, nodeset)

            # Remove the "I/O in progress" marker.
            with self.wrcond:
                assert key in self.wrpending
                self.wrpending.remove(key)
                self.wrcond.notifyAll()

            self.wrqueue.task_done()

    def _write_geodoc(self, key, nodeset):
        "Merge in a set of nodes into a geodoc."
        geodoc = self.db.retrieve_element(C.GEODOC, key)
        if geodoc is None:      # New document.
            geodoc = new_osm_element(C.GEODOC, key)
        geodoc[C.NODES].update(nodeset)
        self.db.store_element(C.GEODOC, key, geodoc)

    def add(self, elem):
        '''Add information about a node 'elem' to the geo table.

        Usage:
        >>> gt = GeoGroupTable()
        >>> gt = gt.add(elem)

        The node 'elem' should have a 'lat' and 'lon' fields that
        encode its latitude and longitude respectively.  The 'id'
        field specifies the node's "id".
        '''

        assert elem.namespace == C.NODE, "elem is not a node: %s" % str(elem)

        # Determine the geo-key for the node.
        ghkey = geohash_key_for_element(elem)
        # Retrieve the partition covering this location.
        ghdoc = self.geodb[ghkey]

        elemid = elem.id
        if elemid not in ghdoc:
            ghdoc.add(elemid)
            self.lru[ghkey] = ghdoc

    def flush(self):
        "Wait pending I/Os"

        # Flush items from the LRU.
        self.lru.flush()

        if self.nthreads:
            # Wait for the work queue to drain.
            self.wrqueue.join()
