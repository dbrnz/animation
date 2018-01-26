from lxml import etree

#import cssselect2
#import tinycss2
#import tinycss2.color3

#------------------------------------------------------------------------------

class Element(object):
    # Dictionary of all elements that have an id
    _elements = { }

    def __init__(self, _class=None, id=None, label=None):
        self._class = _class
        self._id = id
        self._label = label if label else id
        if id is not None:
            Element._elements[id] = self

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
    def __init__(self, potential=None, **kwds):
        super().__init__(**kwds)
        self._potential = potential

#------------------------------------------------------------------------------

class Transporter(Element):
    def __init__(self, **kwds):
        super().__init__(**kwds)

#------------------------------------------------------------------------------

class Flow(Element):
    def __init__(self, transporter=None, **kwds):
        super().__init__(**kwds)
        self._fluxes = []
        self._transporter = transporter

    def add_flux(self, flux):
        self._fluxes.append(flux)

#------------------------------------------------------------------------------

class Flux(Element):
    def __init__(self, _from=None, to=None, count=1, **kwds):
        super().__init__(**kwds)
        self._from = _from
        self._to = to
        self._count = count

#------------------------------------------------------------------------------

class SyntaxError(Exception):
    pass

#------------------------------------------------------------------------------

class Parser(object):
    _reserved_words = ['class', 'from']

    def __init__(self, tree, stylesheet=None):
        self._element_iter = tree.iter()
        self._stylesheet = stylesheet
        self._element = None
        self._element_tag = None
        self._style = None

    def _next_element(self):
        try:
            self._element = self._element_iter.__next__()
            self._element_tag = self._element.tag
            self._element_attributes = dict(self._element.items())
            # The attribute dictionary is used for keyword arguments and since some
            # attribute names are reserved words in Python we prefix these with `_`
            for name in self._reserved_words:
                if name in self._element_attributes:
                    self._element_attributes['_' + name] = self._element_attributes.pop(name)
            print("NEXT: ", self._element_tag, " ", self._element_attributes)
            #self._style = self._stylesheet.match(self._element) if self._stylesheet else None
        except StopIteration:
            self._element = None
            self._element_tag = None
            self._element_attributes = {}
            self._style = None
            raise

    def _parse_container(self, container=None):
        try:
            self._next_element()
            while True:
                if self._element_tag == 'compartment':
                    self.parse_compartment(container)
                elif self._element_tag == 'flow':
                    self.parse_flow()
                elif self._element_tag == 'quantity':
                    self.parse_quantity(container)
                elif isinstance(container, Compartment) and self._element_tag == 'transporters':
                    self.parse_transporters(container)
        except StopIteration:
            pass

    def parse_cell_diagram(self):
        diagram = CellDiagram(**self._element_attributes)
        self._parse_container(diagram)
        return diagram

    def parse_cell_compartment(self, container=None):
        compartment = Compartment(**self._element_attributes)
        if container: container.add_component(compartment)
        self._parse_container(compartment)

    def parse_flow(self):
        flow = Flow(**self._element_attributes)
        self._next_element()
        while self._element_tag == 'flux':
            flow.add_flux(Flux(**self._element_attributes))
            self._next_element()
        ## Add `flow` to diagram's list of flows...

    def parse_quantity(self, container):
        container.add_component(Quantity(**self._element_attributes))
        self._next_element()

    def parse_transporters(self, compartment):
        self._next_element()
        while self._element_tag == 'transporter':
            compartment.add_transporter(Transporter(**self._element_attributes))
            self._next_element()

    def parse(self):
        self._next_element()
        if self._element_tag != 'cell-diagram':
            raise SyntaxError()
        diagram = self.parse_cell_diagram()
        if self._element_tag is not None:
            raise SyntaxError()
        return diagram

#------------------------------------------------------------------------------

def test_diagram():
    diagram = CellDiagram()
    diagram.add_component(Substance(_class="sodium", id="q1",  variable="u1", label="$\\text{q}_1^{[\\text{Na}^+]_o}$"))

    cell = Compartment(_class="cell")
    cell.add_transporter(Transporter(_class="sodium channel", id="Na", label="$\text{I}_\text{Na}"))
    cell.add_transporter(Transporter(_class="sodium channel", id="Na-b", label="$\text{I}_\text{Na,b}"))
    cell.add_transporter(Transporter(_class="sodium channel", id="p-Na", label="$\text{I}_\text{p,Na}"))
    cell.add_component(Substance(_class="sodium", id="q2",  variable="u2", label="$\\text{q}_2^{[\\text{Na}^+]_o}$"))

#------------------------------------------------------------------------------

def test_bond_graph():
    tree = etree.parse('bond_graph.xml')
    parser = Parser(tree)
    diagram = parser.parse()

#------------------------------------------------------------------------------

if __name__ == '__main__':
    test_bond_graph()
