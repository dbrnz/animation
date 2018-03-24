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

import math

#------------------------------------------------------------------------------

from . import bondgraph as bg
from . import diagram as dia
from . import parser

#------------------------------------------------------------------------------

# These could come from stylesheet

QUANTITY_OFFSET = (60, 'x')
FLOW_OFFSET = (60, 'x')

TRANSPORTER_EXTRA = (25, 'x')

# SVG sizes, in pixels
ELEMENT_RADIUS = 15

QUANTITY_WIDTH = 40
QUANTITY_HEIGHT = 30

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
        return self._coords is not None and None not in self._coords

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

    def parse(self, tokens, default_offset, default_dependency):
        """
        * Position as coords: absolute or % of container -- `(100, 300)` or `(10%, 30%)`
        * Position as offset: relation with absolute offset from element(s) -- `300 above #q1 #q2`
        """
        element_dependencies = []
        token = tokens.peek()
        if token.type == '() block':
            tokens.next()
            lengths = parser.get_coordinates(parser.StyleTokens(token.content))
            self.set_lengths(lengths)
        else:
            seen_horizontal = False
            seen_vertical = False
            constraints = 0
            while token is not None:
                using_default = token.type not in ['number', 'dimension', 'percentage']
                offset = parser.get_length(tokens, default=default_offset)
                token = tokens.next()
                if (token.type != 'ident'
                 or token.lower_value not in POSITION_RELATIONS):
                    raise SyntaxError("Unknown relationship for position.")
                reln = token.lower_value
                dependencies = []
                token = tokens.peek()
                if token in [None, ','] and default_dependency is not None:
                    dependencies.append(default_dependency)
                elif token is not None and token.type != 'hash' and token != ',':
                    raise SyntaxError("Identifier(s) expected")
                elif token is not None:
                    tokens.next()   # We peeked above...
                    while token is not None and token.type == 'hash':
                        dependency = self._element.diagram.find_element('#' + token.value)
                        if dependency is None:
                            raise KeyError("Unknown element '#{}".format(token.value))
                        dependencies.append(dependency)
                        token = tokens.next()
                if token == ',':
                    constraints += 1
                    if (seen_horizontal and reln in HORIZONTAL_RELATIONS
                     or seen_vertical and reln in VERTICAL_RELATIONS):
                        raise SyntaxError("Constraints must have different directions.")
                if using_default and constraints >= 1:
                    # No default offsets if there will be two (or more) constraints
                    offset = None
                self.add_relationship(offset, reln, dependencies)
                element_dependencies.extend(dependencies)
                seen_horizontal = reln in HORIZONTAL_RELATIONS
                seen_vertical = reln in VERTICAL_RELATIONS
                if token == ',':
                    token = tokens.peek()
                    continue
                elif tokens.peek() is None:
                    break
                else:
                    raise SyntaxError("Invalid syntax")
        self.add_dependencies(element_dependencies)

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
                self._lengths = parser.get_coordinates(parser.StyleTokens(token.content))
            else:
                raise SyntaxError("Parenthesised pair of lengths expected.")

    @property
    def lengths(self):
        return self._lengths

#------------------------------------------------------------------------------


class Line(object):

    def __init__(self, element, tokens):
        self._element = element
        self._tokens = tokens
        self._segments = []

    def parse(self):
        """
        <line-point> ::= <coord-pair> | <line-angle> <constraint>
        <coord-pair> ::= '(' <length> ',' <length> ')'
        <constraint> ::= ('until-x' | 'until-y') <relative-point>
        <relative-point> ::= <id-list> | [ <offset> <reln> ] <id-list>

        """
        # "210 until-x #u16 #v5, -90 until-y #NCE"
        if self._tokens is None:
            return
        self._segments = []
        tokens = self._tokens
        token = tokens.peek()
        while token is not None:
            angle = parser.get_number(tokens) if token.type == 'number' else None
            # Normalise angle...
            token = tokens.next()
            if (token is None
             or token.type != 'ident'
             or token.lower_value not in ['until', 'until-x', 'until-y']):
                raise SyntaxError("Unknown constraint for curve segment.")
            if angle is None and token.lower_value in ['until-x', 'until-y']:
                raise SyntaxError("Angle expected.")
            elif angle is not None and token.lower_value == 'until':
                raise SyntaxError("Unexpected angle.")
            constraint = (-1 if token.lower_value == 'until-x'
                      else 1 if token.lower_value == 'until-y'
                      else 0)
            # Check that angle != +/-90 if until-x
            # Check that angle != 0/180 if until-y
            token = tokens.peek()
            if token.type == '() block':
                offset = parser.get_coordinates(parser.StyleTokens(token.content), allow_local=False)
                token = tokens.next()
                if token.type != 'ident' or token.lower_value != 'from':
                    raise SyntaxError("'from' expected.")
                token = tokens.next()
            elif token.type in ['number', 'dimension']:
                length = parser.get_length(tokens)
                token = tokens.next()
                if (token.type != 'ident'
                 or token.lower_value not in POSITION_RELATIONS):
                    raise SyntaxError("Unknown relationship for offset.")
                reln = token.lower_value
                if reln in HORIZONTAL_RELATIONS:
                    offset = ((length[0] if reln == 'right' else -length[0], length[1]), (0, ''))
                else:   # VERTICAL_RELATIONS
                    offset = ((0, ''), (length[0] if reln == 'right' else -length[0], length[1]))
                token = tokens.next()
            else:
                offset = ((0, ''), (0, ''))
            dependencies = []
            while token is not None and token.type == 'hash':
                dependency = self._element.diagram.find_element('#' + token.value)
                if dependency is None:
                    raise KeyError("Unknown element '#{}".format(token.value))
                dependencies.append(dependency)
                token = tokens.next()
            if not dependencies:
                raise SyntaxError("Identifier(s) expected.")

            if token is not None and token.type == 'ident' and token.lower_value == 'offset':
                token = tokens.next()
                if token.type == '() block':
                    line_offset = parser.get_coordinates(parser.StyleTokens(token.content), allow_local=False)
                    token = tokens.peek()
                else:
                    raise SyntaxError("Offset expected.")
            else:
                line_offset = None

            self._segments.append((angle, constraint, offset, dependencies, line_offset))

            if token not in [None, ',']:
                raise SyntaxError("Invalid syntax")
            token = tokens.peek()

    def points(self, start_pos, flow=None, reverse=False):
        last_pos = start_pos
        points = [start_pos]
        for segment in self._segments:
            angle = segment[0]
            offset = self._element.diagram.unit_converter.pixel_pair(segment[2], add_offset=False)
            end_pos = offset + Position.centroid(segment[3])  # Centre of dependencies
            if segment[1] == -1:   #  until-x
                dx = end_pos[0] - last_pos[0]
                dy = dx*math.tan(angle*math.pi/180)
                end_pos[1] = last_pos[1] - dy
            elif segment[1] == 1:  #  until-y
                dy = last_pos[1] - end_pos[1]
                dx = dy*math.tan((90-angle)*math.pi/180)
                end_pos[0] = last_pos[0] + dx
            if segment[4] is not None:
                line_offset = self._element.diagram.unit_converter.pixel_pair(segment[4], add_offset=False)
                points[-1] += line_offset
                end_pos += line_offset
            points.append(end_pos)
            last_pos = end_pos
        if flow.transporter is not None:
            trans_coords = flow.transporter.coords
            if (trans_coords[0] == points[-1][0]
             or trans_coords[1] == points[-1][1]):
                points[-1] += flow.flux_offset(self._element)
        return points if not reverse else list(reversed(points))

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
