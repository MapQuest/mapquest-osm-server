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

"""Test the 'datastore.geohash' utility module."""

import pytest

import apiserver.const as C
from apiserver.osmelement import new_osm_element
from datastore.ds_geohash import init_geohash, geohash_key_for_element

_GHKEYLENGTH = 5
_SCALEFACTOR = 10000000

def test_geokeys():
    "Test geo hash keys returned for various coordinates."

    init_geohash(_GHKEYLENGTH, _SCALEFACTOR)
    expected = [
        (0.0, 0.0, 's0000'),
        (89, 0.0, 'upb42'),
        (89.999999999999992, 0.0, 'upbpb'), # Max lat supported.
        (-90, 0.0, 'h0000'),
        (-90, -180, '00000'),
        (-90, +180, '00000'),
        (-90, +90, 'n0000'),
        (-90, -90, '40000'),
        (-45, -45, '70000'),
        (-45, 45, 'm0000'),
        (45, 45, 'v0000'),
        (45, -45, 'g0000')
        ]
        
    for (lat, lon, ghkey) in expected:
        elem = new_osm_element(C.NODE, '0')
        elem[C.LAT] = lat * _SCALEFACTOR
        elem[C.LON] = lon * _SCALEFACTOR
        res = geohash_key_for_element(elem)

        assert res == ghkey
