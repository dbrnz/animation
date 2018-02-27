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

import pyparsing as pp
import networkx as nx

#------------------------------------------------------------------------------

from . import bondgraph as bg
from . import diagram as dia

#------------------------------------------------------------------------------

DEFAULT_OFFSET           = (50, 'gx')
POSITION_QUANTITY_OFFSET = (20, 'gx')
FLOW_TRANSPORTER_OFFSET  = (20, 'gx')

TRANSPORTER_SPACING      = (20, 'l')

#------------------------------------------------------------------------------

class Grammer(object):
    '''
    >>> position.parseString("left")
    ([(['', 'left'], {})], {})

    >>> position.parseString("right #Ca-b, #Ca-t; 10 below #NKE, #K1")
    ([(['', 'right', 'Ca-b', 'Ca-t'], {}), ([(10.0, 'l'), 'below', 'NKE', 'K1'], {})], {})

    >>> position.parseString("(10,)")
    ([(10.0, 'l')], {})

    >>> position.parseString("(10gy, 2.5)")
    ([(10.0, 'gy'), (2.5, 'l')], {})

    >>> position.parseString("(,10)")
    ([',', (10.0, 'l')], {})


    * What about `100 X; 200 Y` == `(100, 200)` ???
    * This would allow `100 X; 50 above #q3`
    * But could do this with `100 right #cell; 50 above #q3`
    '''

    number = pp.Word(pp.nums)
    plusminus = pp.Literal('+') | pp.Literal('-')
    integer = pp.Combine(pp.Optional(plusminus) + number)
    realnumber = pp.Combine(integer + pp.Optional(pp.Literal('.') + pp.Optional(number)))

    # 'l' units depend on element's container
    # 'g' units depend on diagram
    local_global = pp.Literal('l') | pp.Literal('g')
    xy_units = pp.Literal('x') | pp.Literal('y')
    pixel_units = pp.Literal('px')
    units = pp.Combine(xy_units | local_global + pp.Optional(xy_units) | pixel_units) + pp.White().suppress()
    length = pp.Group(realnumber + pp.Optional(units, 'l')).setParseAction( lambda s,l,t: [ (float(t[0][0]), t[0][1]) ] )

    relation = (pp.Keyword('top') | pp.Keyword('bottom')
              | pp.Keyword('left') | pp.Keyword('right')
              | pp.Keyword('above') | pp.Keyword('below')
              | pp.Keyword('centre') | pp.Keyword('center'))

    name = pp.Word(pp.alphas, '_' + '-' + '/' + pp.alphanums)
    identifier = pp.Suppress(pp.Literal('#')) + name
    id_list = pp.delimitedList(identifier)

    relative_position = pp.Group(pp.Optional(length, '') + relation + pp.Optional(id_list))
    relative_position_list = pp.delimitedList(relative_position, ';')

    numeric_coords = (length + pp.Optional(',').suppress() + length)
    coord_pair = pp.Suppress('(') + numeric_coords + pp.Suppress(')')

    absolute_position = coord_pair
    position = (relative_position_list | absolute_position) + pp.StringEnd()

    # Size
    size = coord_pair

    # Line segments
    angle = realnumber
    cond = pp.Keyword('until')

    #pp.Keyword('for')

    line_segment = pp.Group(angle + cond + relative_position)
    line_segment_list = pp.delimitedList(line_segment, ';')
    #"-120 until left #u16, #v5; 180 until left #NCE;"/>

#------------------------------------------------------------------------------

HORIZONTAL_RELN  = ['left', 'right']
VERTICAL_RELN    = ['top', 'bottom', 'above', 'below']
CENTERED_RELN    = ['centre', 'center']

TRANSPORTER_SIDE = ['top', 'bottom', 'left', 'right']

#------------------------------------------------------------------------------

