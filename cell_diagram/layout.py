import pyparsing as pp


number = pp.Word(pp.nums)
plusminus = pp.Literal('+') | pp.Literal('-')
integer = pp.Combine(pp.Optional(plusminus) + number)
realnumber = pp.Combine(integer + pp.Optional(pp.Literal('.') + pp.Optional(number)))

units = pp.Combine((pp.Literal('l') | pp.Literal('g')) + pp.Optional('x'))
length = pp.Group(realnumber + pp.Optional(units, 'l')).setParseAction( lambda s,l,t: [ (float(t[0][0]), t[0][1]) ] )

relation = (pp.Keyword('top') | pp.Keyword('bottom')
          | pp.Keyword('left') | pp.Keyword('right')
          | pp.Keyword('above') | pp.Keyword('below')
          | pp.Keyword('middle'))

name = pp.Word(pp.alphas, '_' + '-' + '/' + pp.alphanums)
identifier = pp.Suppress(pp.Literal('#')) + name
id_list = pp.delimitedList(identifier)

relative_position = pp.Group(pp.Optional(length, '') + relation + pp.Optional(id_list, ''))
relative_position_list = pp.delimitedList(relative_position, ';')

numeric_coords = ((length + pp.Optional(',').suppress() + length)
                | (length + pp.Optional(',').suppress())
                | (',' + length))
absolute_position = pp.Suppress('(') + numeric_coords + pp.Suppress(')')

position = relative_position_list | absolute_position


angle = realnumber

cond = pp.Keyword('until')

#pp.Keyword('for')

line_segment = pp.Group(angle + cond + relative_position)
line_segment_list = pp.delimitedList(line_segment, ';')
#"-120 until left #u16, #v5; 180 until left #NCE;"/>

#try:
#    return parser.parseString(s)
#except pp.ParseException(msg):
#    raise SyntaxError(msg)
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




def layout_container(container, geometry):
    for component in container.components:
        if isinstance(component, Compartment):
            layout_compartment(compenent, geometry)
        elif isinstance(component, Quantity):
            component.set_geometry(geo.Point(x, y))
        else:
            pass

def layout_compartment(compartment, geometry):
    # compartment membrane... (box() ??)
    for transporter in compartment.transporters:
        pass
    layout_container(compartment, geometry)

def layout_diagram(diagram, geometry):
    diagram.set_geometry(geo.box())  # origin, width, height
    layout_container(diagram, geometry)
'''

