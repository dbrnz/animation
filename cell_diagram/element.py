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

from . import layout
from . import parser
from . import SyntaxError

# -----------------------------------------------------------------------------


class Element(object):
    def __init__(self, container, class_name='Element',
                 class_=None, id=None, name=None, label=None, style=None):
        self._container = container
        self._class_name = class_name
        self._class = class_
        self._id = ('#' + id) if id is not None else None
        if name is None:
            name = id if id is not None else ''
        self._local_name = name
        self._full_name = ((container.full_name + '/' + name)
                           if (container and container.full_name and name)
                           else None)
        self._label = label if label else name
        self._position = layout.Position(self)
        pos_tokens = style.pop('position', None) if style else None
        if pos_tokens:
            self.parse_position(self._position, pos_tokens)
        self._style = style

    def __str__(self):
        s = [self._class_name]
        if self._id:
            s.append('({})'.format(self._id))
        return ' '.join(s)

    @property
    def id(self):
        return self._id

    @property
    def label(self):
        return self._label

    @property
    def container(self):
        return self._container

    @property
    def position(self):
        return self._position

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

    def parse_position(self, position, tokens):
        pass

    def svg(self, stroke='none', fill='#cccccc'):
        svg = ['<g{}>'.format(self.id_class())]
        if self.position.has_coords:
            (x, y) = self.position.coords
            svg.append(('  <circle r="10.0" cx="{:g}" cy="{:g}"'
                        ' stroke="{:s}" fill="{:s}"/>')
                       .format(x, y, stroke, fill))
            svg.append('  <text x="{:g}" y="{:g}">{:s}</text>'
                       .format(x-9, y+6, self._label))
        svg.append('</g>')
        return svg

# -----------------------------------------------------------------------------

class PositionedElement(object):

    def parse_position(self, position, tokens):
        """
        * Position as coords: absolute or % of container -- `(100, 300)` or `(10%, 30%)`
        * Position as offset: relation with absolute offset from element(s) -- `300 above #q1 #q2`
        """

        dependencies = []
        try:
            token = tokens.next()
            if token.type == '() block':
                lengths, _ = parser.get_coordinates(parser.StyleTokens(token.content))
                position.set_lengths(lengths)
            else:
                tokens.back()
                offset, tokens = parser.get_offset(tokens)
                token = tokens.next()
                if token.type == 'ident' and token.lower_value in layout.OFFSET_RELATIONS:
                    reln = token.lower_value
                    token = tokens.peek()
                    if token is None or token.type != 'hash':
                        raise SyntaxError("Identifier(s) expected")
                    while token.type == 'hash':
                        try:
                            token = tokens.next()
                            dependencies.append('#' + token.value)
                        except StopIteration:
                            break
                    print('Depend for', self, dependencies)
                    position.add_relationship(offset, reln, dependencies)
        except StopIteration:
            pass

        if tokens.peek() is not None:
            raise SyntaxError("Invalid syntax")

        position.add_dependencies(dependencies + [self.container])

# -----------------------------------------------------------------------------
