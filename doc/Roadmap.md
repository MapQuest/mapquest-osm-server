## About

This page lists the proposed evolution of the server.

## Current Status

* The code is functional: [planet dumps][osmplanet] can be ingested and their data retrieved using the [API][osmapi].
* Serving data via the API is quite fast (see [ProvisioningInformation][]), but ingesting a full planet is slow.
* Modules have unit tests.
* External documentation (i.e., the `doc/` directory) is upto-date.
* The supported data store is: [Membase][].

## Future work

* We need to support 'full' [Planet dumps][fullosmplanet] dumps, along with
  retrieval of changesets, element history and prior versions of elements (tickets [#4][issue4] and [#14][issue14]).
* Performance improvements that have been identified so far could be addressed:
    * The `/map` API call could be further speeded up by grouping nodes and ways based on geographical proximity.
    * The ingestion tool needs to be speeded up ([#13][issue13]) and possibly rewritten in a non-interpreted language.
* Storage efficiency can be improved:
    * A separate string table for frequently used strings could cut down storage needs.
    * Slabs could be coded more efficiently ([#9][issue9]).
* The "front-end" needs to be made fully asynchronous ([#2][issue2]).
* System tests that verify end-to-end integrity of the ingestion process are needed.
* More supported data stores: possibly [Riak][] ([#6][issue6]) for a scalable backend, or perhaps [BerkeleyDB][] for a single machine configuration.

<!-- References -->

  [BerkeleyDB]: http://www.oracle.com/technetwork/database/berkeleydb/overview/index.html "Berkeley DB"
  [fullosmplanet]: http://wiki.openstreetmap.org/wiki/Planet.osm/full "Full OSM Planet"
  [issue2]: https://github.com/MapQuest/mapquest-osm-server/issues/2
  [issue4]: https://github.com/MapQuest/mapquest-osm-server/issues/4
  [issue6]: https://github.com/MapQuest/mapquest-osm-server/issues/6
  [issue9]: https://github.com/MapQuest/mapquest-osm-server/issues/9
  [issue13]: https://github.com/MapQuest/mapquest-osm-server/issues/13
  [issue14]: https://github.com/MapQuest/mapquest-osm-server/issues/14
  [membase]: http://www.membase.org/ "Membase"
  [osmapi]: http://wiki.openstreetmap.org/wiki/API_v0.6 "OSM v0.6 API"
  [osmplanet]: http://wiki.openstreetmap.org/wiki/Planet.osm "OSM Planet"
  [ProvisioningInformation]: ProvisioningInformation.md
  [riak]: http://www.basho.com/ "Riak"
  [wiki]: https://github.com/MapQuest/mapquest-osm-server/wiki "Wiki"
