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

from . import diagram as dia
from . import SyntaxError

#------------------------------------------------------------------------------

class Length(object):
    def __init__(self, length=0, units='%'):
        self._length = length
        self._units = units

    @property
    def length(self):
        return self._length

    @property
    def units(self):
        return self._units

    @classmethod
    def from_text(cls, text):
        len = cls()
        if   text.endswith('%'):
            length = float(text[:-1])/100.0
            units = '%'
        elif text.endswith('px'):
            length = float(text[:-2])
            units = 'px'
        else:
            raise SyntaxError("Missing units: '%' or 'px' required")
        return cls(length, units)

    def __str__(self):
        if self.units == '%': return '{:g}%'.format(100.0*self.length)
        else:                 return '{:g}px'.format(self.length)

    def __eq__(self, other):
        if self.units != other.units:
            raise TypeError('Units are different')
        else:
            return self.length == other.length

    def __ne__(self, other):
        return not (self == other)

    def __lt__(self, other):
        if self.units != other.units:
            raise TypeError('Units are different')
        else:
            return self.length < other.length

    def __le__(self, other):
        return (self < other) or (self == other)

    def __gt__(self, other):
        return not (self <= other)

    def __ge__(self, other):
        return not (self < other)

    def __add__(self, other):
        if self.units != other.units:
            raise TypeError('Units are different')
        else:
            return Length(self.length + other.length, self.units)

    def __sub__(self, other):
        if self.units != other.units:
            raise TypeError('Units are different')
        else:
            return Length(self.length - other.length, self.units)

    def __mul__(self, other):
        if self.units != other.units:
            return Length(self.length*other.length, 'px')
        elif self.is_percentage:
            return Length(self.length*other.length, '%')
        else:
            raise TypeError('Cannot multiply pixel lengths')

    def __truediv__(self, other):
        if self.units != other.units:
            raise TypeError('Units are different')
        elif other.length == 0:
            raise ZeroDivisionError
        else:
            return Length(self.length/other.length, '%')

    @property
    def is_percentage(self):
        return self._units == '%'

    @property
    def is_pixels(self):
        return self._units == 'px'

    def make_percentage_of(self, base):
        if self.is_percentage:
            return self
        elif base.is_percentage:
            raise TypeError('Base length must be in pixels')
        else:
            return Length(self.length/base.length, '%')

    def scale(self, ratio):
        return Length(ratio * self.length, self.units)

#------------------------------------------------------------------------------

class LengthTuple(object):
    def __init__(self, lengths):
        self._lengths = tuple(lengths)

    @classmethod
    def from_text(cls, text):
        return cls([Length.from_text(x) for x in text.split()] if text else [])

    def __len__(self):
        return len(self._lengths)

    def __str__(self):
        return '({})'.format(', '.join([str(l) for l in self._lengths]))

    def __iter__(self):
        for length in self._lengths:
            yield length
        raise StopIteration

    def __eq__(self, other):
        if len(self) != len(other):
            return False
        else:
            for n, l in enumerate(self._lengths):
                if l != other[n]: return False
            return True

    def __ne__(self, other):
        return not (self == other)

    def __add__(self, other):
        if len(self) != len(other):
            raise TypeError('Lengths are of different dimension')
        else:
            return LengthTuple([l + other[n] for n, l in enumerate(self._lengths)])

    def __sub__(self, other):
        if len(self) != len(other):
            raise TypeError('Lengths are of different dimension')
        else:
            return LengthTuple([l - other[n] for n, l in enumerate(self._lengths)])

    def __mul__(self, other):
        if len(self) != len(other):
            raise TypeError('Lengths are of different dimension')
        else:
            return LengthTuple([l*other[n] for n, l in enumerate(self._lengths)])

    def __truediv__(self, other):
        if len(self) != len(other):
            raise TypeError('Lengths are of different dimension')
        else:
            return LengthTuple([l/other[n] for n, l in enumerate(self._lengths)])

    def __getitem__(self, index):
        return self._lengths[index]

    def __contains__(self, value):
        return value in self._lengths

    @property
    def is_percentage(self):
        for l in self._lengths:
            if not l.is_percentage: return False
        return True

    @property
    def is_pixels(self):
        for l in self._lengths:
            if not l.is_pixels: return False
        return len(self) > 0

    def make_percentage_of(self, base):
        if len(self) != len(base):
            raise TypeError('Lengths are of different dimension')
        else:
            return LengthTuple([l.make_percentage_of(base[n]) for n, l in enumerate(self._lengths)])

    def scale(self, ratio):
        return LengthTuple([l.scale(ratio) for l in self._lengths])

