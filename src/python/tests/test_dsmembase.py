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

import apiserver.const as C
import memcache
import json
import pytest

from datastore.ds_membase import Datastore
from datastore.slabutil import slabutil_init
from ConfigParser import ConfigParser
import apiserver.osmelement as O

__BADNAMESPACE = 'badnamespace'
__DBHOST = 'localhost'
__DBPORT = '11211'
__INLINE_SIZE = 256
__NOSUCHKEY = '__NOSUCHKEY__'
__NOSUCHSLABELEMKEY = '-1'
__PER_SLAB = 8
__SLAB_LRU_SIZE = 8
__SLAB_LRU_THREADS = 4

# Helper function.
def insert_key(key, value):
    c = memcache.Client(['%s:%s' % (__DBHOST, __DBPORT)])
    c.set(key, value)

def retrieve_key(key):
    c = memcache.Client(['%s:%s' % (__DBHOST, __DBPORT)])
    return c.get(key)

def pytest_funcarg__datastore(request):
    "Prepare a configuration parser object"

    cfg = ConfigParser()
    cfg.add_section(C.DATASTORE)

    for k in [C.CHANGESETS_INLINE_SIZE, C.NODES_INLINE_SIZE,
              C.RELATIONS_INLINE_SIZE, C.WAYS_INLINE_SIZE]:
        cfg.set(C.DATASTORE, k, str(__INLINE_SIZE))

    for k in [C.CHANGESETS_PER_SLAB, C.NODES_PER_SLAB,
              C.RELATIONS_PER_SLAB, C.WAYS_PER_SLAB]:
        cfg.set(C.DATASTORE, k, str(__PER_SLAB))

    cfg.set(C.DATASTORE, C.DATASTORE_ENCODING, 'json')

    cfg.add_section(C.MEMBASE)
    cfg.set(C.MEMBASE, C.DBHOST, __DBHOST)
    cfg.set(C.MEMBASE, C.DBPORT, __DBPORT)
    cfg.set(C.DATASTORE, C.SLAB_LRU_SIZE, str(__SLAB_LRU_SIZE))
    cfg.set(C.DATASTORE, C.SLAB_LRU_THREADS, str(__SLAB_LRU_THREADS))

    slabutil_init(cfg)

    return Datastore(cfg)

def test_datastore_wrong_namespace(datastore):
    "Verify that an access to an unknown namespace is rejected."
    with pytest.raises(KeyError):
        v = datastore.fetch(__BADNAMESPACE, "0")

def test_datastore_direct_fetch(datastore):
    "Verify that directly fetchable elements can be read."
    _direct_key = 'Gs0000'
    _direct_val = O.new_osm_element(C.GEODOC, _direct_key[1:])
    insert_key(_direct_key, O.encode_json(_direct_val))

    v = datastore.fetch(C.GEODOC, _direct_key[1:])
    assert v == _direct_val

def test_datastore_failed_direct_fetch(datastore):
    "Verify that a non-existent element cannot be fetched."
    v = datastore.fetch(C.GEODOC, __NOSUCHKEY)
    assert v is None

def test_datastore_failed_slab_fetch(datastore):
    "Verify that a non-existent element in a slab cannot be fetched."
    v = datastore.fetch(C.NODE, __NOSUCHSLABELEMKEY)
    assert v is None

def test_datastore_slab_inline_fetch(datastore):
    "Verify that elements in a slab are fetched."
    _slab_key = 'NL8'
    _slab_start = __PER_SLAB
    # Create a slab.
    slab = []
    slabkeys = range(_slab_start, _slab_start + __PER_SLAB)
    for key in slabkeys:
        sk = str(key)
        if key % 2 == 0:
            n = O.new_osm_element(C.NODE, sk)
            slab.append((C.SLAB_INLINE, n))

    insert_key(_slab_key, datastore.encode(slab))

    c = 0
    i = 0
    for key in slabkeys:
        if key % 2 == 0:
            se,sn = slab[i]
            n = datastore.fetch(C.NODE, str(key))
            assert n == sn
            i += 1
        else:
            v = datastore.fetch(C.NODE, str(key))
            assert v is None
        c = c + 1

def test_datastore_write_element(datastore):
    "Test the store_element() entry point."

    _geodoc_key = 'Gs0000'
    _geodoc_val = O.new_osm_element(C.GEODOC, _geodoc_key[1:])

    datastore.store_element(C.GEODOC, _geodoc_key[1:], _geodoc_val)
    
    v = retrieve_key(_geodoc_key)
    assert v == O.encode_json(_geodoc_val)
