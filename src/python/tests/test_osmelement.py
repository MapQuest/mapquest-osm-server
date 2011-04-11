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

import math

from ConfigParser import ConfigParser

import apiserver.const as C
import apiserver.osmelement as O

from datastore.slabutil import slabutil_init

def pytest_funcarg__config(request):
    "Prepare a configuration parser object."

    cfg = ConfigParser()

    cfg.add_section(C.DATASTORE)
    cfg.set(C.DATASTORE, C.SCALE_FACTOR, '10000000')
    cfg.set(C.DATASTORE, C.CHANGESETS_INLINE_SIZE, '1024')
    cfg.set(C.DATASTORE, C.CHANGESETS_PER_SLAB, '8')
    cfg.set(C.DATASTORE, C.NODES_INLINE_SIZE, '1024')
    cfg.set(C.DATASTORE, C.NODES_PER_SLAB, '8')
    cfg.set(C.DATASTORE, C.RELATIONS_INLINE_SIZE, '1024')
    cfg.set(C.DATASTORE, C.RELATIONS_PER_SLAB, '8')
    cfg.set(C.DATASTORE, C.WAYS_INLINE_SIZE, '1024')
    cfg.set(C.DATASTORE, C.WAYS_PER_SLAB, '8')

    cfg.add_section(C.FRONT_END)
    cfg.set(C.FRONT_END, C.SERVER_VERSION, '0.6')
    cfg.set(C.FRONT_END, C.SERVER_NAME, 'Test')

    slabutil_init(cfg)

    return cfg


def test_new_node(config):
    "Test the creation a <node> element."

    O.init_osm_factory(config)

    nodeid = '42'
    n = O.new_osm_element(C.NODE, nodeid)

    # Check the 'id' field.
    assert n.id == str(nodeid)
    # Check that C.REFERENCES field exists, and is an empty set.
    assert n[C.REFERENCES] == set()


def test_new_way(config):
    "Test creation of a <way> element."
    
    O.init_osm_factory(config)
    wayid = '42'
    w = O.new_osm_element(C.WAY, wayid)

    # Check the "id", NODES and REFERENCES attributes.
    assert w.id == str(wayid)
    assert w[C.REFERENCES] == set()
    assert w[C.NODES] == set()


def test_new_relation(config):
    "Test creation of a <relation> element."

    O.init_osm_factory(config)
    relid = '42'
    r = O.new_osm_element(C.RELATION, relid)
    
    # Check the "id", MEMBER and REFERENCES attributes. 
    assert r.id == str(relid)
    assert r[C.REFERENCES] == set()
    assert r[C.MEMBERS] == []


def test_new_geodoc(config):
    "Test the creation of a geodoc element."

    O.init_osm_factory(config)
    georegion = 'szmyg'         # lat, long == 42, 42
    g = O.new_osm_element(C.GEODOC, georegion)

    # Check the "id" field.

    assert g.id == georegion
    assert g[C.NODES] == set()

    bbox = g[C.BBOX]
    assert set(bbox.keys()) == set(['n', 's', 'e', 'w'])


def test_encode_coordinate(config):
    "Test encoding of a coordinate string."

    O.init_osm_factory(config)

    # The following tests assume that the scale factor in use is 10^7.
    _sf = config.getint(C.DATASTORE, C.SCALE_FACTOR)
    assert _sf == 10000000

    #
    # Test encoding of strings.
    #
    inputlist = [ ('0', 0),                  # Zero.
                  ('0.00123456',      12345), # Tiny
                  ('0.12345678',    1234567), # Fraction only
                  ('1.23456789',   12345678), # Normal, small
                  ('12.3456789',  123456789), # Normal
                  ('123.456789', 1234567890), # Normal, large
                  ('1',            10000000), # Integral, small
                  ('12',          120000000), # Integral
                  ('123',        1230000000)  # Integral, large
                ]
    for (strval, refval) in inputlist:
        v = O.encode_coordinate(strval)
        assert refval == v


    #
    # Test encoding of floating point values.
    #
    inputlist = [ (0.0, 0),
                  (0.123456,    1234560),
                  (0.1234567,   1234567),
                  (1.0,        10000000),
                  (1.23456,    12345600),
                 (12.3455899, 123455899)
                ]
    for (flval, refval) in inputlist:
        v = O.encode_coordinate(flval)
        assert v == refval