#------------------------------------------------------------------------------

class GeometricObject(object):
    def __init__(self, pos=None, size=None):
        self._position = LengthTuple.from_text(pos)
        self._size = LengthTuple.from_text(size)

    @property
    def position(self):
        return self._position

    @property
    def size(self):
        return self._size

    @property
    def width(self):
        return self._size[0]

    @property
    def height(self):
        return self._size[1]

    def svg(self):
        return ''

#------------------------------------------------------------------------------

class Box(GeometricObject):
    def __init__(self, container=None, ref=None, **kwds):
        super().__init__(**kwds)
        self._ref = ref

        if not self.size:
            raise ValueError('Box cannot have zero size')

        if self.size.is_pixels:
            self._pixel_size = self.size
            if container is None:
                self._size = LengthTuple((Length(1.0), Length(1.0)))
            elif container.pixel_size:
                self._size = self.size.make_percentage_of(container.pixel_size)
            else:
                raise ValueError("Cannot use pixels if container's pixel size is unknown")
        elif not self.size.is_percentage:
            if container is None or not container.pixel_size:
                raise ValueError("Cannot use pixels if container's pixel size is unknown")
            self._size = self.size.make_percentage_of(container.pixel_size)
            self._pixel_size = self._size * container.pixel_size
        else:
            self._pixel_size = self._size * container.pixel_size

        if not self.position:
            self._position = LengthTuple((Length(), Length()))
        if not self.position.is_percentage:
            if container is None or not container.pixel_size:
                raise ValueError("Cannot use pixels if container's pixel size is unknown")
            self._position = self.position.make_percentage_of(container.pixel_size)

        self._boxes = []
        self._items = []
        if container:
            container.add_box(self)

    @property
    def pixel_size(self):
        return self._pixel_size

    def add_box(self, box):
        self._boxes.append(box)

    def add_item(self, item):
        self._items.append(item)

    def layout_diagram_elements(self, container_offset, container_size):
        top_left = container_offset + container_size * self.position
        size = container_size * self.size
        bottom_right = top_left + size
        if self._ref is not None:
            element = dia.Element.find(self._ref)
            if element is None:
                raise KeyError("Unknown diagram element '{}".format(self._ref))
            else:
                element.set_position((top_left[0].length, top_left[1].length))
                element.set_size((size[0].length, size[1].length))
        for box in self._boxes:
            box.layout_diagram_elements(top_left, size)
        for item in self._items:
            item.layout_diagram_elements(top_left, size)

#------------------------------------------------------------------------------

class Diagram(Box):
    def __init__(self, **kwds):
        super().__init__(**kwds)

    def layout_diagram_elements(self, width=None, height=None):
        if width is None: width = self._pixel_size[0].length
        if height is None: height = self._pixel_size[1].length
        super().layout_diagram_elements(LengthTuple((Length(0, 'px'), Length(0, 'px'))),
                                        LengthTuple((Length(width, 'px'), Length(height, 'px'))))

#------------------------------------------------------------------------------

class Item(GeometricObject):
    def __init__(self, container=None, ref=None, pos=None, boundary=None, **kwds):
        super().__init__(**kwds)
        self._ref = ref
        position = LengthTuple.from_text(pos)
        if not position.is_percentage and (container is None or not container.pixel_size):
            raise ValueError("Cannot use pixels if container's pixel size is unknown")
        if boundary is None:
            self._position = position.make_percentage_of(container.pixel_size)
        else:
            if   boundary == "top":    pos = (position[0], Length(0.0))
            elif boundary == "left":   pos = (Length(0.0), position[-1])
            elif boundary == "bottom": pos = (position[0], Length(1.0))
            elif boundary == "right":  pos = (Length(1.0), position[-1])
            self._position = LengthTuple(pos).make_percentage_of(container.pixel_size)
        if container:
            container.add_item(self)

    def layout_diagram_elements(self, container_offset, container_size):
        offset = container_offset + container_size * self.position
        pos = (offset[0].length, offset[1].length)
        if self._ref is not None:
            element = dia.Element.find(self._ref)
            if element is None:
                raise KeyError("Unknown diagram element '{}".format(self._ref))
            else:
                element.set_position(pos)

#------------------------------------------------------------------------------
