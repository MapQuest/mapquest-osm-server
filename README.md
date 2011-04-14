# README

This is an experimental implementation of an API server that supports
a (read-only) subset of the [OSM v0.6 API][osmapi].

* The data store used by the server is a distributed key/value store.
  The implementation currently uses [Membase][membase] for the data
  store; however the design should work with other key/value systems.
* The server only supports read queries on map data.

## Current Status

This repository contains a working snapshot of the server.

The list of APIs supported is documented at the wiki page
[SupportedRequests][].

<!-- References -->

 [membase]: http://www.membase.org/ "Membase"
 [osmapi]: http://wiki.openstreetmap.org/wiki/API_v0.6 "OSM v0.6 API"
 [SupportedRequests]: https://github.com/MapQuest/mapquest-osm-server/wiki/SupportedRequests
