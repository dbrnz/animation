import logging

from lxml import etree

import cssselect2
import tinycss2
import tinycss2.color3

#------------------------------------------------------------------------------

from . import CellDiagram, Compartment, Quantity, Transporter
from . import BondGraph, Flow, Flux, Potential

#------------------------------------------------------------------------------

NAMESPACE = 'http://www.cellml.org/celldl/1.0#'

def CellDL_namespace(tag):
    return '{{{}}}{}'.format(NAMESPACE, tag)

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
        values = []
        for component in declaration.value:
            if declaration.lower_name in ['color', 'colour']:
                return tinycss2.color3.parse_color(component)
            elif component.type == 'function':
                return component.name + ' (' + tinycss2.serialize(component.arguments) + ')'
            elif component.type[3:] == 'block':
                return component.type[0] + tinycss2.serialize(component.content) + component.type[1]
            else:
                values.append(component.value)
        return ''.join(values).strip()

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

class Element(object):
    _reserved_words = ['class', 'from']

    def __init__(self, element, stylesheets):
        self._element = element
        self._tag = element.etree_element.tag
        self._text = element.etree_element.text
        self._attributes = dict(element.etree_element.items())
        # The attribute dictionary is used for keyword arguments and since some
        # attribute names are reserved words in Python we prefix these with `_`
        for name in self._reserved_words:
            if name in self._attributes:
                    self._attributes['_' + name] = self._attributes.pop(name)
        # Look in all style sheets in order, updating element style dictionary...
        self._style = {}
        for s in stylesheets:
            self._style.update(s.match(element))
        # Now check for a style attribute...
        styling = self._attributes.pop('style', None)
        if styling is not None:
            for d in [obj for obj in tinycss2.parse_declaration_list(styling, skip_whitespace=True)
                                  if obj.type == 'declaration']:
                self._style[d.lower_name] = StyleSheet.style_value(d)
        logging.debug("ELEMENT: %s %s %s", self._tag, self._attributes, self._style)

    @property
    def element(self):
        return self._element

    @property
    def attributes(self):
        return self._attributes

    @property
    def style(self):
        return self._style

    @property
    def tag(self):
        return self._tag

    @property
    def text(self):
        return self._text

#------------------------------------------------------------------------------

class ElementChildren(object):
    def __init__(self, root, stylesheets):
        self._root_element = root.element
        self._stylesheets = stylesheets

    def __iter__(self):
        for e in self._root_element.iter_children():
            if not isinstance(e.etree_element, etree._Element):
                continue
            yield Element(e, self._stylesheets)
        raise StopIteration

#------------------------------------------------------------------------------

class Parser(object):
    def __init__(self):
        self._stylesheets = []

    def parse_container(self, element, container=None):
        for e in ElementChildren(element, self._stylesheets):
            if e.tag == CellDL_namespace('compartment'):
                self.parse_compartment(e, container)
            elif e.tag == CellDL_namespace('quantity'):
                self.parse_quantity(e, container)
            elif (e.tag == CellDL_namespace('transporters')
              and isinstance(container, Compartment)):
                self.parse_transporters(e, container)
            else:
                raise SyntaxError

    def parse_compartment(self, element, container=None):
        compartment = Compartment(style=element.style, **element.attributes)
        if container: container.add_component(compartment)
        self.parse_container(element, compartment)

    def parse_quantity(self, element, container):
        container.add_component(Quantity(style=element.style, **element.attributes))

    def parse_transporters(self, element, compartment):
        for e in ElementChildren(element, self._stylesheets):
            if e.tag == CellDL_namespace('transporter'):
                compartment.add_transporter(Transporter(style=e.style, **e.attributes))
            else:
                raise SyntaxError

    def parse_bond_graph(self, element, bond_graph):
        for e in ElementChildren(element, self._stylesheets):
            if e.tag == CellDL_namespace('potential'):
                self.parse_potential(e, bond_graph)
            elif e.tag == CellDL_namespace('flow'):
                self.parse_flow(e, bond_graph)
            else:
                raise SyntaxError

    def parse_potential(self, element, bond_graph):
        bond_graph.add_potential(Potential(style=element.style, **element.attributes))

    def parse_flow(self, element, bond_graph):
        flow = Flow(style=element.style, **element.attributes)
        for e in ElementChildren(element, self._stylesheets):
            if e.tag == CellDL_namespace('flux'):
                flow.add_flux(Flux(style=e.style, **e.attributes))
            else:
                raise SyntaxError
        bond_graph.add_flow(flow)

    def parse(self, file, stylesheet=None):
        logging.debug('PARSE: %s', file)
        if stylesheet is not None:
            self._stylesheets.append(StyleSheet(stylesheet))

        xml_root = etree.parse(file)
        root_element = Element(cssselect2.ElementWrapper.from_xml_root(xml_root), self._stylesheets)
        if root_element.tag != CellDL_namespace('diagram'): raise SyntaxError()

        # First load all stylesheets
        for e in ElementChildren(root_element, self._stylesheets):
            if e.tag == CellDL_namespace('style'):
                if 'href' in e.attributes:
                    pass
                else:
                    self._stylesheets.append(StyleSheet(e.text))

        cell_diagram = None
        bond_graph = None
        for e in ElementChildren(root_element, self._stylesheets):
            if cell_diagram is None and e.tag == CellDL_namespace('cell-diagram'):
                cell_diagram = CellDiagram(style=e.style, **e.attributes)
                self.parse_container(e, cell_diagram)
            elif bond_graph is None and e.tag == CellDL_namespace('bond-graph'):
                bond_graph = BondGraph(style=e.style, **e.attributes)
                self.parse_bond_graph(e, bond_graph)
            elif e.tag == CellDL_namespace('style'):
                pass
            else:
                raise SyntaxError
        logging.debug('')
        return (cell_diagram, bond_graph)

#------------------------------------------------------------------------------
