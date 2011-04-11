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

"""Turn input sources into iterables.

Exported functions:

makesource -- Turn a file into an iterable that returns OSM elements.
"""

import gzip
import os

from lxml.etree import iterparse

from apiserver.osmelement import encode_coordinate, new_osm_element
import apiserver.const as C

def _make_osm_iterator(config, f):
    "Return an iterator parsing the <osm> format"

    scalefactor = config.getint(C.DATASTORE, C.SCALE_FACTOR)

    parser = iter(iterparse(f, events=('start', 'end')))
    event, root = parser.next()
    if root.tag != u'osm':
        raise ValueError, "Unexpected root tag: %s" % root.tag

    depth = 0
    doc = None
    ignored_elements = ['bound', 'bounds']
    processed_elements = ('changeset', 'node', 'way', 'relation')

    # Parse the input file.
    for event, elem in parser:

        element_name = elem.tag
        if element_name in ignored_elements:
            continue

        if event == 'start':
            if element_name in processed_elements:
                assert depth == 0

                # Start of the element.  Copy 'standard' attributes,
                # translating them to native values where possible.
                doc = new_osm_element(element_name.lower(), elem.get('id'))
                for k,v in elem.items():
                    if k == 'visible':
                        v = bool(v)
                    elif k == 'version' or k == 'uid':
                        v = int(v)
                    elif k == 'lat' or k == 'lon':
                        v = encode_coordinate(v)
                    doc[k] = v

            elif element_name == 'tag':
                # Each 'tag' has a key/value associated with it.
                doc.setdefault('tags', {})[elem.get('k')] = elem.get('v')

            elif element_name == 'nd':
                # <nd> elements contain references.
                doc['nodes'].add(int(elem.get('ref')))

            elif element_name == 'member':
                # Collect the list of (ref, role, type) tuples.
                doc.setdefault('members', []).append((elem.get('ref'),
                                                      elem.get('role'),
                                                      elem.get('type')))
            depth = depth + 1

        elif event == 'end':
            depth = depth - 1
            if depth == 0:
                yield doc       # Return a complete element to the caller.

        root.clear()            # Keep memory usage down.


def makesource(config, options, fn):
    """Return an iterator returning elements contained in 'fn'."""

    # Determine the uncompression technique needed.
    basefn, ext = os.path.splitext(fn)

    if ext in [".bz2", ".gz"]:
        if ext == ".bz2":
            f = os.popen("bzcat %s" % fn, 'r')
        elif ext == ".gz":
            f = gzip.GzipFile(fn, mode='r')
        (basefn, _) = os.path.splitext(fn)
    else:
        basefn = fn
        f = open(fn, mode='r')

    # Determine the file format.
    if basefn.endswith(".osc"):
        raise NotImplementedError, "OsmChange input"
    if basefn.endswith(".pbf"):
        raise NotImplementedError, "PBF input"
    if basefn.endswith(".xml") or basefn.endswith(".osm"):
        return _make_osm_iterator(config, f)
