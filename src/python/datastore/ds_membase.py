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

"""An interface to a Membase based backend store."""

import apiserver.const as C

import memcache                 # Use Memcache bindings (for now).
memcache.SERVER_MAX_VALUE_LENGTH = C.MEMBASE_MAX_VALUE_LENGTH # Update limit.

import types
import threading

from apiserver.osmelement import new_osm_element, OSMElement
from datastore.ds import DatastoreBase
from datastore.slabutil import *

class DatastoreMembase(DatastoreBase):
    "An interface to a Membase (www.membase.org) datastore."

    SLAB_CONFIGURATION_KEYS =  [C.CHANGESETS_PER_SLAB, C.NODES_PER_SLAB,
                                C.RELATIONS_PER_SLAB, C.WAYS_PER_SLAB]

    def __init__(self, config, usethreads=False, writeback=False):
        "Initialize the datastore."

        self.conndb = {}

        DatastoreBase.__init__(self, config, usethreads, writeback)

        dbhosts = config.get(C.MEMBASE, C.DBHOST)
        dbport = config.get(C.MEMBASE, C.DBPORT)

        self.membasehosts = [h + ':' + dbport for h in dbhosts.split()]

        threads = [threading.currentThread()]
        if usethreads:
            threads.extend(self.threads)

        self.register_threads(threads)

        if writeback:
            # Store slab configuration information for subsequent
            # retrieval by the front end.
            slabconfig = new_osm_element(C.DATASTORE_CONFIG, C.CFGSLAB)
            for k in DatastoreMembase.SLAB_CONFIGURATION_KEYS:
                slabconfig[k] = config.get(C.DATASTORE, k)
            slabconfig[C.CONFIGURATION_SCHEMA_VERSION] = C.CFGVERSION
            self.slabconfig = slabconfig
        else:
            # Read slab configuration information from the data store.
            self.slabconfig = slabconfig = \
                self.retrieve_element(C.DATASTORE_CONFIG, C.CFGSLAB)
            if slabconfig is not None:
                schema_version = slabconfig.get(C.CONFIGURATION_SCHEMA_VERSION)
                if schema_version != C.CFGVERSION:
                    raise ValueError, \
                        "Datastore schema version mismatch: expected %s, " \
                        "actual %s." % \
                        (str(C.CFGVERSION), str(schema_version))
                for (k,v) in slabconfig.items():
                    if k in DatastoreMembase.SLAB_CONFIGURATION_KEYS:
                        config.set(C.DATASTORE, k, v)
            else:
                raise ValueError, \
                    "Datastore is missing configuration information."


    def _get_connection(self):
        return self.conndb[threading.currentThread().name]

    def register_threads(self, threads):
        "Register threads with the datastore module."
        for t in threads:
            c = memcache.Client(self.membasehosts, debug=1)
            self.conndb[t.name] = c

    def retrieve_element(self, namespace, key):
        """Return the element for a key.

        Parameters:

        namespace	- namespace for element.
        key		- the key to retrieve.
        """

        dskey = namespace[0].upper() + key

        db = self._get_connection()
        wirebits = db.get(dskey)

        if wirebits is None:
            return None
        n = new_osm_element(namespace, key)
        n.from_mapping(self.decode(wirebits))
        return n

    def store_element(self, namespace, key, value):
        """Store an element at a key."""

        assert isinstance(value, OSMElement)

        dskey = namespace[0].upper() + key
        db = self._get_connection()
        db.set(dskey, self.encode(value.as_mapping()))

    def retrieve_slab(self, namespace, slabkey):
        """Return a slab of elements."""

        db = self._get_connection()
        wirebits = db.get(slabkey)

        if wirebits is None:
            return None

        slab = []
        for (st, kv) in self.decode(wirebits):
            if st == C.SLAB_NOT_PRESENT:
                continue

            if st == C.SLAB_INDIRECT:
                elem = self.retrieve_element(namespace, kv)
                assert elem is not None, "Missing indirect element"
            elif st == C.SLAB_INLINE:
                elem = new_osm_element(namespace, kv[C.ID])
                elem.from_mapping(kv)
            else:
                assert False, "Unknown status %d" % status
            slab.append((elem.id, elem))

        return slab

    def store_slab(self, namespace, slabkey, slabelems):
        """Store a slab's worth of contents."""

        _, nperslab = slabutil_get_config(namespace)
        assert len(slabelems) == nperslab

        slab = []
        for (st, e) in slabelems.items():
            if st:
                # Todo ... INDIRECT elements.
                slab.append((C.SLAB_INLINE, e.as_mapping()))

        rawbits = self.encode(slab)
        db = self._get_connection()
        db.set(slabkey, rawbits)

    def initialize(self):
        "Initialize the database."
        # Flush all existing elements.
        self.conndb[threading.currentThread().name].flush_all()

        # Save the current slab configuration.
        self.store_element(C.DATASTORE_CONFIG, C.CFGSLAB, self.slabconfig)


Datastore = DatastoreMembase
