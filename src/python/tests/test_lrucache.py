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

import pytest
from ConfigParser import ConfigParser

import apiserver.const as C
from datastore.lrucache import LRUCache
from datastore.slabutil import slabutil_make_slab, slabutil_init

_INLINE_SIZE = 256
_LRUSZ = 8
_SLABSZ = 16
_NOSUCHKEY = '__nosuchkey__'
_KEY = '_key'
_NS = 'node'
_NS1 = 'way'

def pytest_funcarg__lrucache(request):
    "Prepare a pre-initialized cache object."
    return LRUCache(_LRUSZ)

def pytest_funcarg__slabutil(request):
    cfg = ConfigParser()
    cfg.add_section(C.DATASTORE)

    for k in [C.CHANGESETS_INLINE_SIZE, C.NODES_INLINE_SIZE,
              C.RELATIONS_INLINE_SIZE, C.WAYS_INLINE_SIZE]:
        cfg.set(C.DATASTORE, k, str(_INLINE_SIZE))

    for k in [C.CHANGESETS_PER_SLAB, C.NODES_PER_SLAB,
              C.RELATIONS_PER_SLAB, C.WAYS_PER_SLAB]:
        cfg.set(C.DATASTORE, k, str(_SLABSZ))

    slabutil_init(cfg)
    return cfg

def test_empty(slabutil):
    "Test the properties of an empty cache object."

    lc = LRUCache(_LRUSZ)
    assert len(lc) == 0
    assert lc.get(_NS, _KEY) is None


def test_get(lrucache, slabutil):
    "Test insert and retrieval of one slab descriptor."

    values = range(_SLABSZ)
    keys = map(str, values)
    slabitems = zip(keys, values)

    slabdesc = slabutil_make_slab(_NS, slabitems)
    lrucache.insert_slab(slabdesc)

    for i in xrange(_SLABSZ):
        st, v = lrucache.get(_NS, str(i))
        assert st
        assert v == values[i]


def test_duplicate_slabdesc(lrucache, slabutil):
    "Test insertion of a duplicate slab descriptor."

    values = range(_SLABSZ)
    keys = map(str, values)
    slabitems = zip(keys, values)
    slabdesc = slabutil_make_slab(_NS, slabitems)

    lrucache.insert_slab(slabdesc)
    with pytest.raises(ValueError):
        lrucache.insert_slab(slabdesc)


def test_duplicate_values(lrucache, slabutil):
    "Test insertion of duplicate values in a namespace."

    values = range(_SLABSZ)
    keys = map(str, values)
    slabitems = zip(keys, values)
    slabdesc = slabutil_make_slab(_NS, slabitems)
    lrucache.insert_slab(slabdesc)

    slabdesc2 = slabutil_make_slab(_NS, slabitems)
    with pytest.raises(ValueError):
        lrucache.insert_slab(slabdesc2)

def test_namespaces(lrucache, slabutil):
    "Test that different namespaces are distinct."
    values = range(_SLABSZ)
    slabdesc1 = slabutil_make_slab(_NS, zip(map(str, values), values))
    lrucache.insert_slab(slabdesc1)

    slabdesc2 = slabutil_make_slab(_NS1, zip(map(str, values),
                                             map(lambda x: x*x, values)))
    lrucache.insert_slab(slabdesc2)

    for i in xrange(_SLABSZ):
        st, v1 = lrucache.get(_NS, str(i))
        assert st
        assert v1 == i
        st, v2 = lrucache.get(_NS1, str(i))
        assert st
        assert v2 == i*i


def test_get_nonexistent(lrucache, slabutil):
    "Test that unknown keys are rejected."
    values = range(_SLABSZ)
    keys = map(str, values)
    slabitems = zip(keys, values)
    slabdesc = slabutil_make_slab(_NS, slabitems)
    lrucache.insert_slab(slabdesc)

    assert lrucache.get(_NS+_NS, '0') is None # Invalid namespace, valid key
    # Valid namespace, out-of-slab key
    assert lrucache.get(_NS, _SLABSZ+1) is None


def test_get_nonexistent_element(lrucache, slabutil):
    "Test that a missing keys is shown as not-present."
    values = range(0, _SLABSZ, 2) # Alternate elements.
    keys = map(str, values)
    slabitems = zip(keys, values)
    slabdesc = slabutil_make_slab(_NS, slabitems)
    lrucache.insert_slab(slabdesc)

    st, v = lrucache.get(_NS, '1') # Valid namespace, missing key
    assert not st
    assert v == '1'

def test_remove(lrucache, slabutil):
    "Test the remove_slab() method."

    values1 = range(_SLABSZ)
    slabdesc1 = slabutil_make_slab(_NS,  zip(map(str, values1), values1))
    lrucache.insert_slab(slabdesc1)

    values2 = range(_SLABSZ, 2*_SLABSZ)
    slabdesc2 = slabutil_make_slab(_NS,  zip(map(str, values2), values2))
    lrucache.insert_slab(slabdesc2)

    # Remove the first slab.
    lrucache.remove_slab(slabdesc1)

    # Items in the original slab should be missing.
    for i in xrange(_SLABSZ):
        st = lrucache.get(_NS, str(i))
        assert st is None

    # Items in the second slab should be present.
    for i in xrange(_SLABSZ, 2 * _SLABSZ):
        st, v = lrucache.get(_NS, str(i))
        assert st
        assert v == i


def test_non_overflow(slabutil):
    "Test that slabs do not overflow upto the slab LRU size."
    slabs = []
    def _mkslab(i):
        v = [i * _SLABSZ]
        return slabutil_make_slab(_NS, zip(map(str, v), v))

    def _cb(self, key, slabdesc, seq=[0]):
        assert False

    lc = LRUCache(_LRUSZ, _cb)
    for i in xrange(_LRUSZ):
        sl = _mkslab(i)
        slabs.append(sl)
        lc.insert_slab(sl)


def test_overflow(slabutil):
    "Test that slabs overflow in LRU sequence."

    slabs = []
    def _mkslab(i):
        v = [i * _SLABSZ]
        return slabutil_make_slab(_NS, zip(map(str, v), v))

    def _cb(slabkey, slabdesc, seq=[0]):
        n = seq[0]
        assert slabdesc is slabs[n]
        seq[0] = n + 1

    lc = LRUCache(_LRUSZ, _cb)
    for i in xrange(2*_LRUSZ):
        sl = _mkslab(i)
        slabs.append(sl)
        lc.insert_slab(sl)


def test_flush(slabutil):
    "Test that flush presents slabs in sequence."

    slabs = []
    def _mkslab(i):
        v = [i * _SLABSZ]
        return slabutil_make_slab(_NS, zip(map(str, v), v))

    seen = [False]
    def _cb(slabkey, slabdesc, seq=[0], seen=seen):
        seen[0] = True
        n = seq[0]
        assert slabdesc is slabs[n]
        seq[0] = n + 1

    lc = LRUCache(_LRUSZ, _cb)
    for i in xrange(_LRUSZ):
        sl = _mkslab(i)
        slabs.append(sl)
        lc.insert_slab(sl)


    lc.flush()
    assert seen[0] is True
