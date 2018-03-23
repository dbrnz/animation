# -----------------------------------------------------------------------------
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
# -----------------------------------------------------------------------------

from collections import OrderedDict

import shapely.geometry as geo
import networkx as nx

# -----------------------------------------------------------------------------

from . import layout
from . import parser
from . import svg_elements
from .element import Element, PositionedElement

# -----------------------------------------------------------------------------


class Container(Element, PositionedElement):
    def __init__(self, container, class_name='Container', **kwds):
        super().__init__(container, class_name=class_name, **kwds)
        self._components = []
        self._unit_converter = None

    @property
    def components(self):
        return self._components

    @property
    def pixel_size(self):
        return (self._width, self._height)

    @property
    def unit_converter(self):
        return self._unit_converter

    @property
    def geometry(self):
        if self._geometry is None and self.position.has_coords:
            self._geometry = geo.box(self.coords[0], self.coords[1],  # Top left corner
                                     self.coords[0] + self._width,    # Right
                                     self.coords[1] + self._height)   # Bottom
        return self._geometry

    def set_pixel_size(self, pixel_size):
        (self._width, self._height) = pixel_size

    def set_unit_converter(self, unit_converter):
        self._unit_converter = unit_converter

    def add_component(self, component):
        self._components.append(component)
        ## Keep name directory...

    def svg(self):
        # Put everything into a group with id and class attributes
        svg = ['<g {}>'.format(self.id_class())]
        if self.position.has_coords:
            svg.append('<g transform="translate({:g}, {:g})">'.format(*self.position.coords))
            element_class = self.get_style_as_string('svg-element')
            if element_class in dir(svg_elements):
                id = self._id[1:] if self._id else ''
                element = svg_elements.__dict__.get(element_class)(id, self._width, self._height)
                svg.append(element.svg())
                # We need to set membrane earlier so can use adjusted width/height
                # and membrane.thickness for transporter/flow offset (which becomes
                # specific to compartment).
            elif not isinstance(self, Diagram):
                svg.append(('<path fill="#eeeeee" stroke="#222222"'
                            ' stroke-width="2.0" opacity="0.6"'
                            ' d="M0,0 L{right:g},0'
                            ' L{right:g},{bottom:g} L0,{bottom:g} z"/>')
                           .format(right=self._width, bottom=self._height))
            svg.append('</g>')
        for component in self._components:
            svg.extend(component.svg())
        svg.append('</g>')
        return svg

# -----------------------------------------------------------------------------


class Compartment(Container):
    def __init__(self, container, **kwds):
        super().__init__(container, class_name='Compartment', **kwds)
        self._size = layout.Size(self.style.get('size', None)
                                 if self.style is not None else None)
        self._transporters = []

    @property
    def size(self):
        return self._size

    @property
    def transporters(self):
        return self._transporters

    def add_transporter(self, transporter):
        self._transporters.append(transporter)

    def parse_geometry(self):
        """
        * Compartment size/position: absolute or % of container -- `(100, 300)` or `(10%, 30%)`
        """
        lengths = None
        for token in self._position_tokens:
            if token.type == '() block' and lengths is None:
                lengths = parser.get_coordinates(parser.StyleTokens(token.content))
            elif lengths is not None:
                raise SyntaxError("Position already defined.")
        self._position.set_lengths(lengths)
        # A compartment's position and size is always in terms of its container
        self._position.add_dependency(self.container)


    def svg(self):
        svg = super().svg()
        for transporter in self._transporters:
            svg.extend(transporter.svg())
        return svg

# -----------------------------------------------------------------------------


class Quantity(Element, PositionedElement):
    def __init__(self, container, **kwds):
        self._potential = None
        super().__init__(container, class_name='Quantity', **kwds)

    def set_potential(self, potential):
        self._potential = potential

    def parse_geometry(self):
        PositionedElement.parse_geometry(self, default_offset=self.diagram.quantity_offset,
                                               default_dependency=self._potential)

    def svg(self):
        svg = ['<g{}{}>'.format(self.id_class(), self.display())]
        if self.position.has_coords:
            (x, y) = self.coords
            svg.append(('  <rect rx="10.0" ry="10" x="{:g}" y="{:g}"'
                        ' width="40" height="30" stroke="none" fill="{:s}"/>')
                       .format(x-20, y-15, self.colour))
            svg.append('  <text x="{:g}" y="{:g}">{:s}</text>'
                       .format(x-9, y+6, self._local_name))
        svg.append('</g>')
        return svg

# -----------------------------------------------------------------------------


class Transporter(Element, PositionedElement):
    def __init__(self, container, **kwds):
        super().__init__(container, class_name='Transporter', **kwds)
        self._compartment_side = None
        self._flow = None
        self._width = (10, 'x')   ### From style...

    @property
    def compartment_side(self):
        return self._compartment_side

    @property
    def width(self):
        return self._width

    def parse_geometry(self):
        """
        * Transporter position: side of container along with offset from
          top-right as % of container -- `left 10%`, `top 20%`
        * Transporter position: side of container along with offset from
          another transporter of the compartment which is on the same side
          and with the same orientation, as % of the container
          -- `left 10% below #t1`
        """
        # A transporter's position always depends on its compartment
        dependencies = [self.container]
        tokens = self._position_tokens
        try:
            token = tokens.next()
            if (token.type != 'ident'
             or token.lower_value not in layout.COMPARTMENT_BOUNDARIES):
                raise SyntaxError('Invalid compartment boundary.')
            self._compartment_side = token.lower_value
            offset = parser.get_percentage(tokens)
            token = tokens.peek()
            if token and token.type == 'hash':
                while token.type == 'hash':
                    try:
                        token = tokens.next()
                        dependencies.append('#' + token.value)
                    except StopIteration:
                        break
        except StopIteration:
            raise SyntaxError("Invalid `transporter` position")
