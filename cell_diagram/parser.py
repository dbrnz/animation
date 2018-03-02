# -----------------------------------------------------------------------------
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
# -----------------------------------------------------------------------------

import io
import itertools
import logging

from lxml import etree

import cssselect2
import tinycss2
import tinycss2.color3

# -----------------------------------------------------------------------------

from . import SyntaxError

from . import bondgraph as bg
from . import diagram as dia

# -----------------------------------------------------------------------------

NAMESPACE = 'http://www.cellml.org/celldl/1.0#'


def CellDL_namespace(tag):
    return '{{{}}}{}'.format(NAMESPACE, tag)

#------------------------------------------------------------------------------

class StyleTokens(object):
    def __init__(self, tokens):
        self._tokens = iter(tokens)
        self._buffer = []
        self._value = None
        self._skip_space = True

    def __iter__(self):
        return self

    def __next__(self):
        while True:
            try:
                token = (self._buffer.pop()
                         if self._buffer
                         else next(self._tokens))
            except StopIteration:
                self._value = None
                raise StopIteration
            if (not self._skip_space
             or token.type not in ['comment', 'whitespace']):
                self._skip_space = True
                self._value = token
                return token

    @property
    def value(self):
        return self._value

    def next(self, skip_space=True):
        self._skip_space = skip_space
        return next(self)

    def back(self):
        self._buffer.append(self._value)

    def peek(self, skip_space=True):
        try:
            self._skip_space = skip_space
            token = next(self)
        except StopIteration:
            return None
        self._buffer.append(token)
        return token

# -----------------------------------------------------------------------------

'''
Convention is that `tokens` is at **last** token processed.
'''

def get_number(tokens):
    """
    :param tokens: `StyleTokens` of tokens
    :return: tuple(value, tokens)
    """
    try:
        token = tokens.next()
        if token.type != 'number':
            raise SyntaxError("Number expected.")
        else:
            return ((token.int_value if token.is_integer else token.value,
                     tokens))
    except StopIteration:
        return (0, tokens)

# -----------------------------------------------------------------------------


def get_percentage(tokens, default=None):
    """
    :param tokens: `StyleTokens` of tokens
    :return: tuple(Length, tokens)
    """

    try:
        token = tokens.peek()
        if token is None or token.type != 'percentage':
            if default is not None:
                return (default, tokens)
            else:
                raise SyntaxError('Percentage expected.')
        percentage = (token.int_value if token.is_integer else token.value)
        tokens.next()
        token = tokens.peek(False)
        modifier = (token.lower_value
                    if (token is not None and token.type == 'ident')
                    else '')
        if modifier not in ['', 'x', 'y']:
            raise SyntaxError("Modifier ({}) must be 'x' or 'y'.".format(modifier))
        elif modifier != '':
            tokens.next()
        return ((percentage, '%' + modifier), tokens)
    except StopIteration:
        return ((0, '%'), tokens)


# -----------------------------------------------------------------------------

def get_length(tokens, default=None):
    """
    :param tokens: `StyleTokens` of tokens
    :return: tuple(Length, tokens)

    `100`, `100x`, `100y`
    """
    try:
        token = tokens.peek()
        if token is not None and token.type == 'percentage':
            return get_percentage(tokens, default)
        elif token is None or token.type not in ['number', 'dimension']:
            if default is not None:
                return (default, tokens)
            else:
                raise SyntaxError('Length expected.')
        value = (token.int_value if token.is_integer else token.value)
        modifier = (token.lower_unit if token.type == 'dimension' else '')
        if modifier not in ['', 'x', 'y']:
            raise SyntaxError("Modifier must be 'x' or 'y'.")
        tokens.next()
        return ((value, modifier), tokens)
    except StopIteration:
        return ((0, ''), tokens)

# -----------------------------------------------------------------------------


def get_coordinates(tokens):
    """
    Get a coordinate pair.

    :param tokens: `StyleTokens` of tokens
    :return: tuple(tuple(Length, Length), tokens)
    """
    coords = []
    got_comma = True
    try:
        while True:
            token = tokens.next()
            if token == ',':
                if got_comma:
                    raise SyntaxError("Unexpected comma.")
                got_comma = True
            elif got_comma and token.type in ['dimension', 'number', 'percentage']:
                got_comma = False
                tokens.back()
                length, tokens = get_length(tokens)
                coords.append(length)
            else:
                raise SyntaxError("Invalid syntax.")

    except StopIteration:
        pass

    if len(coords) != 2:
        raise SyntaxError("Expected length pair.")

    return (coords, tokens)

