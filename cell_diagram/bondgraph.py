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
            (x, y) = p.position.coords
            (qx, qy) = q.position.coords
            svg.append('<path fill="#eeeeee" stroke="#222222" stroke-width="4.0" opacity="0.6"'
                     + ' d="M{start_x:g},{start_y:g} L{end_x:g},{end_y:g}"/>'
                       .format(start_x=x, start_y=y, end_x=qx, end_y=qy))
            svg.extend(p.svg(fill='#c0ffc0'))
        # Link potentials via flows and fluxes
        for flow in self.flows:
            if flow.position is not None:
                svg.extend(flow.svg(fill='#ff8080'))
            for flux in flow.fluxes:
                pass
                # Path from flux.from_potential to flux.to_potentials
                # via flow.transporter and flow nodes
                # repeated flux.count times
                #for p in to_potentials: g.add_edge(flow.id, p, weight=weighting)
        return svg

#------------------------------------------------------------------------------

class Flow(Element, PositionedElement):
    def __init__(self, diagram, transporter=None, **kwds):
        self._transporter = diagram.find_element(transporter, dia.Transporter)
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

    def parse_position(self, position, tokens):
        PositionedElement.parse_position(self, position, tokens)

#------------------------------------------------------------------------------

class Flux(Element):
    def __init__(self, diagram, from_=None, to=None, count=1, line=None, **kwds):
        super().__init__(diagram, class_name='Flux', **kwds)
        self._from_potential = diagram.find_element(_from, Potential)
        self._to_potentials = [diagram.find_element(name, Potential) for name in to.split()]
        self._count = int(count)
        self._line = line

    @property
    def from_potential(self):
        return self._from_potential

    @property
    def to_potentials(self):
        return self._to_potential_ids

    @property
    def count(self):
        return self._count

#------------------------------------------------------------------------------

class Potential(Element, PositionedElement):
    def __init__(self, diagram, quantity=None, **kwds):
        self._quantity = diagram.find_element(quantity, dia.Quantity)
        super().__init__(diagram, class_name='Potential', **kwds)

    @property
    def quantity_id(self):
        return self._quantity.id

    @property
    def quantity(self):
        return self._quantity

    def parse_position(self, position, tokens):
        PositionedElement.parse_position(self, position, tokens)

#------------------------------------------------------------------------------
