from collections import OrderedDict

from lxml import etree
import cssselect2
import tinycss2
import tinycss2.color3

import igraph

import logging

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

    @property
    def id(self):
        return self._id

    @property
    def label(self):
        return self._label

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

    def add_potential(self, potential, quantity):
        self._potentials[potential] = quantity

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

    @property
    def potential(self):
        return self._potential

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

class StyleSheet(cssselect2.Matcher):
    def __init__(self, stylesheet):
        '''Parse CSS and add rules to the matcher.'''
        super().__init__()
        rules = tinycss2.parse_stylesheet(stylesheet, skip_comments=True, skip_whitespace=True)
        for rule in rules:
            selectors = cssselect2.compile_selector_list(rule.prelude)
            declarations = [obj for obj in tinycss2.parse_declaration_list(rule.content, skip_whitespace=True)
                                        if obj.type == 'declaration']
            for selector in selectors:
                self.add_selector(selector, declarations)

    @staticmethod
    def style_value(declaration):
        components = [c for c in declaration.value if c.type != 'whitespace']
        if not components:
            return None
        component = components[0]
        if declaration.lower_name == 'colour':
            return tinycss2.color3.parse_color(component)
        elif component.type == 'function':
            return component.name + ' (' + tinycss2.serialize(component.arguments) + ')'
        elif component.type[3:] == 'block':
            return component.type[0] + tinycss2.serialize(component.content) + component.type[1]
        else:
            return component.value

    def match(self, element):
        rules = {}
        matches = super().match(element)
        if matches:
            for match in matches:
                specificity, order, pseudo, declarations = match
                for declaration in declarations:
                    rules[declaration.lower_name] = self.style_value(declaration)
        return rules

#------------------------------------------------------------------------------

class SyntaxError(Exception):
    pass

#------------------------------------------------------------------------------

class Parser(object):
    _reserved_words = ['class', 'from']

    def __init__(self, elements, stylesheet=None):
        self._element_iter = elements.iter_subtree()
        self._stylesheet = stylesheet
        self._diagram = None
        self._element = None
        self._element_tag = None
        self._element_attributes = {}
        self._style = None

    def _next_element(self):
        try:
            self._element = self._element_iter.__next__()
            while isinstance(self._element.etree_element, etree._Comment):
                self._element = self._element_iter.__next__()
            self._element_tag = self._element.etree_element.tag
            self._element_attributes = dict(self._element.etree_element.items())
            # The attribute dictionary is used for keyword arguments and since some
            # attribute names are reserved words in Python we prefix these with `_`
            for name in self._reserved_words:
                if name in self._element_attributes:
                    self._element_attributes['_' + name] = self._element_attributes.pop(name)
            self._element_style = self._stylesheet.match(self._element) if self._stylesheet else None
        except StopIteration:
            self._element = None
            self._element_tag = None
            self._element_attributes = {}
            self._style = None

    def _parse_container(self, container=None):
        self._next_element()
        while self._element_tag is not None:
            logging.debug("PROCESS: %s %s %s", self._element_tag, self._element_attributes, self._element_style)
            if self._element_tag == 'compartment':
                self.parse_compartment(container)
            elif self._element_tag == 'flow':
                self.parse_flow()
            elif self._element_tag == 'quantity':
                self.parse_quantity(container)
            elif self._element_tag == 'transporters':
                if isinstance(container, Compartment): self.parse_transporters(container)
                else: raise SyntaxError
            else:
                self._next_element()

    def parse_compartment(self, container=None):
        compartment = Compartment(**self._element_attributes)
        if container: container.add_component(compartment)
        self._parse_container(compartment)

    def parse_flow(self):
        flow = Flow(**self._element_attributes)
        self._next_element()
        while self._element_tag == 'flux':
            flow.add_flux(Flux(**self._element_attributes))
            self._next_element()
        self._diagram.add_flow(flow)

    def parse_quantity(self, container):
        quantity = Quantity(**self._element_attributes)
        container.add_component(quantity)
        if quantity.potential is not None:
            self._diagram.add_potential(quantity.potential, quantity)
        self._next_element()

    def parse_transporters(self, compartment):
        self._next_element()
        while self._element_tag == 'transporter':
            compartment.add_transporter(Transporter(**self._element_attributes))
            self._next_element()

    def parse(self):
        self._next_element()
        if self._element_tag != 'cell-diagram': raise SyntaxError()
        self._diagram = CellDiagram(**self._element_attributes)
        self._parse_container(self._diagram)
        if self._element_tag is not None: raise SyntaxError()
        return self._diagram

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

def parse(file, stylesheet=None):
    logging.debug('PARSE: %s', file)
    tree = etree.parse(file)
    selector_tree = cssselect2.ElementWrapper.from_xml_root(tree)
    parser = Parser(selector_tree, stylesheet)
    diagram = parser.parse()
    logging.debug('')
    return diagram

#------------------------------------------------------------------------------

def bond_graph(diagram):
    g = igraph.Graph(directed=True)
    potentials = list(diagram.potentials.keys())
    g.add_vertices(potentials)
    g.vs['label'] = potentials
    for flow in diagram.flows:
        g.add_vertex(flow.id, label=flow.id, color='blue')
        for flux in flow.fluxes:
            for n in range(flux.count):
                g.add_edge(flux.from_potential, flow.id)
                g.add_edge(flow.id, flux.to_potential)
    return g

#------------------------------------------------------------------------------

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)

    stylesheet = StyleSheet('''
        #q21 {
          colour : pink ;
        }
        .cell {
          shape: (12, 8);
          colour: blue;
          /* closed-cylinder, rectangle, circle/ellipse */
          /* thickness, size, aspect-ratio, ... */
        }
        .sodium {
          colour: yellow;
          /* symbol, ... */
        }
        .potassium {
          colour: green;
        }
        .channel {
          position: bottom;
        }
        #i_Leak {
          position: right;
        }
      ''')

    diagram = parse('bond_graph.xml')

    ## parse('cell_diagram.xml', stylesheet)

    g = bond_graph(diagram)
    layout = g.layout("kk")
    igraph.plot(g, layout=layout)

