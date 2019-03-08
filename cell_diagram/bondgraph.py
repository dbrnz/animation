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

import operator
from collections import OrderedDict

import shapely.geometry as geo

#------------------------------------------------------------------------------

from . import diagram as dia
from . import layout
from . import parser
from .element import Element, PositionedElement
from .svg_elements import svg_line

#------------------------------------------------------------------------------

LINE_OFFSET = 3.5

#------------------------------------------------------------------------------

class BondGraph(Element):
    def __init__(self, diagram, **kwds):
        super().__init__(diagram, class_name='BondGraph', **kwds)
        self._flows = []
        self._potentials = OrderedDict()

    @property
    def flows(self):
        return self._flows

    @property
    def potentials(self):
        return self._potentials

    def add_flow(self, flow):
        self._flows.append(flow)

    def add_potential(self, potential):
        self._potentials[potential] = potential.quantity

    def set_offsets(self):
        for flow in self.flows:
            flow.set_transporter_offsets()

    def svg(self):
        svg = [ ]
        # First draw all lines
        for p, q in self.potentials.items():
            svg.append(svg_line(geo.LineString([p.coords, q.coords]),
                                q.stroke if q.stroke != 'none' else '#808080',
                                display=self.display()))
        # Link potentials via flows and their components
        for flow in self.flows:
            for component in flow.components:
                svg.extend(component.svg())
        # Then symbols
        for p, q in self.potentials.items():
            svg.extend(p.svg())
        for flow in self.flows:
            svg.extend(flow.svg())
        return svg

#------------------------------------------------------------------------------

class Flow(Element, PositionedElement):
    def __init__(self, diagram, transporter=None, **kwds):
        self._transporter = diagram.find_element('#' + transporter, dia.Transporter) if transporter else None
        super().__init__(diagram, class_name='Flow', **kwds)
        self._components = []
        self._component_offsets = {}

    @property
    def components(self):
        return self._components

    @property
    def transporter(self):
        return self._transporter

    def add_component(self, component):
        self._components.append(component)
        self._component_offsets[component] = layout.Point()

    def component_offset(self, component):
        return self._component_offsets.get(component, layout.Point())

    def parse_geometry(self):
        PositionedElement.parse_geometry(self, default_offset=self.diagram.flow_offset,
                                               default_dependency=self.transporter)

    def set_transporter_offsets(self):
        if self.transporter is not None and len(self.components) > 1:
            # Get index of coordinate we want to compare against.
            index = (1 if self.transporter.compartment_side in layout.VERTICAL_BOUNDARIES
                     else 0)
            origin = self.transporter.coords[index]
            component_offset = {}
            num_components = len(self.components)
            for component in self.components:
                offset = component.from_potential.coords[index] - origin
                for to in component.to_potentials:
                    offset += (to.coords[index] - origin)
                component_offset[component] = offset/float(1 + len(component.to_potentials))
            for n, p in enumerate(sorted(component_offset.items(), key=operator.itemgetter(1))):
                w = self.diagram.unit_converter.pixels(self.transporter.width, index, add_offset=False)
                self._component_offsets[p[0]][index] = w*(-0.5 + n/float(num_components - 1))

    def get_flow_line(self, component):
        points = []
        if self.transporter is not None:
            compartment = self.transporter.container.geometry()
            side = self.transporter.compartment_side
            index = 0 if side in layout.VERTICAL_BOUNDARIES else 1
            if compartment.contains(self.geometry()):
                sign = -1 if side in ['top', 'left'] else 1
            else:
                sign = 1 if side in ['top', 'left'] else -1
            transporter_end = self.transporter.coords.copy()
            transporter_end[index] += sign*(self.diagram
                                                .unit_converter.pixels(
                                                      layout.TRANSPORTER_EXTRA,
                                                      index,
                                                      add_offset=False))
            offset = self._component_offsets[component]
            # Are the from and flow elements on the same side
            # of the transporter's compartment?
            if (compartment.contains(self.geometry())
             == compartment.contains(component.from_potential.geometry())):
                points.extend([offset+self.coords, offset+transporter_end])
            else:
                points.extend([offset+transporter_end, offset+self.coords])
        else:
            points.append(self.coords)
        return points

#------------------------------------------------------------------------------

class FlowComponent(Element, PositionedElement):
    def __init__(self, diagram, flow, from_=None, to=None, count=1, line=None, **kwds):
        super().__init__(diagram, class_name='FlowComponent', **kwds)
        self._from_potential = diagram.find_element('#' + from_, Potential)
        self._to_potentials = [diagram.find_element('#' + name, Potential) for name in to.split()]
        self._count = int(count)
        self._lines = dict(start=layout.Line(self, parser.StyleTokens.create(self._style, 'line-start')),
                           end=layout.Line(self, parser.StyleTokens.create(self._style, 'line-end')))
        self._flow = flow

    @property
    def from_potential(self):
        return self._from_potential

    @property
    def to_potentials(self):
        return self._to_potentials

    @property
    def count(self):
        return self._count

    def parse_geometry(self):
        for line in self._lines.values():
            line.parse()

    def svg(self):
        svg = []
        component_points = self._lines['start'].points(self.from_potential.coords, flow=self._flow)
        component_points.extend(self._flow.get_flow_line(self))
        for to in self.to_potentials:
            # Can have multiple `to` potentials
            points = list(component_points)
            points.extend(self._lines['end'].points(to.coords, flow=self._flow, reverse=True))
            line = geo.LineString(points)
            line_style = self.get_style_as_string('line-style', '')
            if (self.count % 2) == 0:  # An even number of lines
                for n in range(self.count // 2):
                    offset = (n + 0.5)*LINE_OFFSET
                    svg.append(svg_line(line.parallel_offset(offset, 'left', join_style=2), self.colour,
                                        style=line_style))
                    svg.append(svg_line(line.parallel_offset(offset, 'right', join_style=2), self.colour,
                                        True, style=line_style))
            else:
                for n in range(self.count // 2):
                    offset = (n + 1)*LINE_OFFSET
                    svg.append(svg_line(line.parallel_offset(offset, 'left', join_style=2), self.colour,
                                        style=line_style))
                    svg.append(svg_line(line.parallel_offset(offset, 'right', join_style=2), self.colour,
                                        True, style=line_style))
                svg.append(svg_line(line, self.colour, style=line_style))
        return svg

#------------------------------------------------------------------------------

class Potential(Element, PositionedElement):
    def __init__(self, diagram, quantity=None, **kwds):
        self._quantity = diagram.find_element('#' + quantity, dia.Quantity)
        self._quantity.set_potential(self)
        super().__init__(self._quantity.container, class_name='Potential', **kwds)

    @property
    def quantity_id(self):
        return self._quantity.id

    @property
    def quantity(self):
        return self._quantity

    def parse_geometry(self):
        PositionedElement.parse_geometry(self, default_offset=self.diagram.quantity_offset,
                                               default_dependency=self.quantity)

#------------------------------------------------------------------------------
