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

## The script entry point for the front-end server.

import os.path
import sys
import tornado.options

import apiserver.const as C
from fe import OSMFrontEndServer
from apiserver.osmelement import init_osm_factory
from datastore.slabutil import init_slabutil

# Where to find configuration information.
default_config_directory	= "config"
default_config_file		= "osm-api-server.cfg"

tornado.options.define("backend", default=None,
                       type=str, metavar="BACKEND",
                       help="datastore backend to use")
tornado.options.define("config", default=default_config_file,
                       type=str, metavar="FILE",
                       help="configuration file to use")
tornado.options.define("encoding", default=None,
                       type=str, metavar="ENCODING",
                       help="Encoding used for values")
tornado.options.define("verbose", default=False,
                       type=bool, metavar="BOOLEAN",
                       help="Control verbosity")

def error(message):
    "Print an error message and exit."
    sys.stderr.write("Error: " + message + "\n")
    sys.exit(1)

##
## Script entry point.
##
def main():
    """Launch the API server."""
    # Parse command line options if present.
    tornado.options.parse_command_line()
    options = tornado.options.options

    # Bring in (server-wide) configuration information.
    try:
        import configparser         # Python 3.0
    except ImportError:
        import ConfigParser as configparser

    # Read configuration information.
    configfiles = [options.config,
                   os.path.join(sys.path[0], default_config_directory,
                                default_config_file)]
    cfg = configparser.ConfigParser()
    cfg.read(configfiles)

    # Sanity check.
    if not cfg.has_section(C.FRONT_END):
        error("Incomplete configuration information, tried:\n\t" +
              "\n\t".join(configfiles))

    # Allow command-line options to override the configuration file.
    if options.backend:
        cfg.set(C.DATASTORE, C.DATASTORE_BACKEND, options.backend)
    if options.encoding:
        cfg.set(C.DATASTORE, C.DATASTORE_ENCODING, options.encoding)

    # Load the desired interface to the datastore.
    backend = cfg.get(C.DATASTORE, C.DATASTORE_BACKEND)
    try:
        module = __import__('datastore.ds_' + backend, fromlist=['Datastore'])
        datastore = module.Datastore(cfg)
    except ImportError, x:
        error("Could not initialize datastore of type \"%s\": %s" %
              (backend, str(x)))

    # Initialize the OSM element factory and other modules.
    init_slabutil(cfg)
    init_osm_factory(cfg)

    # Create an instance of the front-end server.
    port = cfg.getint(C.FRONT_END, C.PORT)
    feserver = OSMFrontEndServer(cfg, options, datastore)
    http_server = tornado.httpserver.HTTPServer(feserver.application)
    http_server.listen(port)

    # Start the server.
    try:
        tornado.ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        if options.verbose:
            pass                # Print statistics etc.

#
# Invoke main()
#
if __name__ == "__main__":
    main()
