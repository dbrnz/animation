#------------------------------------------------------------------------------
#
#  Cell Diagramming Language
#
#  Copyright (c) 2018  David Brooks
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
#------------------------------------------------------------------------------

from . import bondgraph as bg
from . import diagram as dia
from . import parser

#------------------------------------------------------------------------------

QUANTITY_OFFSET = (40, 'x')
FLOW_OFFSET = (40, 'x')

#------------------------------------------------------------------------------

HORIZONTAL_RELN  = ['left', 'right']
VERTICAL_RELN    = ['above', 'below']
POSITION_RELATIONS = HORIZONTAL_RELN + VERTICAL_RELN

COMPARTMENT_BOUNDARIES = ['top', 'bottom', 'left', 'right',
                          'top-left', 'top-right',
                          'bottom-left', 'bottom-right']

#------------------------------------------------------------------------------

class Position(object):
    def __init__(self, element):
        self._element = element
        self._lengths = None
        self._relationships = list()
        self._coords = [None, None]
        self._dependencies = set()  # of ids and elements

    def __bool__(self):
        return bool(self._dependencies) or bool(self._lengths)

    @property
    def coords(self):
        return tuple(self._coords)

    @property
    def dependencies(self):
        return self._dependencies

    @property
    def has_coords(self):
        return None not in self._coords

    @property
    def resolved(self):
        return None not in self._coords

    def add_dependencies(self, dependencies):
        self._dependencies.update(dependencies)

    def add_dependency(self, dependency):
        self._dependencies.add(dependency)

    def add_relationship(self, offset, relation, dependencies):
        self._relationships.append((offset, relation, dependencies))

    def set_coords(self, coords):
        self._coords = coords

    def set_lengths(self, lengths):
        self._lengths = lengths

    _orientation = { 'centre': -1, 'center': -1, 'left': 0, 'right': 0, 'above': 1, 'below': 1 }

    @staticmethod
    def centroid(dependencies):
        # find average position of dependencies
        coords = [0.0, 0.0]
        for dependency in dependencies:
            if not dependency.position.resolved:
                raise ValueError("No position for '{}' element".format(dependency))
            coords[0] += dependency.position.coords[0]
            coords[1] += dependency.position.coords[1]
        coords[0] /= len(dependencies)
        coords[1] /= len(dependencies)
        return coords

    def _resolve_point(self, unit_converter, offset, reln, dependencies):
        '''
        :return: tuple(tuple(x, y), orientation) where orientation == 0 means
                 horizontal and 1 means vertical.
        '''
        coords = self.centroid(dependencies)
        orientation = Position._orientation[reln]
        if orientation >= 0:
            adjust = unit_converter.pixels(offset, orientation+1, False)
        if   reln == 'left':  coords[0] -= adjust
        elif reln == 'right': coords[0] += adjust
        elif reln == 'above': coords[1] -= adjust
        elif reln == 'below': coords[1] += adjust
        return (tuple(coords), orientation)

    def resolve(self):
        '''
        # Transporters are always on a compartment boundary
        pos="100 top"    ## x = x(compartment) + 100; y = y(compartment)
        pos="bottom"     ## y = y(compartment) + height(compartment)

        pos="100 top"    ## same as pos="100 right #compartment"
        pos="100 bottom" ## same as pos="100 right #compartment; 1000 below #compartment"

        pos="top; 10 right #t1"    ## same as pos="0 below #compartment; 10 right #t1"
        pos="right; 10 below #t2"  ## same as pos="1000 right #compartment; 10 below #t2"

        pos="top; 10 above/below #t1"  ## ERROR: multiple `y` constraints
        pos="left; 10 left/right #t1"  ## ERROR: multiple `y` constraints
        pos="10 right; 10 below #t2"   ## ERROR: multiple `y` constraints
        pos="5 left #t1; 100 bottom"   ## ERROR: multiple `x` constraints

        # FUTURE: Autopositioning
        pos="top"  # default is top  }
        pos="top"  #                 } Centered in top, spaced evenly (`transporter-spacing`?)
        pos="top"  #                 }
        '''

        unit_converter = self._element.container.unit_converter

        if self._lengths:
            print(self._element.container, self._element, self._lengths, self._coords)
            self._coords = unit_converter.pixel_pair(self._lengths)

        elif None in self._coords and self._relationships:
            if len(self._relationships) == 1:
                # Have just a single constraint
                offset = self._relationships[0][0]
                reln = self._relationships[0][1]
                dependencies = self._relationships[0][2]
                if isinstance(self._element, dia.Transporter):
                    if reln in ['bottom', 'right']:
                        dirn = 'below' if reln in ['top', 'bottom'] else 'right'
                        (coords, orientation) = self._resolve_point(unit_converter,
                                                                    (100, '%'), dirn, [self._element.container])
                        self._coords[orientation] = coords[orientation]
                    dirn = 'right' if reln in ['top', 'bottom'] else 'below'
                    (coords, orientation) = self._resolve_point(unit_converter,
                                                                offset, dirn, [self._element.container])
                    if reln in ['bottom', 'right']: self._coords[orientation] = coords[orientation]
                    else:                           self._coords = coords
                else:
                    self._coords, _ = self._resolve_point(unit_converter,
                                                          offset, reln, dependencies)
            else:
                # Have both horizontal and vertical constraints
                for relationship in self._relationships:
                    offset = relationship[0]
                    reln = relationship[1]
                    dependencies = relationship[2]
                    if isinstance(self._element, dia.Transporter):
