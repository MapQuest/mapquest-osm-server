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

"""Describe OSM elements.

Exported functions:

    new_osm_element -- factory function to create a new OSM element.
    init_osm_factory -- initialize the factory.
"""

import geohash
import math
import types

import cjson

from lxml import etree as ET

import apiserver.const as C
from datastore.slabutil import slabutil_make_slabkey

_server_version = None
_server_name = None
_scale_factor = None
_fraction_width = None
_coordinate_format = None

def init_osm_factory(config):
    """Initialize the factory for OSM elements."""

    global _coordinate_format, _fraction_width, _scale_factor, _server_name
    global _server_version

    _scale_factor = config.getint(C.DATASTORE, C.SCALE_FACTOR)
    _fraction_width = math.trunc(math.log10(_scale_factor))
    _coordinate_format = "%%d.%%0%dd" % _fraction_width

    _server_version = config.get(C.FRONT_END, C.SERVER_VERSION)
    _server_name = config.get(C.FRONT_END, C.SERVER_NAME)

def encode_coordinate(coordinate):
    """Encode a latitude or longitude as an integral value.

    Parameters:

    coordinate -- An OSM latitude or longitude as numeric value, or
                  a string representation of a number.
    """

    coordinate_type = type(coordinate)

    if coordinate_type in types.StringTypes:
        try:
            integral, fractional = coordinate.split(".")
            fractional = fractional[0:_fraction_width]
        except ValueError:
            integral = coordinate
            fractional = "0"

        fractional = fractional.ljust(_fraction_width, "0")
        return int(integral) * _scale_factor + int(fractional)

    elif coordinate_type == types.FloatType:
        fractional, integral = map(lambda x: int(x * _scale_factor),
                                   math.modf(coordinate))
        return integral + fractional

    else:
        raise ValueError, \
            "Unsupported conversion from '%s'" % coordinate_type

def decode_coordinate(encodedvalue):
    """Decode an integral quantity into a OSM latitude or longitude."""

    integral = encodedvalue / _scale_factor
    fractional = encodedvalue - (integral * _scale_factor)

    return _coordinate_format % (integral, fractional)

def new_osm_response():
    "Create an (empty) <osm> XML element."

    osm = ET.Element(C.OSM)
    osm.attrib[C.VERSION] = _server_version
    osm.attrib[C.GENERATOR] = _server_name

    return osm


class OSMElement(dict):
    """A representation of an OSM Element"""

    ignoredkeys = [C.TAGS, C.REFERENCES]

    def __init__(self, namespace, elemid):
        """Initialize an OSMElement object.

        namespace -- the OSM namespace for the element.
        elemid    -- the element id in the namespace.
        """

        assert namespace in _namespace_to_factory.keys()
        assert isinstance(elemid, basestring)

        super(OSMElement, self).__init__()
        super(OSMElement, self).__setitem__(C.ID, elemid)
        super(OSMElement, self).__setitem__(C.REFERENCES, set())
        self.namespace = namespace
        self.id = elemid
        self.slabkey = slabutil_make_slabkey(namespace, elemid)

    def __repr__(self):
        'Return a human-friendly representation of an OSMElement.'
        docstr = super(OSMElement, self).__repr__()
        return "OSMElement<%s>%s" % (self.namespace, docstr)

    def from_mapping(self, d):
        "Translate between a mapping to an OSM element."
        setter = super(OSMElement, self).__setitem__
        for k in d:
            if k == C.ID:
                assert self.id == str(d[k])
                continue
            if k == C.REFERENCES:
                v = set(d[k])
            else:
                v = d[k]
            setter(k, v)

    def as_mapping(self):
        "Translate to a Python mapping."
        d = {}
        for (k,v) in self.items():
            if isinstance(v, set): # Convert sets to lists.
                v = [r for r in v]
            d[k] = v
        return d
                
    def build_response(self, element):
        "Return an XML representation of an element."
        raise TypeError, "Abstract method was invoked."

    def add_attributes(self, element, ignoredkeys=[]):
        "Translate from dictionary keys to XML attributes."
        for (k, v) in self.items():
            if k in ignoredkeys:
                continue
            if k in OSMElement.ignoredkeys:
                continue
            element.attrib[k] = str(v)

    def add_tags(self, element):
        "Add <tag> children to an XML element."
        for (k, v) in self.get(C.TAGS, {}).items():
            t = ET.SubElement(element, C.TAG)
            t.attrib[C.K] = k
            t.attrib[C.V] = v

