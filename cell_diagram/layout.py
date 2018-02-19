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
    '''

    number = pp.Word(pp.nums)
    plusminus = pp.Literal('+') | pp.Literal('-')
    integer = pp.Combine(pp.Optional(plusminus) + number)
    realnumber = pp.Combine(integer + pp.Optional(pp.Literal('.') + pp.Optional(number)))

    local_global = pp.Literal('l') | pp.Literal('g')
    xy_units = pp.Literal('x') | pp.Literal('y')
    units = pp.Combine(xy_units | local_global + pp.Optional(xy_units))
    length = pp.Group(realnumber + pp.Optional(units, 'l')).setParseAction( lambda s,l,t: [ (float(t[0][0]), t[0][1]) ] )

    relation = (pp.Keyword('top') | pp.Keyword('bottom')
              | pp.Keyword('left') | pp.Keyword('right')
              | pp.Keyword('above') | pp.Keyword('below')
              | pp.Keyword('middle'))

    name = pp.Word(pp.alphas, '_' + '-' + '/' + pp.alphanums)
    identifier = pp.Suppress(pp.Literal('#')) + name
    id_list = pp.delimitedList(identifier)

    relative_position = pp.Group(pp.Optional(length, '') + relation + pp.Optional(id_list))
    relative_position_list = pp.delimitedList(relative_position, ';')

    numeric_coords = ((length + pp.Optional(',').suppress() + length)
                    | (length + pp.Optional(',', ','))
                    | (',' + length))
    absolute_position = pp.Suppress('(') + numeric_coords + pp.Suppress(')')

    position = (relative_position_list | absolute_position) + pp.StringEnd()

    angle = realnumber

    cond = pp.Keyword('until')

    #pp.Keyword('for')

    line_segment = pp.Group(angle + cond + relative_position)
    line_segment_list = pp.delimitedList(line_segment, ';')
    #"-120 until left #u16, #v5; 180 until left #NCE;"/>

#------------------------------------------------------------------------------

class Position(object):
    def __init__(self):
        self._coords = [None, None]
        self._dependencies = set()  # of ids and elements ???

    @classmethod
    def from_string(cls, s):
        self = cls()
        coords = []
        try:
            for t in Grammer.position.parseString(s.strip()):
                if isinstance(t, pp.ParseResults):
                    self._dependencies.update(t[2:])
                elif isinstance(t, tuple):
                    # 'l' units ==> depend on element's container
                    # 'g' units ==> depend on diagram
                    coords.append(t)
                elif t == ',':
                    coords.append(None)
            if coords:
                self._coords = coords
        except pp.ParseException as msg:
            raise SyntaxError("Invalid syntax for 'pos': {}".format(s))
        return self

    @property
    def coords(self):
        return self._coords

    @property
    def dependencies(self):
        return self._dependencies

    @property
    def has_position(self):
        return None not in self._coords

    def add_dependency(self, id):
        if id: self._dependencies.add(id)

#------------------------------------------------------------------------------

def position_elements(diagram_elements):
  # :param: diagram_elements list of elements in the diagram

    from matplotlib import pyplot as plt

    g = nx.Graph()  ## DiGraph()

    # We want all elements that have a position -- may not have an id...
    element_dict = dict()
    for e in diagram_elements:
        if e.id: element_dict[e.id] = e
        if e.position: g.add_node(e)   ## Or just work with positions??

#    print(element_dict)

    for e in list(g):
        for id in e.position.dependencies:
            if id in element_dict:
                g.add_edge(element_dict[id], e)  # e depends_on node[id]
            else:
                raise KeyError('Unknown element id: {}'.format(id))

#    for e in nx.topological_sort(g):
#        print(e.id, ' ', len(list(g.predecessors(e))))

    nx.draw(g, labels={e: e.id for e in element_dict.values() if e in g})
    plt.show()
    # now for each node with no id

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

