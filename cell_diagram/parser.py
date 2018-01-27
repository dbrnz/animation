import logging

from lxml import etree

import cssselect2
import tinycss2
import tinycss2.color3

#------------------------------------------------------------------------------

from . import CellDiagram, Compartment, Flow, Flux, Quantity, Transporter

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

    def __init__(self):
        self._element_iter = None
        self._stylesheet = None
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

    def parse(self, file, stylesheet=None):
        logging.debug('PARSE: %s', file)
        tree = etree.parse(file)
        selector_tree = cssselect2.ElementWrapper.from_xml_root(tree)
        self._element_iter = selector_tree.iter_subtree()
        self._stylesheet = stylesheet
        #
        self._next_element()
        if self._element_tag != 'cell-diagram': raise SyntaxError()
        self._diagram = CellDiagram(**self._element_attributes)
        self._parse_container(self._diagram)
        if self._element_tag is not None: raise SyntaxError()
        logging.debug('')
        return self._diagram

#------------------------------------------------------------------------------
