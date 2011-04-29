## About

This page lists the planned evolution of the server.

## Version 0.5

* The code is functional, but need not be fast.
* Modules have unit tests.
* External documentation (i.e., on the [wiki][]) is upto-date.
* [Planet dumps][osmplanet] may be ingested and their data retrieved
  using the [API][osmapi].
* Supported data store: [Membase][].

## Version 0.7

* Performance bottlenecks have been identified and addressed.
* Full [Planet dumps][fullosmplanet] dumps are supported, along with
  retrieval of history and previous versions of elements (tickets [#14][issue14] and [#4][issue4]).
* The "front-end" is fully asynchronous ([#2][issue2]).
* System tests have been added.
* Wiki and internal documentation is complete and upto-date.
* Supported data stores: [Membase][] and possibly [Riak][] ([#6][issue6]).

<!-- References -->

  [fullosmplanet]: http://wiki.openstreetmap.org/wiki/Planet.osm/full "Full OSM Planet"
  [issue2]: https://github.com/MapQuest/mapquest-osm-server/issues/2
  [issue4]: https://github.com/MapQuest/mapquest-osm-server/issues/4
  [issue6]: https://github.com/MapQuest/mapquest-osm-server/issues/6
  [issue14]: https://github.com/MapQuest/mapquest-osm-server/issues/14
  [membase]: http://www.membase.org/ "Membase"
  [osmapi]: http://wiki.openstreetmap.org/wiki/API_v0.6 "OSM v0.6 API"
  [osmplanet]: http://wiki.openstreetmap.org/wiki/Planet.osm "OSM Planet"
  [riak]: http://www.basho.com/ "Riak"
  [wiki]: https://github.com/MapQuest/mapquest-osm-server/wiki "Wiki"