class Position(object):
    def __init__(self, element, text):
        self._element = element
        self._lengths = None
        self._relationships = list()
        self._coords = [None, None]
        self._dependencies = set()  # of ids and elements
        if (isinstance(element, dia.Compartment)   # A compartment's position and size is always in terms of its container
         or isinstance(element, dia.Transporter)): # A transporter's position always depends on its compartment
            self._dependencies.add(element.container)

        if text:
            try:
                tokens = Grammer.position.parseString(text.strip())
            except pp.ParseException as msg:
                raise SyntaxError("Invalid syntax for 'pos': {}".format(text))
            if isinstance(tokens[0], tuple):
                self._lengths = tuple(tokens)
                if isinstance(element, bg.Potential):
                    self._dependencies.add(element.quantity.container)
                elif isinstance(element, bg.Flow) and element.transporter:
                    self._dependencies.add(element.transporter.container)
                else:
                    self._dependencies.add(element.container)
            elif isinstance(tokens[0], pp.ParseResults):
                if len(tokens) > 2:
                    raise SyntaxError("Cannot have more than two positioning statements")
                (have_x, have_y) = (False, False)
                t_relns = [t[1] for t in tokens if len(t) == 2]
                for t in tokens:
                    reln = t[1]
                    if (have_x and reln in HORIZONTAL_RELN
                     or have_y and reln in VERTICAL_RELN
                     or (have_x or have_y) and reln in CENTERED_RELN):
                        raise SyntaxError("Position has multiple constraints for same direction")
                    if   reln in HORIZONTAL_RELN: have_x = True
                    elif reln in VERTICAL_RELN: have_y = True
                    if isinstance(self._element, dia.Transporter):
                        if len(t_relns) != 1 or t_relns[0] not in TRANSPORTER_SIDE:
                            raise SyntaxError("No side given for transporter")
                        if len(t) == 2 and isinstance(t[0], tuple):
                            if len(tokens) > 1:
                                raise SyntaxError("Multiple offsets for transporter postion")
                    elif reln in ['top', 'bottom']:
                        raise SyntaxError("Element cannot have side position")

                    dependencies = t[2:]
                    if not any(dependencies):
                        if isinstance(element, bg.Potential):
                            dependencies = [element.quantity.container]
                        elif isinstance(element, bg.Flow) and element.transporter:
                            dependencies = [element.transporter]
                    self._dependencies.update(dependencies)
                    self._relationships.append((t[0] if t[0] else None, reln, dependencies))

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

    _orientation = { 'centre': -1, 'center': -1, 'left': 0, 'right': 0, 'above': 1, 'below': 1 }

    def _resolve_point(self, diagram, unit_converter, offset, reln, dependencies):
        '''
        :return: tuple(tuple(x, y), orientation) where orientation == 0 means
                 horizontal and 1 means vertical.
        '''
        # find average position of dependencies
        dependency = None
        coords = [0.0, 0.0]
        for dependency in dependencies:
            if isinstance(dependency, str):
                id = dependency
                dependency = diagram.find_element(id)
            if dependency is None or not dependency.position.resolved:
                raise ValueError("No position for '{}' element".format(dependency))
            coords[0] += dependency.position.coords[0]
            coords[1] += dependency.position.coords[1]
        coords[0] /= len(dependencies)
        coords[1] /= len(dependencies)

        if not offset:
            if dependency is not None:
                if (isinstance(self._element, bg.Potential) # and isinstance(dependency, dia.Quantity)
                 or isinstance(self._element, dia.Quantity)): # and isinstance(dependency, bg.Potential)):
                    offset = POSITION_QUANTITY_OFFSET
                elif (isinstance(self._element, bg.Flow) and isinstance(dependency, dia.Transporter)
                   or isinstance(self._element, dia.Transporter) and isinstance(dependency, bg.Flow)):
                    offset = FLOW_TRANSPORTER_OFFSET
                elif isinstance(self._element, dia.Transporter):
                    offset = TRANSPORTER_SPACING
                else:
                    offset = DEFAULT_OFFSET
            elif isinstance(self._element, dia.Transporter):
                offset = TRANSPORTER_SPACING
            else:
                offset = DEFAULT_OFFSET

        orientation = Position._orientation[reln]
        if orientation >= 0:
            adjust = unit_converter.pixels(offset, orientation+1, False)
        if   reln == 'left':  coords[0] -= adjust
        elif reln == 'right': coords[0] += adjust
        elif reln == 'above': coords[1] -= adjust
        elif reln == 'below': coords[1] += adjust

        return (tuple(coords), orientation)

    def resolve(self, diagram):
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

        elif None in self._coords and self._relationships:
            if len(self._relationships) == 1:
                offset = self._relationships[0][0]
                reln = self._relationships[0][1]
                dependencies = self._relationships[0][2]
                if isinstance(self._element, dia.Transporter):
                    if reln in ['bottom', 'right']:
                        dirn = 'below' if reln in ['top', 'bottom'] else 'right'
                        (coords, orientation) = self._resolve_point(diagram, unit_converter,
                                                                    (1000, 'l'), dirn, [self._element.container])
                        self._coords[orientation] = coords[orientation]
                    dirn = 'right' if reln in ['top', 'bottom'] else 'below'
                    (coords, orientation) = self._resolve_point(diagram, unit_converter,
                                                                offset, dirn, [self._element.container])
                    if reln in ['bottom', 'right']: self._coords[orientation] = coords[orientation]
                    else:                           self._coords = coords
                else:
                    (coords, orientation) = self._resolve_point(diagram, unit_converter,
                                                                offset, reln, dependencies)
                    self._coords = coords
            else:
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
                        (coords, orientation) = self._resolve_point(diagram, unit_converter,
                                                                    offset, reln, dependencies)
                        self._coords[orientation] = coords[orientation]

