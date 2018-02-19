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

from . import layout

#------------------------------------------------------------------------------

class SyntaxError(Exception):
    pass

#------------------------------------------------------------------------------

class Element(object):
    def __init__(self, parent, _class=None, id=None, label=None, pos=None, size=None, style=None):
        self._parent = parent
        self._class = _class
        self._id = id
        self._label = label if label else id if id else ''
        self._position = layout.Position.from_string(pos) if pos is not None else None
        self._size = size
        self._style = style

    @property
    def coords(self):
        return self._position.coords if self._position else [None, None]

    @property
    def id(self):
        return self._id

    @property
    def label(self):
        return self._label

    @property
    def parent(self):
        return self._parent

    @property
    def position(self):
        return self._position

    @property
    def has_position_dependencies(self):
        return (len(self._position.dependencies) > 0) if self._position else None

    @property
    def size(self):
        return self._size

    @property
    def style(self):
        return self._style

    def add_position_dependency(self, id):
        if self._position: self._position.add_dependency(id)

    def id_class(self):
        s = []
        if self._id is not None: s.append(' id="{}"'.format(self._id))
        if self._class is not None: s.append(' class="{}"'.format(self._class))
        return ''.join(s)

    def set_size(self, size):
        self._size = size

    def svg(self, stroke='none', fill='#cccccc'):
        svg = ['<g{}>'.format(self.id_class())]
        if self._position is not None:
            (x, y) = self._position.position()
            svg.append('  <circle r="10.0" stroke="{stroke:s}" fill="{fill:s}" cx="{cx:g}" cy="{cy:g}"/>'.format(cx=x, cy=y, stroke=stroke, fill=fill))
            svg.append('  <text x="{x:g}" y="{y:g}">{text:s}</text>'.format(x=x-9, y=y+6, text=self._id))
        svg.append('</g>')
        return svg

#------------------------------------------------------------------------------
