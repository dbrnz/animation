CellDL Design
=============

Separation of abstract concepts
-------------------------------

* Topological relationships between cell elements (structure).
* Geometrical positioning of cell elements.
* Pathways corresponding to a CellML bond-graph model.


Structure
---------

* Compartments
* Transporters
* Quantities


Geometry
--------

* units (inherit/diagram/local)
* aspect ratio (compartments)
* position (compartments, quantities, transporters)
* size (compartments)
* `items` in `boxes`

Bond-graph
----------

* Adds `potentials` and `flows`.
* A flow consists of one or more `fluxes`.
* A flux has a `count`, giving its stoichiometry.

Interfacing
-----------

* Pre-declared compartments
* Incorporating graphic elements `<image id="image-id"/>` along with style rule to
  define image source (so that abstract structure and diagram realisation are kept
  separate).


Identifying elements
~~~~~~~~~~~~~~~~~~~~

* `id` attribute
* `ref` attribute (or use `xlink:href` ??)
* prefix the id with `#` when using it as the value of a `ref` ??

* References in the form `/compartment1/compartment2/quantity` and `#transporter`.
* Check how relative URLs are converted to absolute URLs in SVG.
* SVG refers to XML Base (https://www.w3.org/TR/xmlbase/) and HTML (https://www.w3.org/TR/html51/infrastructure.html#parsing-urls).


Styling
-------

Drawing
-------

* Combines structure, geometry, bond-graph and styling information.
