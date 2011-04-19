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

## Support retrieval of the map data in a bounding box.

import geohash
import tornado.web

from lxml import etree as ET

import apiserver.const as C
from apiserver.osmelement import encode_coordinate, new_osm_response

from util import filter_references, response_to_xml

def _filter_in_bbox(bbox, geodocs):
    "Return the list of nodes that fall into the given bounding box."
    w,s,e,n = map(encode_coordinate, bbox)

    nodeset = set()
    for gd in geodocs:
        for (nid, lat, lon) in gd.get_node_info():
            if w <= lon < e and s <= lat < n:
                nodeset.add(nid)
    return nodeset


class MapHandler(tornado.web.RequestHandler):
    "Handle requests for the /map API."

    def initialize(self, cfg, datastore):
        self.datastore = datastore
        self.precision = cfg.getint(C.DATASTORE, C.GEOHASH_LENGTH)

    def get(self, *args, **kwargs):
        '''Service a GET request to the '/map' URI.

        The 'bbox' parameter contains 4 coordinates "l" (w), "b" (s),
        "r" (e) and "t" (n).'''
        
        # Sanity check the input.
        bbox_arg = self.get_argument('bbox', None)
        if not bbox_arg:
            raise tornado.web.HTTPError(400)  # Bad Syntax
        bbox = bbox_arg.split(',')
        if len(bbox) != 4:
            raise tornado.web.HTTPError(400)
        try:
            w,s,e,n = map(float, bbox)
        except ValueError:
            raise tornado.web.HTTPError(400)

        # Check the "l,b,r,t" coordinates passed in for sanity.
        if w < C.LON_MIN or w > C.LON_MAX or \
           e < C.LON_MIN or e > C.LON_MAX or \
           s < C.LAT_MIN or s > C.LAT_MAX or \
           n < C.LAT_MIN or n > C.LAT_MAX or \
           n < s or e < w:
            raise tornado.web.HTTPError(400)

        nodelist, ways, relations = self.handle_map(bbox)
        response = self.build_bbox_response(nodelist, ways, relations, bbox)

        self.set_header(C.CONTENT_TYPE, C.TEXT_XML)
        self.write(response_to_xml(response))

    def build_bbox_response(self, nodes, ways, relations, bbox):
        """Build an OSM response for the query."""

        # Create a new response element.
        osm = new_osm_response()

        # Add a <bounds> element.
        bb = ET.SubElement(osm, C.BOUNDS)
        (bb.attrib[C.MINLON], bb.attrib[C.MINLAT],
         bb.attrib[C.MAXLON], bb.attrib[C.MAXLAT]) = map(str, bbox)

        # Add nodes, ways and relations in that order.
        for n in nodes:
            n.build_response(osm)
        for w in ways:
            w.build_response(osm)
        for r in relations:
            r.build_response(osm)

        return osm

    def handle_map(self, bbox):
        """Implementation of the /map API.

        Parameters:

        bbox -- Bounding box coordinates.
        """

        nodelist = []
        relations = []
        ways = []

        # This implementation follows the current implementation of
        # the API server at api.openstreetmap.org (the 'rails' port).

        # Look up the geo coded documents covering the desired bbox.
        gckeys = self.get_geocodes(bbox)
        geodocs = self.datastore.fetch_keys(C.GEODOC, gckeys)

        # Step 1: Get the list of nodes contained in the given
        #    bounding box.
        nodeset = _filter_in_bbox(bbox,
                                  [gd for (st, gd) in geodocs if st])
        if len(nodeset) == 0:
            return (nodelist, ways, relations)

        nodelist = [z for (st, z) in self.datastore.fetch_keys(
                C.NODE, [n for n in nodeset]) if st]

        # Step 2: Retrieve all ways that reference at least one node
        #    in the given bounding box.
        wayset = filter_references(C.WAY, nodelist)


        # Step 3: Retrieve any additional nodes referenced by the ways
        # retrieved.
        waynodeset = set()

        for (st,w) in self.datastore.fetch_keys(C.WAY, [w for w in wayset]):
            if st:
                ways.append(w)
                waynodeset.update(w.get_node_ids())

        extranodeset = waynodeset - nodeset
        nodelist.extend([n for (st,n) in
                         self.datastore.fetch_keys(C.NODE,
                                                   [n for n in extranodeset])
                         if st])
        nodeset = nodeset | extranodeset

        # Step 4: Retrieve the relations associated with these nodes.

        # ... all relations that reference nodes being returned.
        relset = filter_references(C.RELATION, nodelist)

        # ... and relations that reference one of the ways in the wayset.
        relset.update(filter_references(C.RELATION, ways))

        # ... retrieve relations from the data store.
        relations = [xr for (st,xr) in
                     self.datastore.fetch_keys(C.RELATION,
                                               [r for r in relset])
                     if st]

        # ... and relations referenced by existing relations
        # (one-pass only).
        extrarelset = filter_references(C.RELATION, relations)
        newrelset = extrarelset - relset

        newrels = [nr for (st, nr) in
                   self.datastore.fetch_keys(C.RELATION,
                                             [r for r in newrelset])
                   if st]
        relations.extend(newrels)

        return (nodelist, ways, relations)


    def get_geocodes(self, bbox):
        """Return a list of keys covering a given area.

        Parameters:

        bbox -- Bounding box of the desired region.
        """

        # TODO: Make this more efficient for sparse areas of the map.
        w, s, e, n = map(float, bbox)

        n = min(C.MAXGHLAT, n)  # work around a geohash library
        s = min(C.MAXGHLAT, s)  # limitation

        assert(w <= e and s <= n)

        gcset = set()
        gc = geohash.encode(s, w, self.precision)

        bl = geohash.bbox(gc)   # Box containing point (s,w).

        s_ = bl['s'];
        while s_ < n:           # Step south to north.
            w_ = bl['w']

            gc = geohash.encode(s_, w_, self.precision)
            bb_sn = geohash.bbox(gc) # bounding box in S->N direction

            while w_ < e:       # Step west to east.
                gcset.add(gc)

                bb_we = geohash.bbox(gc) # in W->E direction
                w_ = bb_we['e']

                gc = geohash.encode(s_, w_, self.precision)

            s_ = bb_sn['n']

        assert(len(gcset) > 0)

        return [gc for gc in gcset]