# -----------------------------------------------------------------------------


class StyleSheet(cssselect2.Matcher):
    def __init__(self, stylesheet):
        '''Parse CSS and add rules to the matcher.'''
        super().__init__()
        rules = tinycss2.parse_stylesheet(stylesheet, skip_comments=True,
                                          skip_whitespace=True)
        for rule in rules:
            selectors = cssselect2.compile_selector_list(rule.prelude)
            declarations = [obj for obj in tinycss2.parse_declaration_list(
                                               rule.content,
                                               skip_whitespace=True)
                            if obj.type == 'declaration']
            for selector in selectors:
                self.add_selector(selector, declarations)

    def match(self, element):
        rules = {}
        matches = super().match(element)
        if matches:
            for match in matches:
                specificity, order, pseudo, declarations = match
                for declaration in declarations:
                    rules[declaration.lower_name] = declaration.value
        return rules

# -----------------------------------------------------------------------------


class ElementWrapper(object):
    _reserved_words = ['class', 'from']

    def __init__(self, element, stylesheets):
        self._element = element
        self._tag = element.etree_element.tag
        self._text = element.etree_element.text
        self._attributes = dict(element.etree_element.items())
        # The attribute dictionary is used for keyword arguments and since some
        # attribute names are reserved words in Python we suffix these with `_`
        for name in self._reserved_words:
            if name in self._attributes:
                self._attributes[name + '_'] = self._attributes.pop(name)
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

# -----------------------------------------------------------------------------


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

# -----------------------------------------------------------------------------


