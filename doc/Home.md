## About

This is an experimental API server for [Open Street Map][osm] map
data.

- The server supports most of the read operations on map data defined by
  [version 0.6][osmapi] of the OSM API (see [SupportedRequests][] for the
  precise list).
- For its data store, the server currently uses [Membase][membase], a
  scalable distributed key/value store.  Support for other scalable
  key/value stores should be easy to add.
- The server has been designed to be easy to scale out horizontally.

## Further Reading

* [Overview][] -- An overview of the implementation.
* [DeploymentInstructions][] -- How to deploy the server.
* [ProvisioningInformation][] -- Sizing information for running a server.
* [Roadmap][] -- The steps going forward.
* [SupportedRequests][] -- The list of supported HTTP requests.

<!--  Reference Links  -->

 [DeploymentInstructions]: DeploymentInstructions.md
 [membase]:    http://www.membase.org/ "Membase"
 [osm]:	       http://www.openstreetmap.org/ "Open Street Map"
 [osmapi]:     http://wiki.openstreetmap.org/wiki/API_v0.6 "OSM API v0.6"
 [Overview]:   Overview.md
 [python]:     http://www.python.org/ "The Python Language"
 [ProvisioningInformation]: ProvisioningInformation.md
 [Roadmap]:    Roadmap.md
 [SupportedRequests]: SupportedRequests.md
