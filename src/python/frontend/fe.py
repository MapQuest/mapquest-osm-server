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

import tornado.httpserver
import tornado.ioloop
import tornado.web

import sys

#
# Local modules
#
import	apiserver.const as C                   # 'constants'
from	capabilities import CapabilitiesHandler
from	maphandler   import MapHandler
from	osmelement   import OsmElementHandler, OsmElementRelationsHandler, \
    OsmFullQueryHandler, OsmMultiElementHandler, OsmWaysForNodeHandler

#
# Handling access to '/'.
#
class RootHandler(tornado.web.RequestHandler):
    """Handle requests for "/".

    Print a message pointing the user to the right API calls."""

    default_message = """\
<html>
  <head>
    <title>A scalable, read-only, OSM API Server</title>
  </head>
  <body>
   <h1>Welcome</h1>

   <p>You have reached an experimental implementation of an API server
      serving map data from the <a
      href="http://www.openstreetmap.org/">OpenStreetMap</a> project.</p>

   <h2>API Version / Operations Supported</h2>
   <p>This server supports read queries conforming to the <ab
     href="http://wiki.openstreetmap.org/wiki/API_v%(apiversion)s">v%(apiversion)s</a>
     OSM API.</p>
   <p>OSM API calls that change map data are not supported.</p>

   <h2>More Information</h2>
   <p>This server is being developed as an open-source project.</p>
   <ul>
     <li><p>Source code for the project is available at:
       <a href="%(sourcerepository)s">%(sourcerepository)s</a>.</p></li>
     <li><p>Documentation for project is available at:
       <a href="%(projectdoc)s">%(projectdoc)s</a>.</p></li>
   </ul>
  </body>
</html>"""

    def initialize(self, cfg):
        self.usagemessage = RootHandler.default_message % dict(
            apiversion=cfg.get(C.FRONT_END, C.API_VERSION),
            projectdoc=cfg.get(C.DEFAULT, C.PROJECT_DOC),
            sourcerepository=cfg.get(C.DEFAULT, C.SOURCE_REPOSITORY))

    def get(self):
        self.write(self.usagemessage)


class ReadOnlyHandler(tornado.web.RequestHandler):
    """Return an error for URLs that a read-only server does not support."""

    def initialize(self, cfg=None):
        pass


class NotImplementedHandler(tornado.web.RequestHandler):
    """Return an error for URIs that are unimplemented."""

    def initialize(self, cfg=None):
        pass

    def get(self, request):
        raise tornado.web.HTTPError(501) # Not Implemented

#
# The OSM front end server.
#
class OSMFrontEndServer:
    """The OSM Front End.

    This wrapper class encapsulates an instance of a Tornado
    'Application' implementing the front end server, and its
    associated configuration information.

    Example:
       >> cfg = ConfigParser.ConfigParser()
       >> cfg.read(my-config-file)
       >> db = <a datastore.DataStore object>
       >> frontend = OSMFrontEndServer(cfg, options, db)

    Attributes:

        application     The Tornado 'Application' for this server
                        instance.
        config          Configuration information for this instance.
        datastore       Datastore in use.
    """

    def __init__(self, cfg, options, datastore):
        """Initialize an OSMFrontEnd.

        Parameters:

        config          Configuration information.
        options         Command line options.
        datastore       Datastore in use.
        """

        osm_api_version = cfg.get(C.FRONT_END, C.API_VERSION)

        # Link URLs to their handlers.
        application = tornado.web.Application([
            (r"/api/%s/map" % osm_api_version, MapHandler,
             dict(cfg=cfg, datastore=datastore)),
            (r"/api/%s/capabilities" % osm_api_version, CapabilitiesHandler,
             dict(cfg=cfg)),
            (r"/api/%s/changeset/([0-9]+)/close" % osm_api_version,
             NotImplementedHandler, dict(cfg=cfg)),
            (r"/api/%s/changeset/([0-9]+)/download" % osm_api_version,
             NotImplementedHandler, dict(cfg=cfg)),
            (r"/api/%s/changeset/([0-9]+)/expand_bbox" % osm_api_version,
             NotImplementedHandler, dict(cfg=cfg)),
            (r"/api/%s/changeset/([0-9]+)/upload" % osm_api_version,
             NotImplementedHandler, dict(cfg=cfg)),
            (r"/api/%s/changesets" % osm_api_version,
             NotImplementedHandler, dict(cfg=cfg)),
            (r"/api/%s/node/([0-9]+)/ways" % osm_api_version,
             OsmWaysForNodeHandler, dict(datastore=datastore)),
            (r"/api/%s/(nodes|ways|relations)" % osm_api_version,
             OsmMultiElementHandler, dict(datastore=datastore)),
            (r"/api/%s/(node|way|relation)/create" % osm_api_version,
             ReadOnlyHandler, dict(cfg=cfg)),
            (r"/api/%s/(node|way|relation)/([0-9]+)/history" %
             osm_api_version, NotImplementedHandler,
             dict(cfg=cfg)),
            (r"/api/%s/(node|way|relation)/([0-9]+)/([0-9]+)" %
             osm_api_version, NotImplementedHandler,
             dict(cfg=cfg)),
            (r"/api/%s/(node|way|relation)/([0-9]+)/relations" %
             osm_api_version, OsmElementRelationsHandler,
             dict(datastore=datastore)),
            (r"/api/%s/(changeset|node|way|relation)/([0-9]+)" %
             osm_api_version, OsmElementHandler, dict(datastore=datastore)),
            (r"/api/%s/(way|relation)/([0-9]+)/full" % osm_api_version,
             OsmFullQueryHandler, dict(datastore=datastore)),
            (r"/api/capabilities", CapabilitiesHandler, dict(cfg=cfg)),
            (r"/", RootHandler, dict(cfg=cfg))
        ])

        self._application = application
        self._config = cfg
        self._datastore = datastore

    def _get_application(self):
        return self._application
    def _get_config(self):
        return self._config
    def _get_datastore(self):
        return self._datastore

    application = property(_get_application)
    config = property(_get_config)
    datastore = property(_get_datastore)
