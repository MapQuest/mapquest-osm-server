## Supported HTTP requests

This server currently supports the following subset of the [OSM v0.6 API](http://wiki.openstreetmap.org/wiki/API_v0.6).

<table width="100%" border=0>
 <thead>
  <tr>
    <th align="left">Operation/URI</th><th align="left">Description</th>
  </tr>
 </thead>
 <tbody>
   <tr>
    <td>GET /</td>
    <td>Return information about this server instance.</td>
   </tr>
   <tr>
    <td>GET /api/capabilities</td>
    <td>Retrieve server information.</td>
   </tr>
   <tr>
    <td>GET /api/0.6/capabilities</td>
    <td>Retrieve server information.</td>
   </tr>
   <tr>
    <td>GET /api/0.6/map?bbox=l,b,r,t</td>
    <td>Retrieve information by a bounding box.</td>
   </tr>
   <tr>
    <td>GET /api/0.6/node/NNNN</td>
    <td>Retrieve node `NNNN`.</td>
   </tr>
   <tr>
    <td>GET /api/0.6/way/NNNN</td>
    <td>Retrieve way `NNNN`.</td>
   </tr>
   <tr>
    <td>GET /api/0.6/relation/NNNN</td>
    <td>Retrieve relation `NNNN`.</td>
   </tr>
   <tr>
    <td>GET /api/0.6/nodes?nodes=#,#,#,...</td>
    <td>Retrieve multiple nodes in one request.</td>
   </tr>
   <tr>
    <td>GET /api/0.6/ways?ways=#,#,#,...</td>
    <td>Retrieve multiple ways in one request.</td>
   </tr>
   <tr>
    <td>GET /api/0.6/relations?relations=#,#,#,...</td>
    <td>Retrieve multiple relations in one request.</td>
   </tr>
   <tr>
    <td>GET /api/0.6/nodes/NNNN/relations</td>
    <td>Retrieve relations for a node.</td>
   </tr>
   <tr>
    <td>GET /api/0.6/ways/NNNN/relations</td>
    <td>Retrieve relations for a way.</td>
   </tr>
   <tr>
    <td>GET /api/0.6/relations/NNNN/relations</td>
    <td>Retrieve relations for a relation.</td>
   </tr>
   <tr>
    <td>GET /api/0.6/node/NNNN/ways</td>
    <td>Retrieve ways for a node.</td>
   </tr>
   <tr>
    <td>GET /api/0.6/way/NNNN/full</td>
    <td>Retrieve a way and all nodes referenced by the way.</td>
   </tr>
   <tr>
    <td>GET /api/0.6/relation/NNNN/full</td>
    <td>Retrieve a relation, all nodes and ways that are its members, and all nodes referenced by the ways being returned.</td>
   </tr>
 </tbody>
</table>
