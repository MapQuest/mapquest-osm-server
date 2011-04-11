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

## Support retrieval of the server's capabilities.

import tornado.web

from lxml import etree as ET

import apiserver.const as C
from apiserver.osmelement import new_osm_response
from util import response_to_xml

# Sample output:
# 
# <osm version="0.6" generator="OpenStreetMap server">
#   <api>
#     <version minimum="0.6" maximum="0.6"/>
#     <area maximum="0.25"/>
#     <tracepoints per_page="5000"/>
#     <waynodes maximum="2000"/>
#     <changesets maximum_elements="50000"/>
#     <timeout seconds="300"/>
#   </api>
# </osm>

class CapabilitiesHandler(tornado.web.RequestHandler):
    "Handle requests for server capabilities."

    def initialize(self, cfg):
        self.cfg = cfg

    def get(self):
        self.set_header(C.CONTENT_TYPE, C.TEXT_XML)

        def _get(name):
            return self.cfg.get(C.FRONT_END, name)

        osm = new_osm_response()

        api = ET.SubElement(osm, "api")
        version = ET.SubElement(api, "version")
        version.attrib['minimum'] = _get(C.API_VERSION_MINIMUM)
        version.attrib['maximum'] = _get(C.API_VERSION_MAXIMUM)
        area = ET.SubElement(api, "area")
        area.attrib['maximum'] = _get(C.AREA_MAX)

        tracepoints = ET.SubElement(api, "tracepoints")
        tracepoints.attrib['per_page'] = _get(C.TRACEPOINTS_PER_PAGE)
        
        waynodes = ET.SubElement(api, "waynodes")
        waynodes.attrib['maximum'] = _get(C.WAYNODES_MAX)

        changesets = ET.SubElement(api, "changesets")
        changesets.attrib['maximum_elements'] = _get(C.CHANGESETS_MAX)

        timeout = ET.SubElement(api, "timeout")
        timeout.attrib['seconds'] = _get(C.API_CALL_TIMEOUT)

        self.write(response_to_xml(osm))
