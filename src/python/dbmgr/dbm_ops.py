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

"""Operations on an OSM database."""

import apiserver.const as C

from apiserver.osmelement import new_osm_element
from dbmgr.dbm_stats import increment_stats
from dbmgr.dbm_geotables import GeoGroupTable

def make_backreference(namespace, elemid):
    """Create a backreference string.

    namespace -- The OSM namespace for the element.
    elemid    -- Element ID in the namespace.
    """

    return namespace[0].upper() + elemid

class DBOps:
    """This class implements the semantics of adding OSM elements and
    changesets to the backend."""

    def __init__(self, config, options, db):
        "Initialize an operations structure."
        self.db = db
        self.verbose = options.verbose
        self.geotable = GeoGroupTable(config, options, db)

    def add_element(self, elem):
        "Add an element to the datastore."

        self.db.store(elem)

        # If the element is a node, add it to the appropriate geodoc.
        ns = elem.namespace
        backreference = make_backreference(ns, elem.id)

        if self.verbose:
            increment_stats(ns)

        # Do element-specific processing.
        if ns == C.NODE:
            # Add the element to the appropriate geodoc.
            self.geotable.add(elem)

        elif ns == C.WAY:
            # Backlink referenced nodes to the current way.
            for (rstatus, node_or_key) in \
                    self.db.fetch_keys(C.NODE, map(str, elem[C.NODES])):
                if rstatus:
                    node = node_or_key
                else:
                    node = new_osm_element(C.NODE, node_or_key)
                node[C.REFERENCES].add(backreference)
                self.db.store(node)

        elif ns == C.RELATION:
            # If the element is a relation, backlink referenced ways &
            # relations.

            def _retrieve(selector, members):
                return [str(mref) for (mref, mrole, mtype) in members
                        if mtype == selector]

            members = elem[C.MEMBERS]

            elements = []
            for ns in [C.NODE, C.WAY, C.RELATIONS]:
                elements.append((ns, _retrieve(ns, members)))

            for (ns, refs) in elements:
                if len(refs) == 0:
                    continue
                for (rstatus, node_or_key) in self.db.fetch_keys(ns, refs):
                    # Retrieve all elements referenced by the relation.
                    if rstatus:
                        elem = node_or_key
                    else:
                        elem = new_osm_element(ns, node_or_key)

                    # Add a backreference to the element being
                    # referenced by this relation.
                    elem[C.REFERENCES].add(backreference)
                    self.db.store(elem)

    def add_changeset(self, changeset):
        "Add a changeset to the database."
        raise NotImplementedError

    def finish(self):
        """Signal the end of DB operations."""

        # Push out all pending geodoc changes.
        self.geotable.flush()

        # Request the underlying database to wind up operation.
        self.db.finalize()
