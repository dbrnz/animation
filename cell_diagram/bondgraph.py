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

from collections import OrderedDict

#------------------------------------------------------------------------------

from . import diagram as dia
from . import parser
from .element import Element, PositionedElement

#------------------------------------------------------------------------------

FLOW_OFFSET      = 30  # pixels   ### From stylesheet??
POTENTIAL_OFFSET = 30  # pixels

def relative_position(position, direction, offset):
    if   direction == 'left': return  (position[0] - offset, position[1])
    elif direction == 'right': return (position[0] + offset, position[1])
    elif direction == 'above': return (position[0], position[1] - offset)
    elif direction == 'below': return (position[0], position[1] + offset)

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

    def position_elements(self):
        ###self.style.get('flow-offset')
        ###self.style.get('potential-offset')

        # Position potentials wrt corresponding quantities
        for p, q in self.potentials.items():
            p.set_position(relative_position(q.position, p.style.get('pos', 'left'), POTENTIAL_OFFSET))

        # Position flows wrt their transporters
        for flow in self.flows:
            pos = flow.style.get('pos', 'above')
            if flow.transporter:
                flow.set_position(relative_position(flow.transporter.position, pos, FLOW_OFFSET))
            else:
                # Position flow at centroid of to/from potentials
                from_position = [0.0, 0.0]
                from_count = 0
                to_position = [0.0, 0.0]
                to_count = 0
                for flux in flow.fluxes:
                    from_position[0] += flux.from_potential.position[0]
                    from_position[1] += flux.from_potential.position[1]
                    from_count += 1
                    for p in flux.to_potentials:
                        to_position[0] += p.position[0]
                        to_position[1] += p.position[1]
                        to_count += 1
                if from_count and to_count:
                    flow.set_position(((from_position[0]/float(from_count) + to_position[0]/float(to_count))/2.0,
                                       (from_position[1]/float(from_count) + to_position[1]/float(to_count))/2.0))

    def svg(self):
        svg = [ ]
        for p, q in self.potentials.items():
            (x, y) = p.coords
            (qx, qy) = q.coords
            svg.append('<path fill="none" stroke="#222222" stroke-width="2.0" opacity="0.6"'
                     + ' d="M{start_x:g},{start_y:g} L{end_x:g},{end_y:g}"/>'
                       .format(start_x=x, start_y=y, end_x=qx, end_y=qy))
            svg.extend(p.svg(fill='#c0ffc0'))
        # Link potentials via flows and fluxes
        for flow in self.flows:
            svg.extend(flow.svg(fill='#ff8080'))
            for flux in flow.fluxes:
                svg.extend(flux.svg(flow))
        return svg

#------------------------------------------------------------------------------

class Flow(Element, PositionedElement):
    def __init__(self, diagram, transporter=None, **kwds):
        self._transporter = diagram.find_element('#' + transporter, dia.Transporter) if transporter else None
        super().__init__(diagram, class_name='Flow', **kwds)
        self._fluxes = []

    @property
    def fluxes(self):
        return self._fluxes

    @property
    def transporter(self):
        return self._transporter

    def add_flux(self, flux):
        self._fluxes.append(flux)

    def parse_position(self):
        PositionedElement.parse_position(self, default_offset=self.diagram.flow_offset,
                                               default_dependency=self.transporter)

#------------------------------------------------------------------------------

class Flux(Element, PositionedElement):
    def __init__(self, diagram, from_=None, to=None, count=1, line=None, **kwds):
        super().__init__(diagram, class_name='Flux', **kwds)
        self._from_potential = diagram.find_element('#' + from_, Potential)
        self._to_potentials = [diagram.find_element('#' + name, Potential) for name in to.split()]
        self._count = int(count)
        curve_tokens = self._style.get('curve', None) if self._style else None
        self._curve_tokens = parser.StyleTokens(curve_tokens) if curve_tokens else None
        self._curve_segments = []

    @property
    def from_potential(self):
        return self._from_potential

    @property
    def to_potentials(self):
        return self._to_potentials

    @property
    def count(self):
        return self._count

    def parse_position(self):
        if self._curve_tokens is None:
            return
        tokens = self._curve_tokens
        # "210 above #u16 #v5, -90 left #NCE"
        while True:
            angle, tokens = parser.get_number(tokens)
            token = tokens.next()
            if (token.type != 'ident'
             or token.lower_value not in ['x-pos', 'y-pos']):
                raise SyntaxError("Unknown constraint for curve segment.")
            direction = 0 if token.lower_value == 'xpos' else 1
            dependencies = []
            token = tokens.next()
            while token.type == 'hash':
                try:
                    dependencies.append('#' + token.value)
                    token = tokens.next()
                except StopIteration:
                    break
            if not dependencies:
                raise SyntaxError("Identifier(s) expected")
            self._curve_segments.append((angle, direction, dependencies))
            if token == ',':
                continue
            elif tokens.peek() is None:
                break
            else:
                raise SyntaxError("Invalid syntax")

        def svg(self, flow):
            compartment = (flow.transporter.container.geometry
                           if flow.transporter is not None
                           else None)
            (from_x, from_y) = flux.from_potential.coords
            flow_points = []
            if compartment is not None:
                # Are the from and flow elements on the same side
                # of the transporter's compartment?
                if (compartment.contains(flow.geometry) == compartment.contains(flux.from_potential.geometry)):
                    flow_points.extend([flow.coords, flow.transporter.coords])
                else:
                    flow_points.append(flow.transporter.coords)

            for to in flux.to_potentials:
                if (compartment is None
                 or compartment.contains(flow.geometry) != compartment.contains(flux.from_potential.geometry)):
                    flow_points.append(flow.coords)
                flow_points.append(to.coords)
                svg.append('<path fill="none" stroke="#222222" stroke-width="{:g}" opacity="0.6"'
                    .format(flux.count*2.5)
                  + ' d="M{:g},{:g} {:s}"/>'
                    .format(from_x, from_y,
                           ' '.join(['L{:g},{:g}'.format(*point) for point in flow_points])))
            # Path from flux.from_potential to flux.to_potentials
            # via flow.transporter and flow nodes
            # repeated flux.count times

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

    def parse_position(self):
        PositionedElement.parse_position(self, default_offset=self.diagram.quantity_offset,
                                               default_dependency=self.quantity)

#------------------------------------------------------------------------------
