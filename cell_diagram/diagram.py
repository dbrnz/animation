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

# -----------------------------------------------------------------------------

from . import layout
from .element import Element

# -----------------------------------------------------------------------------


class Container(Element):
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

    def set_pixel_size(self, pixel_size):
        (self._width, self._height) = pixel_size

    def set_unit_converter(self, unit_converter):
        self._unit_converter = unit_converter

    def add_component(self, component):
        self._components.append(component)

    def svg(self):
        # Put everything into a group with id and class attributes
        svg = ['<g{}>'.format(self.id_class())]
        if self.position.has_coords:
            top_left = self.position.coords
            bottom_right = (top_left[0] + self._width,
                            top_left[1] + self._height)
            svg.append(('<path fill="#eeeeee" stroke="#222222"'
                        ' stroke-width="2.0" opacity="0.6"'
                        ' d="M{left:g},{top:g} L{right:g},{top:g}'
                        ' L{right:g},{bottom:g} L{left:g},{bottom:g} z"/>')
                       .format(left=top_left[0], right=bottom_right[0],
                               top=top_left[1], bottom=bottom_right[1]))
        for component in self._components:
            svg.extend(component.svg())
        svg.append('</g>')
        return svg

# -----------------------------------------------------------------------------


class Diagram(Container):
    def __init__(self, **kwds):
        super().__init__(None, class_name='Diagram', **kwds)
        self._elements = list()
        self._elements_by_id = OrderedDict()
        self._layout = None
        self._width = float(self.style.get('width', 0)
                            if self.style is not None else 0)
        self._height = float(self.style.get('height', 0)
                            if self.style is not None else 0)

    @property
    def elements(self):
        return self._elements

    @property
    def height(self):
        return self._height

    @property
    def width(self):
        return self._width

    def add_element(self, element):
        self._elements.append(element)
        if element.id is not None:
            self._elements_by_id[element.id] = element

    def find_element(self, id, cls=Element):
        e = self._elements_by_id.get(id)
        return e if e is not None and isinstance(e, cls) else None

    def position_elements(self):
        layout.position_diagram(self)

    def svg(self, bond_graph):
        svg = ['<?xml version="1.0" encoding="UTF-8"?>']
        svg.append(('<svg xmlns="http://www.w3.org/2000/svg"'
                    ' xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1"'
                    ' viewBox="0 0 {:g} {:g}">')
                   .format(self._width, self._height))
# # Add <def>s for common shapes??
        svg.extend(super().svg())
        if bond_graph is not None:
            svg.extend(bond_graph.svg())
        svg.append('</svg>')
        return '\n'.join(svg)

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

    def svg(self):
        svg = super().svg()
        for transporter in self._transporters:
            svg.extend(transporter.svg())
        return svg

# -----------------------------------------------------------------------------


class Quantity(Element):
    def __init__(self, container, **kwds):
        super().__init__(container, class_name='Quantity', **kwds)

    def svg(self):
        return super().svg(stroke='#ff0000', fill='#FF80ff')

# -----------------------------------------------------------------------------


class Transporter(Element):
    def __init__(self, container, **kwds):
        super().__init__(container, class_name='Transporter', **kwds)

    def svg(self):
        return super().svg(stroke='#ffff00', fill='#80FFFF')

# -----------------------------------------------------------------------------
