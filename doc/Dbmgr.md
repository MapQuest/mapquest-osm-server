## About

This document describes the `dbmgr` ingestion tool.

## What the tool does

The `dbmgr` tool is used to:

1.  initialize the data store,
2.  to load data into the data store,
3.  to incrementally change existing information in the data store.

## Requirements

### Initialization

A command line option would specify that the data store needs to be
reset.  In the current code, this is the `-I` option.

### Input

The following input formats are proposed to be accepted by the tool:

1.  An OSM planet file in <osm> XML format.

    This would be used for initializing the data store from a regular
    [planet dump][planetdump].

2.  A "full" planet dump in <osm> XML format.

    See: task [#4][issue4].

    This would be used for initializing the data store from a
    [full planet dump][fullplanetdump].

3.  `osmChange` files in <osmChange> XML format.

    See: task [#14][issue14].

    These would be used for incremental updates to the data store,
    see the [planet.osm diffs page][planetdiffs]. 

4.  A planet file in [PBF format][planetpbf].

    See: task [#3][issue3].

    The PBF format has the same content as the OSM <osm> planet format,
    but is smaller and faster to process.

Note that while "full" planet dumps include \<changeset> information,
the [osmChange][] incremental format does not include information
about new \<changeset>s.  Thus, if a full planet dump is being
incrementally updated, additional changeset information for the change
would need to be downloaded separately from the main OSM server.

No data transfer format seems to support transfer of GPS tracks or of
user information.

### Backends

The following backends are planned to be supported (in approximate
order of priority):

1. A Membase based backend.
2. A CouchDB/BigCouch based backend.
3. A Riak based backend.

The code is to be structured in such a way that supporting another
distributed key/value store should be easy.

## Live Updates

The tool should be able to change data in the data store without
cluster downtime.

## Non-requirements

1.  Retrieval of diffs from 'planet.openstreetmap.org'.

    The tool does not automate the process of downloading
    minutely/hourly/daily diffs from <http://planet.openstreetmap.org/>.

## Handling multiple backends

Code to support each type of backend (CouchDB, Membase, etc.)
resides in a separate Python module (e.g., `datastore/ds_membase.py`).

The specifically module needed is loaded in dynamically (using
`__import__`); the module is expected to provide a class `Datastore`
that implements the required backend.

This approach avoids (package) dependencies on support code for unused
backend modules.

## Sizing Numbers

An analysis of `swales-101025.osm.bz2`.  This subset contains:

* 816036 nodes
* 80690 ways
* 382 relations

### Element sizes with JSON based storage

The OSM elements in the `swales-101025.osm.bz2` subset were stored in
the data store in JSON encoded form.  The size distribution seen was
as follows:

* Nodes
    * Average size 202 bytes
    * 12157 (1.489%) nodes exceed 256 bytes of JSON
    * 2538 (0.311%) nodes exceed 512 bytes of JSON
* Ways
    * Average size 351 bytes
    * 7134 (8.8%) exceed 512 bytes
    * 1267 (1.6%) exceed 1024 bytes
* Relations
    * Average size 1477 bytes
    * 90 (23.6%) exceed 2048 bytes
    * 44 (11.5%) exceed 3072 bytes
    * 25 (6.5%) exceed 4096 bytes

<!-- References -->

 [fullplanetdump]: http://wiki.openstreetmap.org/wiki/Planet.osm/full
 [issue3]: https://github.com/MapQuest/mapquest-osm-server/issues/3
 [issue4]: https://github.com/MapQuest/mapquest-osm-server/issues/4
 [issue14]: https://github.com/MapQuest/mapquest-osm-server/issues/14
 [osmChange]: http://wiki.openstreetmap.org/wiki/OsmChange
 [planetdiffs]: http://wiki.openstreetmap.org/wiki/Planet.osm/diffs
 [planetdump]: http://wiki.openstreetmap.org/wiki/Planet.osm
 [planetpbf]: http://wiki.openstreetmap.org/wiki/PBF
