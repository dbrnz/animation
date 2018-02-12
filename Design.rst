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

Positioning
~~~~~~~~~~~

* absolute
* relative to another element

    - `y="10px above id1 id2"`
    - if no `x` given then calculated as mean of x-coordinate of ids
    - `y` above/below
    - `x` left/right (-of)
    - also for box/container postioning
    - need to check for consistency -- we want a DAG!

* units

    - global (absolute)

        + e.g. 'pixel'

    - proportional (relative)

        + in relation to diagram
        + in relation to container

* points
* lines

    - start/end point
    - single point, angle, and ending condition (e.g. length, intersection)

        + from ID at ANGLE until ??

* polylines

    - collection of points

        + from ID1 at ANGLE1; to ID2 at ANGLE2
        + from ID1 at ANGLE1; parallel DISTANCE from LEFT ID2; to ID3 at ANGLE3

    - a connected set of lines
    - polygon boundary
* polygons


::

    implicit and explicit rules.

    <point ref="id1">
        <x offset="10" dirn="left" rel="id2"/>
        <y/>
    </point>

    <line ref="id3">
        <mid-point>
            <x
