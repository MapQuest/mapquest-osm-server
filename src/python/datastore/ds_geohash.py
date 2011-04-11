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

"""Convenience routines for managing geo-hashes."""

import geohash

import apiserver.const as C

__GHKEYLENGTH = None
__SCALEFACTOR = None

def init_geohash(ghkeylength, scalefactor):
    "Initialize the module."
    global __GHKEYLENGTH, __SCALEFACTOR

    __GHKEYLENGTH = ghkeylength
    __SCALEFACTOR = scalefactor

def geohash_key_for_element(elem):
    "Return a geohash key for element 'elem'."

    lat = min(C.MAXGHLAT, float(elem.get(C.LAT)) / __SCALEFACTOR)
    lon = float(elem.get(C.LON)) / __SCALEFACTOR

    return geohash.encode(lat, lon, precision=__GHKEYLENGTH)
