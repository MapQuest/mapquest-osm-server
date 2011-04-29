# README

This is an experimental implementation of an API service that supports
a (read-only) subset of the [OSM v0.6 API][osmapi].

The goal for this project is to explore an implementation of the
[OSM API][osmapi] built over a distributed key/value store (i.e., a
"NoSQL" backend).  The service has been designed to be easy to scale
horizontally.

The implementation currently uses [Membase][membase] for the data
store; however its design should work with other key/value systems.

## Current Status

This repository contains a working snapshot of the service.
The server only supports read queries on map data.

## Further Information

Information on how to use this software package may be found in the
project's [documentation][].

<!-- References -->

 [membase]: http://www.membase.org/ "Membase"
 [osmapi]: http://wiki.openstreetmap.org/wiki/API_v0.6 "OSM v0.6 API"
 [documentation]: doc/Home.md
