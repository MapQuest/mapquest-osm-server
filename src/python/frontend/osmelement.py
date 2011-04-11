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

## Handle API requests for nodes, ways and elements.

import tornado.web

import apiserver.const as C
from apiserver.osmelement import new_osm_response
from util import filter_references, response_to_xml

class OsmElementHandler(tornado.web.RequestHandler):
    "Handle requests for the (changeset|node|way|relation)/ API."

    def initialize(self, datastore):
        self.datastore = datastore

    def delete(self, element):
        """Handle a DELETE HTTP request."""

        raise tornado.web.HTTPError(501) # Not Implemented.

    def get(self, namespace, ident):
        self.set_header(C.CONTENT_TYPE, C.TEXT_XML)

        elem = self.datastore.fetch(namespace, ident)
        if elem is None:
            raise tornado.web.HTTPError(404)

        self.write(response_to_xml(elem.build_response(new_osm_response())))

    def put(self, element):
        """Handle a PUT HTTP request."""

        raise tornado.web.HTTPError(501) # Not Implemented.

class OsmMultiElementHandler(tornado.web.RequestHandler):
    """Handle requests for the (nodes|ways|relations) API."""

    def initialize(self, datastore):
        """Initialize the handler."""
        self.datastore = datastore

    def get(self, element):
        """Retrieve multiple elements.

        The elements are specified by (nodes|ways|relations) parameter
        to the request, as a comma separated list of element IDs.
        """

        if element not in [C.NODES, C.WAYS, C.RELATIONS]:
            # Programming error.
            raise tornado.web.HTTPError(500)

        # Determine the name space to use.
        if element == C.NODES:
            namespace = C.NODE
        elif element == C.WAYS:
            namespace = C.WAY
        elif element == C.RELATIONS:
            namespace = C.RELATION
        else:
            assert False, "Unexpected element '%s'" % element

        # The name of the parameter (i.e., one of "nodes", "ways" or
        # "relations") match the last component of the URI.
        params = self.get_argument(element, None)
        if not params:
            raise tornado.web.HTTPError(400)

        # Create a new response.
        osm = new_osm_response()

        # Add elements to the response.
        for (st,r) in self.datastore.fetch_keys(namespace, params.split(",")):
            if st:
                r.build_response(osm)

        # Send the XML representation back to the client.
        self.set_header(C.CONTENT_TYPE, C.TEXT_XML)
        self.write(response_to_xml(osm))


class OsmElementRelationsHandler(tornado.web.RequestHandler):
    """Retrieve relations for a node or way element."""

    def initialize(self, datastore):
        """Initialize the handler."""
        self.datastore = datastore

    def get(self, namespace, ident):
        """Retrieve relations for an element.

        The element can be a 'node' or 'way'.
        """

        if namespace not in [C.NODE, C.WAY, C.RELATION]:
            raise tornado.web.HTTPError(500)

        elem = self.datastore.fetch(namespace, ident)

        osm = new_osm_response()

        if elem:
            relset = filter_references(C.RELATION, [elem])
            if len(relset) > 0:
                relations = self.datastore.fetch_keys(C.RELATION,
                                                      [r for r in relset])
                for (st,r) in relations:
                    if st:
                        r.build_response(osm)

        self.set_header(C.CONTENT_TYPE, C.TEXT_XML)
        self.write(response_to_xml(osm))

class OsmWaysForNodeHandler(tornado.web.RequestHandler):
    """Retrieve ways associated with a node."""

    def initialize(self, datastore):
        self.datastore = datastore

    def get(self, nodeid):
        "Retrieve the ways associated with a node."

        elem = self.datastore.fetch(C.NODE, nodeid)
        if elem is None:
            raise tornado.web.HTTPError(404)

        osm = new_osm_response()

        wayset = filter_references(C.WAY, [elem])
        if len(wayset) > 0:
            ways = self.datastore.fetch_keys(C.WAY,
                                             [w for w in wayset])
            for (st,w) in ways:
                if st:
                    w.build_response(osm)

        self.set_header(C.CONTENT_TYPE, C.TEXT_XML)
        self.write(response_to_xml(osm))

class OsmFullQueryHandler(tornado.web.RequestHandler):
    """Handle a `full' query for a way or relation."""

    def initialize(self, datastore):
        self.datastore = datastore

    def get(self, namespace, elemid):
        """Implement a 'GET' operation.

        For a way:
        - Return the way itself,
        - Return the full XML of all nodes referenced by the
          way.
        For a relation:
        - Return the relation itself,
        - All nodes and ways that are members of the relation.
        - All nodes referenced from the ways above.
        """

        # Retrieve the element.
        element = self.datastore.fetch(namespace, elemid)
        if element is None:
            raise tornado.web.HTTPError(404)

        nodes = []
        ways = []
        relations = []

        if namespace == C.RELATION:
            # Retrieve nodes directly referenced by the relation.
            nodeset = element.get_member_ids(C.NODE)
            nodes.extend([z for (st,z) in
                          self.datastore.fetch_keys(C.NODE, [n for n in nodeset])
                          if st])
            # Retrieve way IDs directly referenced by the relation.
            wayset = element.get_member_ids(C.WAY)
            # Include the relation itself.
            relations.append(element)
        else:
            nodeset = set()
            wayset = set([elemid])

        # Fetch all ways.
        if len(wayset) > 0:
            ways.extend([z for (st, z) in
                         self.datastore.fetch_keys(C.WAY, [w for w in wayset])
                         if st])

        # Fetch additional nodes referenced by the ways in the
        # way set.
        additional_nodes = set()
        for w in ways:
            additional_nodes.update(w.get_node_ids())

        additional_nodes = additional_nodes - nodeset
        nodes.extend([z for (st, z) in
                      self.datastore.fetch_keys(C.NODE, [n for n in additional_nodes])
                      if st])

        # Build and return a response.
        osm = new_osm_response()
        for n in nodes:
            n.build_response(osm)
        for w in ways:
            w.build_response(osm)
        for r in relations:
            r.build_response(osm)

        self.set_header(C.CONTENT_TYPE, C.TEXT_XML)
        self.write(response_to_xml(osm))
