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

HORIZONTAL_RELATIONS = ['left', 'right']
VERTICAL_RELATIONS = ['above', 'below']
POSITION_RELATIONS = (HORIZONTAL_RELATIONS
                    + VERTICAL_RELATIONS)

HORIZONTAL_BOUNDARIES = ['top', 'bottom']
VERTICAL_BOUNDARIES = ['left', 'right']
CORNER_BOUNDARIES = ['top-left', 'top-right',
                     'bottom-left', 'bottom-right']
COMPARTMENT_BOUNDARIES = (HORIZONTAL_BOUNDARIES
                        + VERTICAL_BOUNDARIES)
                        ## + CORNER_BOUNDARIES)   ## FUTURE

#------------------------------------------------------------------------------


class Point(object):
    def __init__(self, x=0.0, y=0.0):
        self._coords = [x, y]

    @property
    def x(self):
        return self._coords[0]

    @property
    def y(self):
        return self._coords[1]

    def __str__(self):
        return "<Point ({:g}, {:g})>".format(*self._coords)

    def __len__(self):
        return 2

    def __add__(self, other):
        return Point(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Point(self.x - other.x, self.y - other.y)

    def __mul__(self, other):
        return Point(other*self.x, other*self.y)

    def __rmul__(self, other):
        return Point(other*self.x, other*self.y)

    def __truediv__(self, other):
        return Point(self.x/other, self.y/other)

    def __itruediv__(self, other):
        return Point(self.x/other, self.y/other)

    def __getitem__(self, key):
        return self._coords[key]

    def __setitem__(self, key, value):
        self._coords[key] = value

    def copy(self):
        return Point(self.x, self.y)

#------------------------------------------------------------------------------


class Position(object):
    def __init__(self, element):
        self._element = element
        self._lengths = None
        self._relationships = list()
        self._coords = None
        self._dependencies = set()  # of ids and elements

    def __bool__(self):
        return bool(self._dependencies) or bool(self._lengths)

    @property
    def coords(self):
        return self._coords

    @property
    def dependencies(self):
        return self._dependencies

    @property
    def has_coords(self):
        return self._coords is not None

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

    _orientation = { 'centre': -1, 'center': -1,
                     'left': 0, 'right': 0,
                     'above': 1, 'below': 1 }

    @staticmethod
    def centroid(dependencies):
        # find average position of dependencies
        coords = Point()
        for dependency in dependencies:
            if not dependency.position.resolved:
                raise ValueError("No position for '{}' element".format(dependency))
            coords += dependency.position.coords
        coords /= len(dependencies)
        return coords

    def _resolve_point(self, unit_converter, offset, reln, dependencies):
        '''
        :return: tuple(tuple(x, y), index) where index == 0 means
                 horizontal and 1 means vertical.
        '''
        coords = self.centroid(dependencies)
        index = Position._orientation[reln]
        if index >= 0:
            adjust = unit_converter.pixels(offset, index, False)
            if reln in ['left', 'above']:
                coords[index] -= adjust
            else: # reln in ['right', 'below']
                coords[index] += adjust
        return (coords, index)

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
            self._coords = unit_converter.pixel_pair(self._lengths)
        elif self._coords is None and self._relationships:
            self._coords = Point()
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
                        (coords, index) = self._resolve_point(unit_converter,
                                                              offset, reln, dependencies)
                        if offset is None:
                            index = index - 1  # Swap meaning
                        self._coords[index] = coords[index]

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

    def pixels(self, length, index, add_offset=True):
        if length is not None:
            units = length[1]
            if 'x' in units: index = 0
            elif 'y' in units: index = 1
            if units.startswith('%'):
                offset = length[0]*self._local_size[index]/100.0
                return ((self._local_offset[index] if add_offset else 0) + offset)
            else:
                return length[0]*self._global_size[index]/1000.0
        return 0

    def pixel_pair(self, coords, add_offset=True):
        return Point(self.pixels(coords[0], 0, add_offset),
                     self.pixels(coords[1], 1, add_offset))

#------------------------------------------------------------------------------


if __name__ == "__main__":
    import doctest
    doctest.testmod()

#------------------------------------------------------------------------------
