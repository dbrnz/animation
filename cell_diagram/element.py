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

import shapely.geometry as geo

# -----------------------------------------------------------------------------

from . import layout
from . import parser
from . import SyntaxError

# -----------------------------------------------------------------------------


class Element(object):
    def __init__(self, container, class_name='Element',
                 class_=None, id=None, name=None, label=None, style=None):
        self._id = ('#' + id) if id is not None else None
        if name is None:
            name = id if id is not None else ''
        self._local_name = name
        if self == container:
            self._container = None
            self._diagram = self
            self._full_name = '/'
        else:
            self._container = container
            self._diagram = container.diagram
            self._full_name = ((container.full_name + '/' + name)
                               if (container and container.full_name and name)
                               else None)
        self._class_name = class_name
        self._class = class_
        self._label = label if label else name
        self._style = style
        super().__init__()   # Now initialise any PositionedElement mixin

    def __str__(self):
        s = [self._class_name]
        if self._id:
            s.append('({})'.format(self._id))
        return ' '.join(s)

    @property
    def full_name(self):
        return self._full_name

    @property
    def id(self):
        return self._id

    @property
    def label(self):
        return self._label

    @property
    def local_name(self):
        return self._local_name

    @property
    def diagram(self):
        return self._diagram

    @property
    def container(self):
        return self._container

    @property
    def style(self):
        return self._style

    def set_container(self, container):
        self._container = container

    def id_class(self):
        s = []
        if self._id is not None:
            s.append(' id="{}"'.format(self._id))
        if self._class is not None:
            s.append(' class="{}"'.format(self._class))
        return ''.join(s)

# -----------------------------------------------------------------------------


class PositionedElement(object):
    def __init__(self):
        self._position = layout.Position(self)
        self._position.add_dependency(self._container)
        # We delay parsing until all the XML has been parsed and
        # do so when we start resolving positions.
        pos_tokens = self._style.get('position', None) if self._style else None
        self._position_tokens = parser.StyleTokens(pos_tokens) if pos_tokens else None
        self._geometry = None

    @property
    def position(self):
        return self._position

    @property
    def coords(self):
        return self._position.coords

    @property
    def geometry(self):
        if self._geometry is None and self.position.has_coords:
            self._geometry = geo.Point(self.coords)
        return self._geometry

    def resolve_position(self):
        self._position.resolve()

    def parse_position(self, default_offset=None, default_dependency=None):
        """
        * Position as coords: absolute or % of container -- `(100, 300)` or `(10%, 30%)`
        * Position as offset: relation with absolute offset from element(s) -- `300 above #q1 #q2`
        """
        if self._position_tokens is None:
            return
        tokens = self._position_tokens
        element_dependencies = []
        token = tokens.peek()
        if token.type == '() block':
            tokens.next()
            lengths, _ = parser.get_coordinates(parser.StyleTokens(token.content))
            self._position.set_lengths(lengths)
        else:
            seen_horizontal = False
            seen_vertical = False
            while True:
                dependencies = []
                using_default = token.type not in ['number', 'dimension', 'percentage']
                offset, tokens = parser.get_length(tokens, default=default_offset)
                token = tokens.next()
                if (token.type != 'ident'
                 or token.lower_value not in layout.POSITION_RELATIONS):
                    raise SyntaxError("Unknown relationship for position.")
                reln = token.lower_value
                token = tokens.peek()
                if ((token is None or token ==',')
                 and default_dependency is not None):
                    dependencies.append(default_dependency)
                elif (token is None
                  or (token.type != 'hash' and token != ',')):
                    raise SyntaxError("Identifier(s) expected")
                else:
                    tokens.next()   # We peeked above...
                    while token.type == 'hash':
                        try:
                            dependencies.append('#' + token.value)
                            token = tokens.next()
                        except StopIteration:
                            break
                if token == ',':
                    if using_default:
                        # No default offsets if two (or more) constraints
                        offset = None
                    if (seen_horizontal and reln in layout.HORIZONTAL_RELN
                     or seen_vertical and reln in layout.VERTICAL_RELN):
                        raise SyntaxError("Constraints must have different directions.")
                self._position.add_relationship(offset, reln, dependencies)
                element_dependencies.extend(dependencies)
                seen_horizontal = reln in layout.HORIZONTAL_RELN
                seen_vertical = reln in layout.VERTICAL_RELN
                if token == ',':
                    continue
                elif tokens.peek() is None:
                    break
                else:
                    raise SyntaxError("Invalid syntax")
        self._position.add_dependencies(element_dependencies)

    def svg(self, stroke='none', fill='#cccccc'):
        svg = ['<g{}>'.format(self.id_class())]
        if self.position.has_coords:
            (x, y) = self.coords
            svg.append(('  <circle r="10.0" cx="{:g}" cy="{:g}"'
                        ' stroke="{:s}" fill="{:s}"/>')
                       .format(x, y, stroke, fill))
            svg.append('  <text x="{:g}" y="{:g}">{:s}</text>'
                       .format(x-9, y+6, self._local_name))
        svg.append('</g>')
        return svg




# -----------------------------------------------------------------------------
