## About

This page contains information about implementation approaches that were tried but which did not work well.

## CouchDB's 'views' (slow responses)

In an earlier version of this server I had used a [CouchDB][] backend to store map data.   The `/map` API was implemented by using CouchDB's [views][couchdbviews].

The reasons I abandoned this approach were:

1.  CouchDB's [views][couchdbviews] turned out to be slow, causing the `/map` call to take several
    hundreds of milliseconds to complete.  This was well over my design goal.
2.  [CouchDB][]'s on-disk storage scheme seemed to need a large amount of disk space.  Given that the
    size of the OSM dataset is already large (over one billion nodes, nearly a hundred million ways,
    and growing), these high overheads were a concern.
3.  [CouchDB][] uses HTTP based access; every data store access was thus high overhead.

## Vanilla Membase (high memory overheads)

In the initial design of the [Membase based data store][dsmembase.py] I mapped each node, way and relation
one to one to a Membase key.  While this approach is simple, it does not scale well: [Membase][]
as of the current version (v1.6.5), has an [overhead of 120 bytes][membasesizing] per key.  Thus
we would need 120G of RAM to store _just the keys_ for the current OSM data set.

My current design [groups keys into "slabs"][slabutil.py].  This brings down the number of (membase)
keys needed to manageable levels.   I/O is done in terms of slabs, and a local ["cache" with LRU
semantics][lrucache.py] is used to reduce the number of I/O requests sent to the Membase server.

<!-- References -->

 [couchdb]: http://couchdb.apache.org/ "Apache CouchDB"
 [couchdbviews]: http://wiki.apache.org/couchdb/Introduction_to_CouchDB_views "CouchDB Views"
 [ds.py]: https://github.com/MapQuest/mapquest-osm-server/blob/master/src/python/datastore/ds.py
 [dsmembase.py]: https://github.com/MapQuest/mapquest-osm-server/blob/master/src/python/datastore/ds_membase.py
 [lrucache.py]:  https://github.com/MapQuest/mapquest-osm-server/blob/master/src/python/datastore/lrucache.py
 [membase]: http://www.membase.org/ "Membase"
 [membasesizing]: http://techzone.couchbase.com/wiki/display/membase/Sizing+Guidelines "Sizing Guidelines"
 [slabutil.py]:  https://github.com/MapQuest/mapquest-osm-server/blob/master/src/python/datastore/slabutil.py
