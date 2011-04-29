## About

This page describes enhancements to the current design of the API
server.

## Speeding Up Ingestion

Ingestion of a planet dump by the [ingestion tool][dbmgr] needs to be
sped up.  This issue is being tracked in [issue #13][issue13].

Currently:

*  When processing `nodes`, the tool appears to be limited by Python's
   bytecode interpretation overhead---I/O does not seem to introducing
   a bottleneck.
*  When processing `ways` and `relations` in the planet dump, the
   program becomes bound by I/O latencies.  In particular,
       * The current design of the element cache is inefficient for
	 nodes (see below).
       * The program processes one way or relation element at a time
	 (i.e., in a single-threaded fashion).

## Improving Cache Efficiencies

The upstream [OSM API][osmapi] numbers new map elements (nodes, ways
and relations) sequentially, as and when they are created.  This means
that elements that are geographically 'close' can have ids that are
far apart in numeric value.

In the current design elements are [grouped into 'slabs'][slabutil.py]
by element id.  API queries however, tend to be for OSM elements which
are geographically 'close' to each other.  For such queries, the
current scheme is inefficient both from the point of view of I/O
traffic and (cache) RAM consumption.

A better scheme would therefore be:

* Group elements into geographically keyed slabs; elements in each
  slab would be "close by" in terms of geographical distance.
* For direct lookups of elements via the API, use a mapping from
  element ids to the slabs holding element's definition.
  
In this new scheme, direct lookups of elements would need two key
retrievals from the data store, compared to one retrieval in the
current scheme.  However, the improvements to the efficiency of the
element cache should compensate for this additional overhead.

See also: Issue [#16][issue16].

<!-- References -->

 [dbmgr]: https://github.com/MapQuest/mapquest-osm-server/tree/master/src/python/dbmgr
 [issue13]: https://github.com/MapQuest/mapquest-osm-server/issues/13
 [issue16]: https://github.com/MapQuest/mapquest-osm-server/issues/16
 [osmapi]: http://wiki.openstreetmap.org/wiki/API_v0.6 "OSM API v0.6"
 [slabutil.py]:  https://github.com/MapQuest/mapquest-osm-server/blob/master/src/python/datastore/slabutil.py
