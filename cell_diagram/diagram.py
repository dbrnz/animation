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

from . import Element

#------------------------------------------------------------------------------

class Container(Element):
    def __init__(self, **kwds):
        super().__init__(**kwds)
        self._components = []

    @property
    def components(self):
        return self._components

    def add_component(self, component):
        self._components.append(component)

    def svg(self):
        svg = []
        if self.position:
            top_left = self.position
            bottom_right = (top_left[0] + self.size[0], top_left[1] + self.size[1])
            svg.append('<path fill="#eeeeee" stroke="#222222" stroke-width="2.0" opacity="0.6"'
                     + ' d="M{left:g},{top:g} L{right:g},{top:g} L{right:g},{bottom:g} L{left:g},{bottom:g} z"/>'
                        .format(left=top_left[0], right=bottom_right[0], top=top_left[1], bottom=bottom_right[1]))
        for component in self._components:
            svg.extend(component.svg())
        return svg

#------------------------------------------------------------------------------

class Diagram(Container):
    def __init__(self, **kwds):
        super().__init__(**kwds)

    def svg(self, bond_graph):
        ##    width = diagram.style.get('width')
        ##    height = diagram.style.get('height')
        self.set_size((1040, 685))  ### TEMP ## MUST come from geometry...
#        if width is None: width = self._pixel_size[0].length
#        if height is None: height = self._pixel_size[1].length


        svg = ['<?xml version="1.0" encoding="UTF-8"?>',
               '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1"'
             + ' viewBox="0 0 {width:g} {height:g}">'.format(width=self.size[0], height=self.size[1])]
        svg.extend(super().svg())
        svg.extend(bond_graph.svg())
        svg.append('</svg>')
        return '\n'.join(svg)

#------------------------------------------------------------------------------

class Compartment(Container):
    def __init__(self, **kwds):
        super().__init__(**kwds)
        self._transporters = []

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

#------------------------------------------------------------------------------

class Quantity(Element):
    def __init__(self, **kwds):
        super().__init__(**kwds)

    def svg(self):
        return['<circle r="5.0" stroke="#ff0000" stroke-width="1.0" fill="#0000FF"'
              + ' cx="{cx:g}" cy="{cy:g}"/>'.format(cx=self.position[0], cy=self.position[1])]

#------------------------------------------------------------------------------

class Transporter(Element):
    def __init__(self, **kwds):
        super().__init__(**kwds)

    def svg(self):
        return['<circle r="5.0" stroke="#ffff00" stroke-width="1.0" fill="#800000" opacity="0.6"'
              + ' cx="{cx:g}" cy="{cy:g}"/>'.format(cx=self.position[0], cy=self.position[1])]

#------------------------------------------------------------------------------

