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

import logging

from lxml import etree

import cssselect2
import tinycss2
import tinycss2.color3

#------------------------------------------------------------------------------

from . import SyntaxError

from . import bondgraph as bg
from . import diagram as dia
#from . import geometry as geo

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
            # special parsing for position, width, height??
            elif component.type == 'function':
                return component.name + ' (' + tinycss2.serialize(component.arguments) + ')'
            elif component.type[3:] == 'block':
                return component.type[0] + tinycss2.serialize(component.content) + component.type[1]
            elif component.type == 'ident':
                values.append(component.lower_value)
            elif component.type == 'number':
                pass # value/is_integer/int_value
            elif component.type == 'percentage':
                pass # value/is_integer/int_value
            elif component.type == 'dimension':
                pass # value/is_integer/int_value, unit/lower_unit
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

class ElementWrapper(object):
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
    def __init__(self, root, stylesheets=None):
        self._root_element = root.element
        self._stylesheets = stylesheets if stylesheets else []

    def __iter__(self):
        for e in self._root_element.iter_children():
            if not isinstance(e.etree_element, etree._Element):
                continue
            yield ElementWrapper(e, self._stylesheets)
        raise StopIteration

#------------------------------------------------------------------------------

class Parser(object):
    def __init__(self):
        self._diagram = None
        self._stylesheets = []

    def parse_container(self, element, container):
        for e in ElementChildren(element, self._stylesheets):
            if e.tag == CellDL_namespace('compartment'):
                self.parse_compartment(e, container)
            elif e.tag == CellDL_namespace('quantity'):
                self.parse_quantity(e, container)
            elif (e.tag == CellDL_namespace('transporters')
              and isinstance(container, dia.Compartment)):
                self.parse_transporters(e, container)
            else:
                raise SyntaxError

    def parse_compartment(self, element, container):
        compartment = dia.Compartment(container, style=element.style, **element.attributes)
        self._diagram.add_element(compartment)
        if compartment.has_position_dependencies is False and container:
            compartment.add_position_dependency(container.id)
        container.add_component(compartment)
        self.parse_container(element, compartment)

    def parse_quantity(self, element, container):
        quantity = dia.Quantity(container, style=element.style, **element.attributes)
        self._diagram.add_element(quantity)
        container.add_component(quantity)

    def parse_transporters(self, element, compartment):
        for e in ElementChildren(element, self._stylesheets):
            if e.tag == CellDL_namespace('transporter'):
                transporter = dia.Transporter(compartment, style=e.style, **e.attributes)
                if transporter.has_position_dependencies is False:
                    transporter.add_position_dependency(compartment.id)
                # also no pos attribute ==> set position wrt previous transporter
                self._diagram.add_element(transporter)
                compartment.add_transporter(transporter)
            else:
                raise SyntaxError("Expected 'transporter' element")

    def parse_bond_graph(self, element, bond_graph):
        for e in ElementChildren(element, self._stylesheets):
            if e.tag == CellDL_namespace('potential'):
                self.parse_potential(e, bond_graph)
            elif e.tag == CellDL_namespace('flow'):
                self.parse_flow(e, bond_graph)
            else:
                raise SyntaxError("Invalid 'bond-graph' element")

    def parse_potential(self, element, bond_graph):
        potential = bg.Potential(bond_graph, style=element.style, **element.attributes)
        self._diagram.add_element(potential)
        bond_graph.add_potential(potential)

    def parse_flow(self, element, bond_graph):
        flow = bg.Flow(bond_graph, style=element.style, **element.attributes)
        self._diagram.add_element(flow)
        if flow.has_position_dependencies is False and flow.transporter:
            flow.add_position_dependency(flow.transporter.id)
        for e in ElementChildren(element, self._stylesheets):
            if e.tag == CellDL_namespace('flux'):
                flux = bg.Flux(bond_graph, style=e.style, **e.attributes)
                self._diagram.add_element(flux)
                flow.add_flux(flux)
            else:
                raise SyntaxError
        bond_graph.add_flow(flow)

    '''
    def parse_geometry(self, element, geometry):
        # <geometry> doesn't have a boundary, <box> does
        return self.parse_box(element, geometry, boundary=False)

    def parse_box(self, element, container=None, boundary=True):
        box = geo.Box(container=container, **element.attributes)
        for e in ElementChildren(element):
            if   boundary and e.tag == CellDL_namespace('boundary'):
                self.parse_boundary(e, box)
            elif e.tag == CellDL_namespace('box'):
                self.parse_box(e, box)
            elif e.tag == CellDL_namespace('item'):
                geo.Item(container=box, **e.attributes)
            else:
                raise SyntaxError
        return box

    def parse_boundary(self, element, box):
        for e in ElementChildren(element):
            if   e.tag == CellDL_namespace('top'):    boundary = 'top'
            elif e.tag == CellDL_namespace('left'):   boundary = 'left'
            elif e.tag == CellDL_namespace('bottom'): boundary = 'bottom'
            elif e.tag == CellDL_namespace('right'):  boundary = 'right'
            else:                                     raise SyntaxError
            for item in ElementChildren(e):
                geo.Item(container=box, boundary=boundary, **item.attributes)
    '''
    def parse(self, file, stylesheet=None):
        logging.debug('PARSE: %s', file)
        if stylesheet is not None:
            self._stylesheets.append(StyleSheet(stylesheet))

        # Parse the XML file and wrap the resulting root element so
        # we can easily iterate through its children
        xml_root = etree.parse(file)
        root_element = ElementWrapper(cssselect2.ElementWrapper.from_xml_root(xml_root), self._stylesheets)
        if root_element.tag != CellDL_namespace('cell-diagram'): raise SyntaxError()

        # Parse top-level children, loading stylesheets and
        # finding any diagram and bond-graph elements
        diagram_element = None
        bond_graph_element = None
        for e in ElementChildren(root_element, self._stylesheets):
            if   e.tag == CellDL_namespace('bond-graph'):
                if bond_graph_element is None: bond_graph_element = e
                else: raise SyntaxError
            elif e.tag == CellDL_namespace('diagram'):
                if diagram_element is None: diagram_element = e
                else: raise SyntaxError
            elif e.tag == CellDL_namespace('style'):
                if 'href' in e.attributes: pass          ### TODO: Load external stylesheets...
                else: self._stylesheets.append(StyleSheet(e.text))
            else:
                raise SyntaxError

        # Parse the diagram element
        if diagram_element is not None:
            self._diagram = dia.Diagram(style=diagram_element.style, **diagram_element.attributes)
            self.parse_container(diagram_element, self._diagram)

        # Parse the bond-graph element
        if bond_graph_element is not None:
            bond_graph = bg.BondGraph(self._diagram, style=bond_graph_element.style, **bond_graph_element.attributes)
            self.parse_bond_graph(bond_graph_element, bond_graph)

        logging.debug('')

#        if geometry:
        width = self._diagram.style.get('width')
        height = self._diagram.style.get('height')
        self._diagram.position_elements()

        # For all elements, parse 'pos' attribute
        # Build position dependency graph
        # Assign positions

        # For all fluxes
        # parse 'line' attribute
        # assign line segments

#            geometry.layout_diagram_elements(diagram)
#        if bond_graph:
#            bond_graph.position_elements()

        return (self._diagram, bond_graph)

#------------------------------------------------------------------------------
