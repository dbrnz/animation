Specifying Cell Diagrams
========================

Overview
--------

* membranes have channels/transporters (use Reactome terminolgy ??)
* types/classes of membranes and channels
* organs/organelles enclosed in other organs/organelles
* organs/organelles are bounded by a membrane

* elements have ids
* separate styling information (by class/id) for positioning, size, fill/colour etc. (c.f. CSS).

Example
-------

::

    <cell>  # Has a membrane by definition, style to specify shape, colour
      <membrane>
        <transporter id="Na"
      </membrane>
      <cytoplasm>
      </cytoplasm>
    </cell>


    <compartment class="cell-wall" id="cell_1">
      <transporter class="K-channel" id="i_K"/>
      <transporter class="Na-channel" id="i_Na"/>
      <transporter class="ion-channel" id="i_Leak"/>
    </compartment>

    <style>
      .cell_wall {
        shape: rounded-rectangle;
        /* closed-cylinder, rectangle, circle/ellipse */
        /* thickness, size, aspect-ratio, ... */
      }
      #i_Na {
        colour: yellow;
        position: top;
        /* symbol, ... */
      }
      #i_K {
        colour: lilac;
        position: top;
      }
      #i_Leak {
        colour: orange;
        position: bottom;
      }
    </style>


* https://models.physiomeproject.org/workspace/chang_fujita_b_1999/file/d9a44ca71a03bb5cf4865a58dc59f18baa19c05c/chang_1999b.svg

* https://models.physiomeproject.org/workspace/warren_tawhai_crampin_2009/file/7a277ddc5b1acbb9c6dde1189df14d614a0be6e7/warren_2010.svg

* http://sites.bioeng.auckland.ac.nz/mwu035/mpb/

* Transporters: https://en.wikipedia.org/wiki/Membrane_transport_protein and https://en.wikipedia.org/wiki/Transporter_Classificatquantity_Database


Implementation
--------------

Symbol library
~~~~~~~~~~~~~~

* ./membrane/cell-wall.svg
* ./transporter/K-channel.svg
* ./transporter/Na-channel.svg
* ./transporter/ion-channel.svg

Python pacakges
~~~~~~~~~~~~~~~

* lxml
* tinycss2
* cssselect

SVG components
~~~~~~~~~~~~~~

* segment::

          O
          ||
           O

..

* segment:
    * has width and height.
    * origin is top left corner?
    * has coords of rotational centre.
    * has coords of top right corner?
    * but when rotated corners change, so maybe origin is at rotational centre and then have coords of attachment points??
    * label attachement points `A, B, C, ...` and then specify connections as `A` to `B` etc.
* generate horizontal membrane pieces with arbitrary number of segments.
* generate vertical membrane pieces with arbitrary number of segments.
* generate membrane pieces with arbitrary number of segments and at an arbitrary angle??
* generate quarter circle membrane pieces with a given outer radius? Or number of segments?
    * limited number of solutions
    * piece width/height
* generate circular arc membrane pieces that turn a specified angle. And with a given outer radius? Or number of segments?


Drawing and connecting components
.................................

* Position by specifying location top-left
* Component origin wrt some component it's embedded into. Need parent component.
* `world` coordinate system -- parent = None.
* Can only join two components (at a connector) if each can resolve origin to 'world'
* alignment of connector edges
* Connector local information ((x1, y1), (x2, y2)) wrt local origin
* `Diagram` class contains componentsl a diagram's co-ord system.
* `place` components into a diagram.

Other
.....

* Translate elements so that their local coordinate origin is at the element's centre. Then
  rotation will preserve symmetry.
* Scale (by 1/5.6) so that membrane marker spacing is unity.

