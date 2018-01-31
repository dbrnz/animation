from collections import OrderedDict

#------------------------------------------------------------------------------

class Element(object):
    # Dictionary of all elements that have an id
    _elements = { }

    def __init__(self, _class=None, id=None, label=None, style=None):
        self._class = _class
        self._id = id
        self._label = label if label else id
        if id is not None:
            Element._elements[id] = self
        self._style = style

    @property
    def id(self):
        return self._id

    @property
    def label(self):
        return self._label

    @property
    def style(self):
        return self._style

    def draw(self):
        return ''

    @classmethod
    def find(cls, id):
        e = Element._elements.get(id)
        return e if e is not None and isinstance(e, cls) else None

#------------------------------------------------------------------------------

class Container(Element):
    def __init__(self, **kwds):
        super().__init__(**kwds)
        self._components = []

    def add_component(self, component):
        self._components.append(component)

    def draw(self):
        return '\n'.join([c.draw() for c in self._components])

#------------------------------------------------------------------------------

class CellDiagram(Container):
    def __init__(self, **kwds):
        super().__init__(**kwds)

#------------------------------------------------------------------------------

class Compartment(Container):
    def __init__(self, **kwds):
        super().__init__(**kwds)
        self._transporters = []

    def add_transporter(self, transporter):
        self._transporters.append(transporter)

#------------------------------------------------------------------------------

class Quantity(Element):
    def __init__(self, **kwds):
        super().__init__(**kwds)

#------------------------------------------------------------------------------

class Transporter(Element):
    def __init__(self, **kwds):
        super().__init__(**kwds)

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
