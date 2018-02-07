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

#------------------------------------------------------------------------------

class Diagram(Container):
    def __init__(self, **kwds):
        super().__init__(**kwds)

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

#------------------------------------------------------------------------------

class Quantity(Element):
    def __init__(self, **kwds):
        super().__init__(**kwds)

#------------------------------------------------------------------------------

class Transporter(Element):
    def __init__(self, **kwds):
        super().__init__(**kwds)

#------------------------------------------------------------------------------