## TODO
##        pos="top; 10 right #t1"    ## same as pos="0 below #compartment; 10 right #t1"
##        pos="right; 10 below #t2"  ## same as pos="1000 right #compartment; 10 below #t2"
                        pass
                    else:
                        (coords, orientation) = self._resolve_point(unit_converter,
                                                                    offset, reln, dependencies)
                        orientation = orientation - 1  # Swap meaning
                        self._coords[orientation] = coords[orientation]

#------------------------------------------------------------------------------


class Size(object):
    def __init__(self, tokens):
        self._lengths = None
        for token in parser.StyleTokens(tokens):
            if token.type == '() block':
                self._lengths, _ = parser.get_coordinates(parser.StyleTokens(token.content))
            else:
                raise SyntaxError("Parenthesised pair of lengths expected.")

    @property
    def lengths(self):
        return self._lengths

#------------------------------------------------------------------------------


class UnitConverter(object):
    def __init__(self, global_size, local_size, local_offset=(0, 0)):
        '''
        :param global_size: tuple(width, height) of diagram, in pixels
        :param local_size: tuple(width, height) of current container, in pixels
        :param local_offset: tuple(x_pos, y_pos) of current container, in pixels
        '''
        self._global_size = global_size
        self._local_size = local_size
        self._local_offset = local_offset

    def __str__(self):
        return 'UC: global={}, local={}, offset={}'.format(self._global_size, self._local_size, self._local_offset)

    def pixels(self, length, dimension, add_offset=True):
        if length is not None:
            units = length[1]
            if units.startswith('%'):
                if   'x' in units or ('y' not in units and dimension == 1):
                    offset = length[0]*self._local_size[0]/100.0
                elif 'y' in units or ('x' not in units and dimension == 2):
                    offset = length[0]*self._local_size[1]/100.0
                if dimension == 1:
                    return (self._local_offset[0] if add_offset else 0) + offset
                else:
                    return (self._local_offset[1] if add_offset else 0) + offset
            else:
                if   'x' in units or ('y' not in units and dimension == 1):
                    return length[0]*self._global_size[0]/1000.0
                elif 'y' in units or ('x' not in units and dimension == 2):
                    return length[0]*self._global_size[1]/1000.0
        return 0

    def pixel_pair(self, coords, add_offset=True):
        return tuple(self.pixels(l, (n+1), add_offset) for n, l in enumerate(coords))

#------------------------------------------------------------------------------


if __name__ == "__main__":
    import doctest
    doctest.testmod()

#------------------------------------------------------------------------------

'''

import shapely.geometry as geo
import shapely.affinity as affine

layout diagram == assigning geometry

compartment by compatment, starting with innermost ones ==> want reverse compartment/container order.

laying out a compartment:
 * boundary --> geo.Polygon
 * transporters --> geo.Point
 * interior quantities --> geo.Point

geo.MultiPoint, geo.MultiLineString, geo.MultiPolygon

geo.GeometryCollection

Compartments scaled when placed in a containing compartment.

'''