class OSMChangeSet(OSMElement):
    def __init__(self, elemid):
        super(OSMChangeSet, self).__init__(C.CHANGESET, elemid)

    def build_response(self, osm):
        """Return the XML representation for a <changeset>."""

        changeset = ET.SubElement(osm, C.CHANGESET)
        self.add_attributes(changeset)
        self.add_tags(changeset)

        return osm

class OSMDatastoreConfig(OSMElement):
    def __init__(self, elemid):
        OSMElement.__init__(self, C.DATASTORE_CONFIG, elemid)

class OSMGeoDoc(OSMElement):
    """A geodoc references nodes which fall into a given geographic area."""
    def __init__(self, region):
        super(OSMGeoDoc, self).__init__(C.GEODOC, region)
        # Fill in default values for 'standard' fields.
        self.__setitem__(C.NODES, set())
        self.__setitem__(C.BBOX, geohash.bbox(region))

    def build_response(self, element):
        raise TypeError, "GeoDocuments have no XML representation."

    def get_node_info(self):
        "Return node ids and (lat, lon) coordinates in this document."
        return self[C.NODES]

class OSMNode(OSMElement):

    special_attributes = [C.LAT, C.LON]

    def __init__(self, elemid):
        super(OSMNode, self).__init__(C.NODE, elemid)

    def build_response(self, osm):
        "Return an XML representation for a <node>."

        node = ET.SubElement(osm, C.NODE)

        self.add_attributes(node, ignoredkeys=OSMNode.special_attributes)

        for k in OSMNode.special_attributes:
            node.attrib[k] = decode_coordinate(self.get(k))

        self.add_tags(node)

        return osm

class OSMWay(OSMElement):
    def __init__(self, elemid):
        super(OSMWay, self).__init__(C.WAY, elemid)
        super(OSMWay, self).__setitem__(C.NODES, set())

    def build_response(self, osm):
        "Incorporate an XML representation for a <way>."

        way = ET.SubElement(osm, C.WAY)

        self.add_attributes(way, ignoredkeys=[C.NODES])

        nodes = self.get(C.NODES, [])
        for n in nodes:
            node = ET.SubElement(way, C.ND)
            node.attrib[C.REF] = str(n)

        self.add_tags(way)

        return osm

    def get_node_ids(self):
        "Return ids for the nodes associated with a way."
        return [str(n) for n in self[C.NODES]]

class OSMRelation(OSMElement):
    def __init__(self, elemid):
        super(OSMRelation, self).__init__(C.RELATION, elemid)
        super(OSMRelation, self).__setitem__(C.MEMBERS, [])

    def build_response(self, osm):
        "Incorporate an XML representation for a <relation>."

        rel = ET.SubElement(osm, C.RELATION)

        self.add_attributes(rel, ignoredkeys=[C.MEMBERS])

        members = self.get(C.MEMBERS, [])
        for m in members:
            member = ET.SubElement(rel, C.MEMBER)
            (member.attrib[C.REF], member.attrib[C.ROLE],
             member.attrib[C.TYPE]) = m

        self.add_tags(rel)

        return osm

    def get_member_ids(self, namespace):
        "Return a set of members in the specified namespace."

        return set([str(mid) for (mid, mrole, mtype) in self[C.MEMBERS]])


#
# Factory function.
#

_namespace_to_factory = {
    C.CHANGESET:	OSMChangeSet,
    C.DATASTORE_CONFIG: OSMDatastoreConfig,
    C.GEODOC:		OSMGeoDoc,
    C.NODE:		OSMNode,
    C.WAY:		OSMWay,
    C.RELATION:		OSMRelation
    }

def new_osm_element(namespace, elemid):
    '''Create an OSM element.

    namespace   -- the OSM namespace.
    elemid      -- element id for the element.
    '''

    factory = _namespace_to_factory[namespace]

    return factory(elemid)

#
# JSON representation of an OSM element.
#

def decode_json(jsonvalue):
    "Returns a Python object, given its JSON representation."
    return cjson.decode(jsonvalue)

def encode_json(obj):
    "Returns the JSON representation for a Python object."
    return cjson.encode(obj)

#
# Protobuf handling.
#

try:
    import protobuf

    def _notimplemented(_):
        raise NotImplementedError, "Protobuf support has not been written"
        
    decode_protobuf = _notimplemented
    encode_protobuf = _notimplemented

except ImportError:

    def _noprotobufs(pbuf):
        "Returns an OSM element given its Protobuf representation."
        raise NotImplementedError, "Protobuf libraries are not present"

    decode_protobuf = _noprotobufs
    encode_protobuf = _noprotobufs
