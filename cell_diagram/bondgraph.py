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

#------------------------------------------------------------------------------

from . import diagram as dia
from . import layout
from . import parser
from .element import Element, PositionedElement

#------------------------------------------------------------------------------

FLOW_OFFSET      = 30  # pixels   ### From stylesheet??
POTENTIAL_OFFSET = 30  # pixels

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
            (x, y) = p.coords
            (qx, qy) = q.coords
            svg.append('<path fill="none" stroke="#222222" stroke-width="2.0" opacity="0.6"'
                     + ' d="M{start_x:g},{start_y:g} L{end_x:g},{end_y:g}"/>'
                       .format(start_x=x, start_y=y, end_x=qx, end_y=qy))
        # Link potentials via flows and fluxes
        for flow in self.flows:
            for flux in flow.fluxes:
                svg.extend(flux.svg())
        # Then symbols
        for p, q in self.potentials.items():
            svg.extend(p.svg(fill='#c0ffc0'))
        for flow in self.flows:
            svg.extend(flow.svg(fill='#ff8080'))
        return svg

#------------------------------------------------------------------------------

class Flow(Element, PositionedElement):
    def __init__(self, diagram, transporter=None, **kwds):
        self._transporter = diagram.find_element('#' + transporter, dia.Transporter) if transporter else None
        super().__init__(diagram, class_name='Flow', **kwds)
        self._fluxes = []
        self._flux_offsets = {}

    @property
    def fluxes(self):
        return self._fluxes

    @property
    def transporter(self):
        return self._transporter

    def add_flux(self, flux):
        self._fluxes.append(flux)
        self._flux_offsets[flux] = layout.Point()

    def flux_offset(self, flux):
        return self._flux_offsets.get(flux, layout.Point())

    def parse_geometry(self):
        PositionedElement.parse_geometry(self, default_offset=self.diagram.flow_offset,
                                               default_dependency=self.transporter)

    def set_transporter_offsets(self):
        if self.transporter is not None and len(self.fluxes) > 1:
            # Get index of coordinate we want to compare against.
            index = (1 if self.transporter.compartment_side in layout.VERTICAL_BOUNDARIES
                     else 0)
            origin = self.transporter.coords[index]
            flux_offset = {}
            num_fluxes = len(self.fluxes)
            for flux in self.fluxes:
                offset = flux.from_potential.coords[index] - origin
                for to in flux.to_potentials:
                    offset += (to.coords[index] - origin)
                flux_offset[flux] = offset/float(1 + len(flux.to_potentials))
            for n, p in enumerate(sorted(flux_offset.items(), key=operator.itemgetter(1))):
                self._flux_offsets[p[0]][index] = (self.diagram.unit_converter.pixels(
                                                      self.transporter.width,
                                                      index,
                                                      add_offset=False)
                                                 *(-0.5 + n/float(num_fluxes - 1)))

    def get_flow_line(self, flux):
        TRANSPORTER_EXTRA = (10, 'x')  ## Get from CSS ???
        points = []
        if self.transporter is not None:
            compartment = self.transporter.container.geometry
            side = self.transporter.compartment_side
            index = 0 if side in layout.VERTICAL_BOUNDARIES else 1
            if compartment.contains(self.geometry):
                sign = -1 if side in ['top', 'left'] else 1
            else:
                sign = 1 if side in ['top', 'left'] else -1
            transporter_end = self.transporter.coords.copy()
            transporter_end[index] += sign*(self.diagram
                                                .unit_converter.pixels(
                                                      TRANSPORTER_EXTRA,
                                                      index,
                                                      add_offset=False))
            offset = self._flux_offsets[flux]
            # Are the from and flow elements on the same side
            # of the transporter's compartment?
            if (compartment.contains(self.geometry)
             == compartment.contains(flux.from_potential.geometry)):
                points.extend([offset+self.coords, offset+transporter_end])
            else:
                points.extend([offset+transporter_end, offset+self.coords])
        else:
            points.append(self.coords)
        return points

#------------------------------------------------------------------------------

class Flux(Element, PositionedElement):
    def __init__(self, diagram, flow, from_=None, to=None, count=1, line=None, **kwds):
        super().__init__(diagram, class_name='Flux', **kwds)
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
        flux_points = self._lines['start'].points(self.from_potential.coords, flow=self._flow)
        flux_points.extend(self._flow.get_flow_line(self))
        for to in self.to_potentials:
            # Can have multiple `to` potentials
            points = list(flux_points)
            points.extend(self._lines['end'].points(to.coords, flow=self._flow, reverse=True))
            # TODO: Get colour of line from class...
            svg.append('<path fill="none" stroke="#222222" stroke-width="{:g}" opacity="0.6"'
                .format(self.count*2.5)
              + ' d="M{:g},{:g} {:s}"/>'
                .format(points[0][0], points[0][1],
                       ' '.join(['L{:g},{:g}'.format(*point) for point in points[1:]])))
        # repeated flux.count times
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
