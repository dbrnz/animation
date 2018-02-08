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
from . import Element

#------------------------------------------------------------------------------

FLOW_OFFSET      = 15  # pixels   ### From stylesheet??
POTENTIAL_OFFSET = 20  # pixels

def relative_position(position, direction, offset):
    if   direction == 'left': return  (position[0] - offset, position[1])
    elif direction == 'right': return (position[0] + offset, position[1])
    elif direction == 'above': return (position[0], position[1] - offset)
    elif direction == 'below': return (position[0], position[1] + offset)

#------------------------------------------------------------------------------

class BondGraph(Element):
    def __init__(self, **kwds):
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

#------------------------------------------------------------------------------

class Flow(Element):
    def __init__(self, transporter=None, **kwds):
        super().__init__(**kwds)
        self._fluxes = []
        self._transporter_id = transporter

    @property
    def fluxes(self):
        return self._fluxes

    @property
    def transporter(self):
        return dia.Transporter.find(self._transporter_id)

    def add_flux(self, flux):
        self._fluxes.append(flux)

#------------------------------------------------------------------------------

class Flux(Element):
    def __init__(self, _from=None, to=None, count=1, **kwds):
        super().__init__(**kwds)
        self._from = _from
        self._to = to
        self._count = int(count)

    @property
    def from_potential(self):
        return self._from

    @property
    def to_potential(self):
        return self._to

    @property
    def count(self):
        return self._count

#------------------------------------------------------------------------------

class Potential(Element):
    def __init__(self, quantity=None, **kwds):
        super().__init__(**kwds)
        self._quantity_id = quantity

    @property
    def quantity_id(self):
        return self._quantity_id

    @property
    def quantity(self):
        return dia.Quantity.find(self._quantity_id)

#------------------------------------------------------------------------------
