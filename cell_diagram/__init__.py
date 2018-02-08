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

class SyntaxError(Exception):
    pass

#------------------------------------------------------------------------------

class Element(object):
    # Dictionary of all elements that have an id
    _elements = { }

    def __init__(self, _class=None, id=None, label=None, style=None):
        self._class = _class
        self._id = id
        self._label = label if label else id
        if id is not None:
            Element._elements[id] = self
        self._style = style
        self._position = None
        self._size = None

    @property
    def id(self):
        return self._id

    @property
    def label(self):
        return self._label

    @property
    def style(self):
        return self._style

    @classmethod
    def reset(cls):
        Element._elements.clear()

    @classmethod
    def find(cls, id):
        e = Element._elements.get(id)
        return e if e is not None and isinstance(e, cls) else None

    def set_position(self, position):
        self._position = position

    def set_size(self, size):
        self._size = size

    @property
    def position(self):
        return self._position

    @property
    def size(self):
        return self._size

#------------------------------------------------------------------------------
