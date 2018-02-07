#------------------------------------------------------------------------------

from collections import OrderedDict

#------------------------------------------------------------------------------

from . import Element

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

#------------------------------------------------------------------------------

class Flow(Element):
    def __init__(self, transporter=None, **kwds):
        super().__init__(**kwds)
        self._fluxes = []
        self._transporter = transporter

    @property
    def fluxes(self):
        return self._fluxes

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
        return Quantity.find(self._quantity_id)

#------------------------------------------------------------------------------