#------------------------------------------------------------------------------

class Size(object):
    def __init__(self, text):
        self._lengths = None
        if text:
            try:
                tokens = Grammer.position.parseString(text.strip())
            except pp.ParseException as msg:
                raise SyntaxError("Invalid syntax for 'size': {}".format(text))
            self._lengths = tuple(tokens)

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
            if units[0] == 'g':
                if   'x' in units or dimension == 1:
                    return length[0]*self._global_size[0]/1000.0
                elif 'y' in units or dimension == 2:
                    return length[0]*self._global_size[1]/1000.0
            elif units[0] in ['l', 'x', 'y']:
                if   'x' in units or dimension == 1:
                    return (self._local_offset[0] if add_offset else 0) + length[0]*self._local_size[0]/1000.0
                elif 'y' in units or dimension == 2:
                    return (self._local_offset[1] if add_offset else 0) + length[0]*self._local_size[1]/1000.0
            elif units == 'px':
                return length[0]

    def pixel_pair(self, coords, add_offset=True):
        return tuple(self.pixels(l, (n+1), add_offset) for n, l in enumerate(coords))

#------------------------------------------------------------------------------

def position_diagram(diagram):
    # Build a dependency graph
    g = nx.DiGraph()

    # We want all elements that have a position; some may not have an id
    for e in diagram.elements:
        if e.position: g.add_node(e)

    # Add dependency edges
    for e in list(g):
        for dependency in e.position.dependencies:
            if isinstance(dependency, str):
                id = dependency
                dependency = diagram.find_element(id)
                if dependency is None:
                    raise KeyError('Unknown element id: {}'.format(id))
            g.add_edge(dependency, e)

    diagram.set_unit_converter(UnitConverter(diagram.pixel_size, diagram.pixel_size))
    for e in nx.topological_sort(g):
        if e != diagram:
            e.position.resolve(diagram)
            if isinstance(e, dia.Compartment):
                e.set_pixel_size(e.container.unit_converter.pixel_pair(e.size.lengths, False))
                e.set_unit_converter(UnitConverter(diagram.pixel_size, e.pixel_size, e.position.coords))

#   write_dot(g, 'cell.dot')
    from matplotlib import pyplot as plt
    from networkx.drawing.nx_agraph import graphviz_layout, write_dot
    pos = graphviz_layout(g, prog='neato')
    nx.draw(g, pos, labels={e: e.id for e in diagram.elements if e in g})
    plt.show()

    return g

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