class Parser(object):
    def __init__(self):
        self._diagram = None
        self._bond_graph = None
        self._stylesheets = []
        self._last_element = None  # For error handling

    def parse_container(self, element, container):
        for e in ElementChildren(element, self._stylesheets):
            self._last_element = e
            if e.tag == CellDL_namespace('compartment'):
                self.parse_compartment(e, container)
            elif e.tag == CellDL_namespace('quantity'):
                self.parse_quantity(e, container)
            elif (e.tag == CellDL_namespace('transporter')
              and isinstance(container, dia.Compartment)):
                self.parse_transporter(e, container)
            else:
                raise SyntaxError("Unexpected XML element <{}>".format(e.tag))

    def parse_compartment(self, element, container):
        compartment = dia.Compartment(container, style=element.style, **element.attributes)
        self._diagram.add_element(compartment)
        container.add_component(compartment)
        self.parse_container(element, compartment)

    def parse_quantity(self, element, container):
        quantity = dia.Quantity(container, style=element.style, **element.attributes)
        self._diagram.add_element(quantity)
        container.add_component(quantity)

    def parse_transporter(self, element, compartment):
        transporter = dia.Transporter(compartment, style=element.style, **element.attributes)
        self._diagram.add_element(transporter)
        compartment.add_transporter(transporter)   ## Do when adding element to diagram??

    def parse_bond_graph(self, element):
        for e in ElementChildren(element, self._stylesheets):
            self._last_element = e
            if e.tag == CellDL_namespace('potential'):
                self.parse_potential(e)
            elif e.tag == CellDL_namespace('flow'):
                self.parse_flow(e)
            else:
                raise SyntaxError("Invalid <bond-graph> element")

    def parse_potential(self, element):
        potential = bg.Potential(self._diagram, style=element.style, **element.attributes)
        if potential.quantity is None:
            raise SyntaxError("Missing or unknown quantity.")
        potential.set_container(potential.quantity.container)
        self._diagram.add_element(potential)
        self._bond_graph.add_potential(potential)

    def parse_flow(self, element):
        flow = bg.Flow(self._diagram, style=element.style, **element.attributes)
        self._diagram.add_element(flow)
        container = transporter.container if flow.transporter is not None else None
        for e in ElementChildren(element, self._stylesheets):
            self._last_element = e
            if e.tag == CellDL_namespace('flux'):
                if 'from_' not in e.attributes or 'to' not in e.attributes:
                    raise SyntaxError("Flux requires 'from' and 'to' potentials.")
                flux = bg.Flux(self._diagram, style=e.style, **e.attributes)
                if flow.transporter is None:
                    if container is None:
                        container = flux.from_potential.container
                    elif container != flux.from_potential.container:
                        raise ValueError("All 'to' potentials must be in the same container.")
                    for p in flux.to_potentials:
                        if container != p.container:
                            raise ValueError("All 'from' and 'to' potentials must be in the same container.")
                flux.set_container(container)
                self._diagram.add_element(flux)    ## Add to container...
                flow.add_flux(flux)
            else:
                raise SyntaxError
        self._bond_graph.add_flow(flow)


    def parse_diagram(self, root):
        self._last_element = root
        if root.tag != CellDL_namespace('cell-diagram'):
            raise SyntaxError("Root tag is not <cell-diagram>")

        # Parse top-level children, loading stylesheets and
        # finding any diagram and bond-graph elements
        diagram_element = None
        bond_graph_element = None
        for e in ElementChildren(root, self._stylesheets):
            self._last_element = e
            if   e.tag == CellDL_namespace('bond-graph'):
                if bond_graph_element is None:
                    bond_graph_element = e
                else:
                    raise SyntaxError("Can only declare a single <bond-graph>")
            elif e.tag == CellDL_namespace('diagram'):
                if diagram_element is None:
                    diagram_element = e
                else:
                    raise SyntaxError("Can only declare a single <diagram>")
            elif e.tag == CellDL_namespace('style'):
                pass
            else:
                raise SyntaxError("Unknown XML element: <{}>".format(e.tag))

        # Parse the diagram element
        if diagram_element is not None:
            self._diagram = dia.Diagram(style=diagram_element.style,
                                        **diagram_element.attributes)
            self.parse_container(diagram_element, self._diagram)
        else:
            self._diagram = dia.Diagram()

        # Parse the bond-graph element
        if bond_graph_element is not None:
            self._bond_graph = bg.BondGraph(self._diagram,
                                            style=bond_graph_element.style,
                                            **bond_graph_element.attributes)
            self.parse_bond_graph(bond_graph_element)
        else:
            self._bond_graph = bg.BondGraph(self._diagram)


    def parse(self, file, stylesheet=None):
        logging.debug('PARSE: %s', file)

        # Parse the XML file and wrap the resulting root element so
        # we can easily iterate through its children
        error = None
        try:
            xml_root = etree.parse(file)
        except (etree.ParseError, etree.XMLSyntaxError) as err:
            lineno, column = err.position
            with open(file) as f:
                t = f.read()
                line = next(itertools.islice(io.StringIO(t), lineno-1, None))
            error = ("{}\n{}".format(err, line))
        if error:
            raise SyntaxError(error)

        try:
            # Load all style information before wrapping the root element
            if stylesheet is not None:
                self._stylesheets.append(StyleSheet(stylesheet))
            for e in xml_root.iterfind(CellDL_namespace('style')):
                if 'href' in e.attrib:
                    pass          ### TODO: Load external stylesheets...
                else:
                    self._stylesheets.append(StyleSheet(e.text))
        except cssselect2.parser.SelectorError as err:
            error = "{} when parsing stylesheet.".format(err)
        if error:
            raise SyntaxError(error)

        root_element = ElementWrapper(
            cssselect2.ElementWrapper.from_xml_root(xml_root),
            self._stylesheets)

        try:
            self.parse_diagram(root_element)
        except Exception as err:
            e = self._last_element.element.etree_element
            s = self._last_element.style
            error = "{}\n<{} {}/>\n{}".format(err,
                    e.tag,
                    ' '.join(['{}="{}"'.format(a, v) for a, v in e.items()]),
                    '\n'.join(['{}: {};'.format(a, tinycss2.serialize(n)) for a, n in s.items()])
                    )
        if error:
            raise SyntaxError(error)

        try:
            self._diagram.position_elements()
        except Exception as err:
            error = "{}".format(err)
        if error:
            raise SyntaxError(error)

        logging.debug('')

        # For all fluxes
        # parse 'line' attribute
        # assign line segments

        return (self._diagram, self._bond_graph)

# -----------------------------------------------------------------------------

