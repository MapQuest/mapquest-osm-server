# README

This directory contains a [Python][python] implementation of a
scalable API server for OSM map data.

## Directory Contents

* `apiserver/`

    Common definitions and utilities.

* `datastore/`

    Interfaces to various key/value stores.

* `dbmgr/`

    Code for the data store management utility.

* `frontend/`

    Code for the 'frontend' of the API server.

* `tests/`

    Test code.

## Running the code 'in-place'

* Configuration information for these tools is specified in the file
  `config/osm-api-server.cfg`.
* The script `front-end` starts the server.  With the default
  configuration, this server would need to be run as root since it
  listens for API requests on port 80.  The listening port may be
  changed using the configuration file (see section `front-end`,
  configuration item `port`).

    % sudo ./front-end

* The script `db-mgr` invokes the ingestion tool.  For example:
    * To initialize the data store, use:

        % ./db-mgr -I

    * To load a "planet.osm" planet dump into the data store, use:

        % ./db-mgr PLANET.OSM

Both scripts support a `--help` option.

<!-- References. -->

 [python]: http://www.python.org/ "The Python Programming Language"
