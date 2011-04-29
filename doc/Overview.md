## About

This document presents an overview of this map server.

## Goals

The goal of this project is to explore an implementation of an
OSM-like map server using a scalable, distributed, key/value system
for data storage.

Access to map data would be using the [APIs][osmapi] defined by the
OSM project.  Currently, this prototype supports a read-only subset of
the [OSM APIs][osmapi].

## Architecture

The server has three major components.

*   The "data store".

    The data store is a persistent store of map data.  Map data from
    "[planet.osm][osmplanet]" snapshots is processed by an ingestion tool
    (see below) and is stored in key/value form in the data store.
    
    The key/value store needs to be able to deal with a large number
    of keys; the current prototype uses [membase][].

*   The "front end".
    
    The front end responds to HTTP requests of the form defined by the
    [OSM API][osmapi].   The list of supported requests may be found in
    [SupportedRequests][].
    
*   The data store manager.

    This tool is used to ingest [planet.osm][osmplanet] and
    [OSM change][osmchange] files published by the [openstreetmap][]
    project into the data store.

## Configuration

Most aspects of the operation of the server is controlled by a
configuration file, see the file [osm-api-server.cfg][configsrc].

## See Also

* [DesignMistakes][] -- Alternative designs that were tried, but
  which did not work out well.
* [Improvements][] -- (Near term) improvements to the design.

<!-- References -->

 [configsrc]: https://github.com/MapQuest/mapquest-osm-server/blob/master/src/python/config/osm-api-server.cfg "Configuration file"
 [DesignMistakes]: DesignMistakes.md
 [Improvements]: Improvements.md
 [membase]: http://www.membase.org/ "Membase"
 [osmapi]: http://wiki.openstreetmap.org/wiki/API_v0.6 "OSM v0.6 API"
 [osmchange]: http://wiki.openstreetmap.org/wiki/OsmChange "OSM Change"
 [osmplanet]: http://wiki.openstreetmap.org/Planet.osm "Planet.OSM"
 [openstreetmap]: http://www.openstreetmap.org/ "Open Street Map"
 [SupportedRequests]: SupportedRequests.md
