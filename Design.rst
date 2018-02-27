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
--------------------

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

    - `y="10px above #id1 #id2"`
    - if no `x` given then calculated as mean of x-coordinate of #ids
    - `y` above/below
    - `x` left/right (-of)
    - also for box/container postioning
    - need to check for consistency -- we want a DAG!

* units

    - absolute

        + e.g. pixel: `px`

    - proportional (relative)

        + 1000 units per side of bounding box
        + in relation to diagram: `g`
        + in relation to container: `l`
        + modifiers to specify bounding box side: `gx`, `gy`, `lx`, `ly`.

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

    # implicit and explicit rules.
    # units default to `l`

    pos="100 right #id"                  ## x = x(id) + 100; y = y(id)
    pos="10 below #id"                   ## x = x(id); y = y(id) + 10
    pos="100 right #id1, 10 below #id2"  ## x = x(id1) + 100; y = y(id2) + 10
    pos="100 above #id1, 10 left #id2"   ## x = x(id2) - 10; y = y(id1) - 100

    # Multiple defining elements
    pos="100 right #id1 #id2"           ## x = (x(id1) + x(id2))/2 + 100; y = (y(id1) + y(id2))/2

    # Can't overspecify
    pos="100 right/left #id1, 10 right/left #id2"    ## ERROR
    pos="100 above/below #id1, 10 above/below #id2"  ## ERROR

    pos="(100, 10)"                      ## x = 100; y = 10

    pos="100 right"  ## Of what??
    pos="right #id"  ## How much?? Do we have default offsets?
                     ## `transporter-spacing`, `potential-offset`, `flow-offset` ??
                     ## and override this via style sheet??

    # Transporters are always on a compartment boundary
    pos="100 top"    ## x = x(compartment) + 100; y = y(compartment)
    pos="bottom"     ## y = y(compartment) + height(compartment)

    pos="100 top"    ## same as pos="100 right #compartment"
    pos="100 bottom" ## same as pos="100 right #compartment; 1000 below #compartment"

    pos="top, 10 right #t1"    ## same as pos="0 below #compartment; 10 right #t1"
    pos="right, 10 below #t2"  ## same as pos="1000 right #compartment; 10 below #t2"

    pos="top, 10 above/below #t1"  ## ERROR: multiple `y` constraints
    pos="left, 10 left/right #t1"  ## ERROR: multiple `y` constraints
    pos="10 right, 10 below #t2"   ## ERROR: multiple `y` constraints
    pos="5 left #t1, 100 bottom"   ## ERROR: multiple `x` constraints

    # Autopositioning
    pos="top"  # default is top  }
    pos="top"  #                 } Centered in top, spaced evenly (`transporter-spacing`?)
    pos="top"  #                 }



    Transporter posn:

    <posn> ::=  <side> [ , <offset> ]
    <offset> ::= <length>  // From top/left of compartment
              |  <length> <reln> <element-ref>


    Compartment posn:

    Compartment size:

    Quantity/Potential/Flow posn:


