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

## Script entry point for the database management tool.

import os.path
import sys
import itertools

## Tool configuration
devconfigdir = 'config'
devconfigfilename = 'osm-api-server.cfg'

toolname = 'dbmgr'
toolversion = '0.1'
toolconfig = '/etc/openstreetmap/osm-api-server.cfg'

from datastore.ds_geohash import init_geohash
from dbmgr.dbm_input import makesource
from dbmgr.dbm_ops import DBOps
from dbmgr.dbm_stats import fini_statistics, init_statistics

import apiserver.const as C
from apiserver.osmelement import init_osm_factory

#
#
# SCRIPT ENTRY POINT
#

usage = '''%prog [--I|--init] [options]
       %prog [options] [files]...

       Manage an OSM database.

       Use option -h/--help for help on usage.'''

def main():
    'Manage the OSM DB during development.'
    from optparse import OptionParser

    parser = OptionParser(usage=usage, prog=toolname,
                          version='%prog ' + toolversion)
    parser.add_option('-b', '--buffering', dest='buffering', metavar="NUMBER",
                      default=64, type="int",
                      help="Buffer size in KB for *zip uncompression " +
                      "[%default]")
    parser.add_option('-B', '--backend', dest='backend', metavar='DBTYPE',
                      default=None,
                      help="Type of backend to use [from configuration file]"),
    parser.add_option('-C', '--config', dest='config', metavar="FILENAME",
                      default=toolconfig,
                      help="Path to configuration information [%default]")
    parser.add_option('-E', '--encoding', dest='datastore_encoding',
                      metavar='ENCODING', default=None, type="str",
                      help="Encoding for use for values [%default]"),
    parser.add_option('-I', '--init', dest='doinit', action='store_true',
                      default=False, help='(Re-)initialize the backend'),
    parser.add_option('-n', '--dryrun', dest='dryrun', metavar="BOOLEAN",
                      default=False, action="store_true",
                      help="Parse, but do not upload data [%default]")
    parser.add_option('-T', '--nothreading', dest='nothreading',
                      metavar="BOOLEAN", default=False, action="store_true",
                      help="Do not use threads [%default]"),
    parser.add_option('-v', '--verbose', dest='verbose', metavar="BOOLEAN",
                      default=False, action="store_true",
                      help="Be verbose")
    parser.add_option("-x", '--nochangesets', dest="nochangesets",
                      action="store_true", default=False,
                      help="Skip retrieval of changeset information "
                      "[%default]")

    options, args = parser.parse_args()

    # Read configuration information.
    configfiles = [options.config, os.path.join(sys.path[0], devconfigdir,
                                         devconfigfilename)]
    from ConfigParser import ConfigParser
    cfg = ConfigParser()
    cfg.read(configfiles)

    # Sanity check.
    if not cfg.has_section(C.FRONT_END):
        parser.error("Incomplete configuration, tried:\n\t" +
                     "\n\t".join(configfiles))

    # Override configuration options specified on the command line.
    if options.datastore_encoding:
        cfg.set(C.DATASTORE, C.DATASTORE_ENCODING, options.datastore_encoding)
    if options.backend:
        cfg.set(C.DATASTORE, C.DATASTORE_BACKEND, options.backend)

    # Initialize statistics.
    init_statistics(cfg, options)

    # Load in the desired interface to the datastore.
    backend = cfg.get(C.DATASTORE, C.DATASTORE_BACKEND)
    try:
        module = __import__('datastore.ds_' + backend,
                            fromlist=['Datastore'])
    except ImportError, x:
        parser.exit("Error: Could not initialize backend of type \"%s\": %s" %
                     (backend, str(x)))

    db = module.Datastore(cfg, not options.nothreading, True)

    if options.doinit:
        db.initialize()

    ops = DBOps(cfg, options, db)

    # Initialize the geohash module.
    init_geohash(cfg.getint(C.DATASTORE, C.GEOHASH_LENGTH),
                 cfg.getint(C.DATASTORE, C.SCALE_FACTOR))

    # Initialize the OSM element factory.
    init_osm_factory(cfg)

    # Turn file names into iterators that deliver an element at a time.
    try:
        iterlist = map(lambda fn: makesource(cfg, options, fn), args)
        inputelements = itertools.chain(*iterlist)
    except Exception, x:
        parser.exit("Error: " + str(x))

    for elem in inputelements:
        # Add basic elements
        if elem.namespace in [C.CHANGESET, C.NODE, C.RELATION, C.WAY]:
            ops.add_element(elem)
        else:
            raise NotImplementedError, "Element type: %s" % elem.kind

    ops.finish()
    fini_statistics(options)

if __name__ == '__main__':
    main()
