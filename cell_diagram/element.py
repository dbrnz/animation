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

from . import diagram
from . import layout
from . import parser
from . import svg_elements
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
        self._classes = class_.split() if class_ is not None else []
        self._label = label if label else '\\text{{{}}}'.format(name)
        self._style = style if style is not None else {}
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

    @property
    def colour(self):
        tokens = self._style.get('colour', self._style.get('color', None))
        if tokens is None:
            return '#808080'
        colour = parser.get_colour(parser.StyleTokens(tokens))
        return colour

    @property
    def stroke(self):
        return self.get_style_as_string('stroke', 'none')

    @property
    def stroke_width(self):
        return self.get_style_as_string('stroke-width', '1')

    def get_style_as_string(self, name, default=None):
        tokens = self._style.get(name, None)
        return (' '.join([str(t.value) if t.type != 'hash' else ('#' + t.value)
                           for t in tokens if t.type not in ['comment', 'whitespace']])
                if tokens is not None else default)

    def is_class(self, name):
        return name in self._classes

    def set_container(self, container):
        self._container = container

    def display(self):
        d = self.get_style_as_string('display')
        return ' display="{}"'.format(d) if d else ''

    def id_class(self):
        s = ['']
        if self._id is not None:
            s.append('id="{}"'.format(self._id[1:]))
        if self._classes:
            s.append('class="{}"'.format(' '.join(self._classes)))
        return ' '.join(s)

# -----------------------------------------------------------------------------


class PositionedElement(object):
    def __init__(self):
        self._position = layout.Position(self)
        self._position.add_dependency(self._container)
        # We delay parsing until all the XML has been parsed and
        # do so when we start resolving positions.
        self._position_tokens = parser.StyleTokens.create(self._style, 'position')
        self._geometry = None

    @property
    def position(self):
        return self._position

    @property
    def position_resolved(self):
        return self._position is not None and self._position.resolved

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

    def parse_geometry(self, default_offset=None, default_dependency=None):
        """
        * Position as coords: absolute or % of container -- `(100, 300)` or `(10%, 30%)`
        * Position as offset: relation with absolute offset from element(s) -- `300 above #q1 #q2`
        """
        if self._position_tokens is not None:
            self.position.parse(self._position_tokens, default_offset, default_dependency)

    def svg(self):
        svg = ['<g{}{}>'.format(self.id_class(), self.display())]
        if self.position.has_coords:
            (x, y) = self.coords
            svg.append(('  <circle r="{}" cx="{}" cy="{}"'
                        ' stroke="{}" stroke-width="{}" fill="{}"/>')
                       .format(layout.ELEMENT_RADIUS, x, y, self.stroke, self.stroke_width, self.colour))
            if isinstance(self, diagram.Transporter):  ## TODO: Improve...
                svg.append(svg_elements.Text.typeset(self.label, x, y))
            else:
                svg.append(('  <text text-anchor="middle" dominant-baseline="central"'
                            ' x="{}" y="{}">{}</text>').format(x, y, self._local_name))
        svg.append('</g>')
        return svg




# -----------------------------------------------------------------------------