## We can (and should ??) now set lengths if no element dependencies
        self._position.add_relationship(offset, self._compartment_side, dependencies)
        self._position.add_dependencies(dependencies)

    def svg(self):
        svg = []
        element_class = self.get_style_as_string('svg-element')
        if element_class in dir(svg_elements):
            svg.append('<g{}{}>'.format(self.id_class(), self.display()))
            id = self._id[1:] if self._id else ''
            element = (svg_elements.__dict__.get(element_class)(
                          id,
                          self.coords,
                          0 if self.compartment_side in layout.HORIZONTAL_BOUNDARIES else 90))
            svg.append(element.svg())
            svg.append('</g>')
        svg.extend(super().svg(stroke='#ffff00'))
        return svg

# -----------------------------------------------------------------------------


class Diagram(Container):
    def __init__(self, **kwds):
        super().__init__(self, class_name='Diagram', **kwds)
        self._elements = list()
        self._elements_by_id = OrderedDict()
        self._elements_by_name = OrderedDict()
        self._layout = None
        self._width = self._number_from_style('width', 0)
        self._height = self._number_from_style('height', 0)
        self._flow_offset = self._length_from_style('flow-offset', layout.FLOW_OFFSET)
        self._quantity_offset = self._length_from_style('quantity-offset', layout.QUANTITY_OFFSET)
        self._bond_graph = None

    def _length_from_style(self, name, default):
        if self.style and name in self.style:
            value = parser.get_length(parser.StyleTokens(self.style.get(name)))
            return value
        return default

    def _number_from_style(self, name, default):
        if self.style and name in self.style:
            value = parser.get_number(parser.StyleTokens(self.style.get(name)))
            return value
        return default

    @property
    def bond_graph(self):
        return self._bond_graph

    @property
    def elements(self):
        return self._elements

    @property
    def height(self):
        return self._height

    @property
    def width(self):
        return self._width

    @property
    def flow_offset(self):
        return self._flow_offset

    @property
    def quantity_offset(self):
        return self._quantity_offset

    def set_bond_graph(self, bond_graph):
        self._bond_graph = bond_graph

    def add_element(self, element):
        self._elements.append(element)
        if element.id is not None:
            if element.id in self._elements_by_id:
                raise KeyError("Duplicate 'id': {}".format(element.id))
            self._elements_by_id[element.id] = element
        self._elements_by_name[element.full_name] = element
        # Also add to element's container

    def find_element(self, id_or_name, cls=Element):
        if id_or_name.startswith('#'):
            e = self._elements_by_id.get(id_or_name)
        else:
            e = self._elements_by_name.get(id_or_name)
        return e if e is not None and isinstance(e, cls) else None

    def layout(self):
        """
        Set positions (and sizes) of all components in the diagram.

        We position and size all compartments before positioning
        other elements.
        """
        self.position.set_coords(layout.Point())

        # Build the dependency graph
        g = nx.DiGraph()
        # We want all elements that have a position; some may not have an id
        for e in self._elements:
            # We now have the diagram's structure so can parse positions
            e.parse_geometry()
            if e.position:
                g.add_node(e)
        # Add edges
        for e in list(g):
            for dependency in e.position.dependencies:
                if isinstance(dependency, str):
                    id_or_name = dependency
                    dependency = self.find_element(id_or_name)
                    if dependency is None:
                        raise KeyError('Unknown element: {}'.format(id_or_name))
                g.add_edge(dependency, e)
        # Now resolve element positions in dependency order
        self.set_unit_converter(layout.UnitConverter(self.pixel_size, self.pixel_size))
        for e in nx.topological_sort(g):
            if e != self and not e.position_resolved:
                e.resolve_position()
                if isinstance(e, Compartment):
                    e.set_pixel_size(e.container.unit_converter.pixel_pair(e.size.lengths, False))
                    e.set_unit_converter(layout.UnitConverter(self.pixel_size, e.pixel_size, e.position.coords))


        # Now that we have element positions we can calculate the offsets
        # of flux lines passing through transporters
        self.bond_graph.set_offsets()

    def svg(self):
        svg = ['<?xml version="1.0" encoding="UTF-8"?>']
        svg.append(('<svg xmlns="http://www.w3.org/2000/svg"'
                    ' xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1"'
                    ' width="{width:g}" height="{height:g}"'
                    ' viewBox="0 0 {width:g} {height:g}">')
                   .format(width=self._width, height=self._height))
        svg.extend(super().svg())
        svg.extend(self.bond_graph.svg())
        svg.append('<defs>')
        svg.extend(svg_elements.DefinesStore.defines())
        svg.append('</defs>')
        svg.append('</svg>')
        return '\n'.join(svg)

# -----------------------------------------------------------------------------
