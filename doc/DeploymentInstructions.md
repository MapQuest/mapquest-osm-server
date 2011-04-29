## About

This document describes how to install and maintain an instance of
this server.

## Note

Currently, the 'front-end server' and the 'ingestion tool' (the
document [Overview][] describes what these are) work "in-place" in the
source tree.  An install-friendly package is yet to be created; see
ticket [#5][issue5].

## Software Dependencies

The server uses the following software packages:

1. The [Python][], programming language.
1. [Tornado][], a [Python][] web server framework, for the front-end.
1. [lxml][], a [Python][] XML parsing library, used by both the
   front-end and the ingestion tool.
1. The [cjson][] JSON (en|de)coder module 
1. [Membase][], a scalable, distributed key/value store, used as the
   data store.
1. [Python Geohash][pygeohash], a geohashing library.
1. [Python Memcache][pymemcache], a [Memcache][] interface for [Python][],
   used to connect to the [Membase][] server, in compatibility mode.
1. [Py.Test][pytest], a test framework.

### Installation on Ubuntu 10.04 LTS

To install these dependencies on an Ubuntu GNU/Linux v10.04 LTS system, do:

1.  Install [Membase][]:
    1.  Download the `.deb` file appropriate for your computer architecture
	from the project's [download page][membasedownload].
    1.  Install the download `.deb` package using the **dpkg** utility.
    	For example:
```shell
% sudo dpkg -i membase-server-community_x86_1.6.5.3.deb
```
	Repeat this on all the machines that you wish to run your
	[Membase][] cluster on.
    1.  Using your browser, login to the membase console at
    	http://*hostname*:8091, and create a default bucket of type
	'membase' listening on port 11211. If you have multiple machines
	in your [Membase][] cluster, you would need to login and setup
	each of these.

    *Note*: By default [Membase][] will listen and accept protocol requests
    on *all* network interfaces.  On an internet-facing server, you would
    need to adjust your firewall rules to prevent the world+dog from accessing
    your membase instance.
2.  Install pre-packaged binaries:
```shell
% sudo apt-get install git-core gcc g++
% sudo apt-get install python2.6 python2.6-dev python-lxml python-setuptools python-memcache python-cjson
```
3.  Install additional Python libraries and tools
    1.  Install [Python geohash][pygeohash] using `easy_install`:
```shell
% sudo easy_install python-geohash
```
    1. Install [Tornado][]:
```shell
% git clone https://github.com/facebook/tornado.git
% cd tornado
% sudo python setup.py install
```
4.  Optional stuff:
    1.  Install `py.test`, if you wish to run the tests:
```shell
% sudo easy_install pytest
```

## Setup

The procedure to bring up the server is as follows.

1. Install the dependencies listed above.
1. Checkout the server source from [GitHub][].
```shell    
% git clone git://github.com/MapQuest/mapquest-osm-server.git
```
1. Edit the file `src/python/config/osm-api-server.cfg`, and change
   the `dbhost` configuration item in section `membase` to point to
   where your [Membase][] instance lives.  The default configuration
   assumes that your membase server is running on localhost.
1. Download a [planet.osm][osmplanet] dump or subset thereof, for
   example, from <http://geofabrik.de/>.
1. Load in the downloaded planet file using the `db-mgr` tool:
```shell    
% cd src/python
% ./db-mgr PATH-TO-THE-DOWNLOADED-PLANET
```
1.  Run the front-end of the server:
```shell
% sudo ./front-end
```
    The server listens for API requests on port 80 by default.  The
    configuration item `port` in the configuration section `front-end`
    can be used to change this.
1.  Check operation of the server.  Assuming that the default
    configuration, you could try:
```shell
% curl http://localhost/api/capabilities
<?xml version='1.0' encoding='utf-8'?>
<osm version="0.6" generator="OSM API Server Prototype 0.6">
 <api>
   <version minimum="0.6" maximum="0.6"/>
    <area maximum="180.0"/>
    <tracepoints per_page="5000"/>
    <waynodes maximum="2000"/>
    <changesets maximum_elements="50000"/>
    <timeout seconds="300"/>
 </api>
</osm>
```
    The document [SupportedRequests][] lists the current set of APIs supported.

<!-- References -->

 [github]: http://www.github.com/ "GitHub"
 [issue5]: https://github.com/MapQuest/mapquest-osm-server/issues/5 "Issue 5"
 [lxml]: http://lxml.de/ "XML Processing Library"
 [Membase]: http://www.membase.org/ "Membase"
 [membasedownload]: http://www.couchbase.com/downloads/membase-server/community
 [memcache]: http://memcached.org/ "Memcache"
 [osmplanet]: http://wiki.openstreetmap.org/wiki/Planet.osm "OSM Planet"
 [Overview]: Overview.md
 [pygeohash]: http://pypi.python.org/pypi/python-geohash "Geohashing library"
 [pymemcache]: http://pypi.python.org/pypi/python-memcached/ "Memcache interface"
 [pytest]: http://www.pytest.org/ "Py.Test"
 [Python]: http://www.python.org/ "The Python Programming Language"
 [SupportedRequests]: SupportedRequests.md
 [Tornado]: http://www.tornadoweb.org/ "The Tornado Web Server"
 [cjson]: http://pypi.python.org/pypi/python-cjson "The cjson JSON en/decoder library" 
