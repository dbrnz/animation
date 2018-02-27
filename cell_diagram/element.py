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

# -----------------------------------------------------------------------------


class Element(object):
    def __init__(self, container, class_name='Element',
                 _class=None, id=None, label=None, style=None):
        self._container = container
        self._class_name = class_name
        self._class = _class
        self._id = id
        self._label = label if label else id if id else ''
        self._position = layout.Position(self, style.pop('position', '')
                                         if style is not None else '')
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

    def svg(self, stroke='none', fill='#cccccc'):
        svg = ['<g{}>'.format(self.id_class())]
        if self.position.has_coords:
            (x, y) = self.position.coords
            svg.append(('  <circle r="10.0" cx="{:g}" cy="{:g}"'
                        ' stroke="{:s}" fill="{:s}"/>')
                       .format(x, y, stroke, fill))
            svg.append('  <text x="{:g}" y="{:g}">{:s}</text>'
                       .format(x-9, y+6, self._id))
        svg.append('</g>')
        return svg

# -----------------------------------------------------------------------------
