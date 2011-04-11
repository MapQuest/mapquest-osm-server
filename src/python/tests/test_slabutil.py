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
from datastore.slabutil import *
from ConfigParser import ConfigParser

INLINE_SIZE = 256
PER_SLAB = 1024
SLAB_LRU_SIZE = 8

def pytest_funcarg__config(request):
    "Prepare a configuration parser object"

    cfg = ConfigParser()
    cfg.add_section(C.DATASTORE)

    for k in [C.CHANGESETS_INLINE_SIZE, C.NODES_INLINE_SIZE,
              C.RELATIONS_INLINE_SIZE, C.WAYS_INLINE_SIZE]:
        cfg.set(C.DATASTORE, k, str(INLINE_SIZE))

    for k in [C.CHANGESETS_PER_SLAB, C.NODES_PER_SLAB,
              C.RELATIONS_PER_SLAB, C.WAYS_PER_SLAB]:
        cfg.set(C.DATASTORE, k, str(PER_SLAB))

    return cfg


def test_use_slab(config):
    "Check that the expected namespaces use slabs."

    slabutil_init(config)

    # The following three namespaces use slabs.
    for ns in [C.CHANGESET, C.NODE, C.RELATION, C.WAY]:
        assert slabutil_use_slab(ns) is True

    # The following namespaces do not use slabs currently.
    for ns in [C.GEODOC]:
        assert slabutil_use_slab(ns) is False

def test_get_config(config):
    "Check the return values from the 'slabutil_get_config()' method."
    slabutil_init(config)
    for ns in [C.CHANGESET, C.NODE, C.RELATION, C.WAY]:
        inline_size, per_slab = slabutil_get_config(ns)
        assert inline_size == INLINE_SIZE
        assert per_slab == PER_SLAB

def test_groupkeys(config):
    "Check the expected return values from the 'group_keys()' API."

    slabutil_init(config)

    expected_node_slabset = {
        "NL0": set(['0', '1', '511', '1023']),
        "NL1024": set(['1024', '1025', '2047']),
        "NL2048": set(['2048'])
        }

    expected_way_slabset = {
        "WL0": set(['0', '1', '511', '1023']),
        "WL1024": set(['1024', '1025', '2047']),
        "WL2048": set(['2048'])
        }

    expected_relation_slabset = {
        "RL0": set(['0', '1', '511', '1023']),
        "RL1024": set(['1024', '1025', '2047']),
        "RL2048": set(['2048'])
        }

    keys = map(str, [0, 1, 511, 1023, 1024, 1025, 2047, 2048])

    slabset = slabutil_group_keys(C.NODE, keys)
    assert slabset == expected_node_slabset

    slabset = slabutil_group_keys(C.WAY, keys)
    assert slabset == expected_way_slabset

    slabset = slabutil_group_keys(C.RELATION, keys)
    assert slabset == expected_relation_slabset

def test_groupkeys_nonnumeric(config):
    "Check the expected return values from the 'group_keys()' API."

    slabutil_init(config)

    expected_geodoc_slabset = {
        "GLtdr4t": set(["tdr4t"]),
        "GLs0000": set(["s0000"])
        }

    keys = ['tdr4t', 's0000']
    slabset = slabutil_group_keys(C.GEODOC, keys)
    assert slabset == expected_geodoc_slabset

def test_make_slabkey(config):
    "Test the make_slabkey() API."

    slabutil_init(config)

    expected = [
        (C.CHANGESET, '4567', 'CL4096'),
        (C.GEODOC, 'tdr4t', 'GLtdr4t'),
        (C.NODE, '1234', 'NL1024'),
        (C.RELATION, '16385', 'RL16384'),
        (C.WAY, '2345', 'WL2048'),
        ]

    for (ns, key, slabkey) in expected:
        v = slabutil_make_slabkey(ns, key)
        assert v == slabkey
