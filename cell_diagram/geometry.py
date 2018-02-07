#------------------------------------------------------------------------------

from . import SyntaxError

#------------------------------------------------------------------------------

class Geometry(object):
    def __init__(self, size=None, units='percentage'):
        self._size = Geometry.parse_numeric_tuple(size)
        if 0.0 in self._size: raise ValueError
        if   units == 'percentage': self._divisor = (100.0, 100.0)
        elif units == 'fractional': self._divisor = (1.0, 1.0)
        elif units == 'bounding-box': self._divisor = self._size
        else: raise SyntaxError

    @staticmethod
    def parse_numeric_tuple(text):
        return tuple(float(x) for x in text.replace(',', ' ').split()) if text else (0.0, 0.0)

    @property
    def size(self):
        return self._size

    def add_item(self, item):
        pass

    def add_box(self, item):
        pass

class Box(Geometry):
    def __init__(self, ref=None, size=None, pos=None):
        super().__init__(size=size)
        self._ref = ref
        self._pos = Geometry.parse_numeric_tuple(pos)

    @property
    def top(self):
        return 0.0

    @property
    def left(self):
        return 0.0

    @property
    def bottom(self):
        return 1.0

    @property
    def right(self):
        return 1.0

class Item(object):
    def __init__(self, box, ref=None, pos=None, border=None):
        self._ref = ref
        position = Geometry.parse_numeric_tuple(pos)
        if   border == "top":    self._pos = (position[0], box.top)
        elif border == "left":   self._pos = (box.left, position[0])
        elif border == "bottom": self._pos = (position[0], box.bottom)
        elif border == "right":  self._pos = (box.right, position[0])
        else:                    self._pos = position

#------------------------------------------------------------------------------
