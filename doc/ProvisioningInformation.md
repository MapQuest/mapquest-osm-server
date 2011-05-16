## About

This document contains information about the resource requirements
needed for running an instance of this server.

**Note**: A pending issue ([#13][issue13]) is currently preventing the load of a complete
[planet][osmplanet].  The data below is therefore for a subset.

## Membase

* Membase version: 1.6.5 (i386), running on a laptop with 3GB RAM,
  running Ubuntu GNU/Linux:
* Source tree at commit [7bcb49c807f39fbb9989](https://github.com/MapQuest/mapquest-osm-server/commit/7bcb49c807f39fbb998958e3cfc14496077b065e).
* Extract: `india.osm.bz2` from `download.geofabrik.de`, dated
  2011-04-11:
  * Size: 53387268 bytes bzipped.
  * Containing 0 changesets, 3568521 nodes, 215498 ways, and 933 relations.
* Resource usage (Membase):
  * Reported disk usage: 920MB.
  * Reported RAM usage: 882MB (seems high?).
  * 245137 unique keys in the data store (using the default slab settings).
* Representative timings using the default configuration, with both Membase and front-end running on `localhost`:
  * First fetch of a node (i.e., with a 'cold' element cache): <br />
    `[I 110413 21:53:53 web:849] 200 GET /api/0.6/node/15382163 (127.0.0.1) 15.50ms`
  * First fetch of the ways for a node: <br />
    `[I 110413 21:53:57 web:849] 200 GET /api/0.6/node/15382163/ways (127.0.0.1) 5.40ms`
  * Subsequent re-fetch of the ways for the same node: <br />
    `[I 110413 21:54:00 web:849] 200 GET /api/0.6/node/15382163/ways (127.0.0.1) 0.99ms`
  * A re-fetch of the same node: <br />
    `[I 110413 21:54:10 web:849] 200 GET /api/0.6/node/15382163 (127.0.0.1) 0.68ms`

I do not have scaling numbers under load (yet).

## Related Tickets

* Ticket [#9][issue9] tracks efforts to reduce the data storage requirements for map data.
* Ticket [#13][issue13] tracks efforts to speed up ingestion of a full planet dump.

<!-- References -->

 [issue9]: https://github.com/MapQuest/mapquest-osm-server/issues/9
 [issue13]: https://github.com/MapQuest/mapquest-osm-server/issues/13
 [osmplanet]: http://wiki.openstreetmap.org/wiki/Planet.osm "OSM Planet"

