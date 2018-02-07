#------------------------------------------------------------------------------

class Geometry(object):
    def __init__(self, size=None, units='percentage'):
        self._size = Geometry.parse_numeric_tuple(size)
        self._divisor = 1.0 if units == 'fractional' else 100.0

    @staticmethod
    def parse_numeric_tuple(text):
        return tuple(float(x) for x in text.replace(',', ' ').split()) if text else (0.0, 0.0)

    @property
    def size(self):
        return self._size

class Box(object):
    def __init__(self, ref=None, size=None, pos=None):
        self._ref = ref
        self._size = Geometry.parse_numeric_tuple(size)
        self._pos = Geometry.parse_numeric_tuple(pos)

class Item(object):
    def __init__(self, box=box, ref=None, pos=None, border=None):
        self._ref = ref
        position = Geometry.parse_numeric_tuple(pos)
        if   border == "left":   self._pos = (box.left, position[0])
        elif border == "right":  self._pos = (box.right, position[0])
        elif border == "top":    self._pos = (position[0], box.top)
        elif border == "bottom": self._pos = (position[0], box.bottom)
        else:                    self._pos = position

    @property
    def fixed(self):
        return self._fixed

    @property
    def fixed_coords(self):
        return self._fixed_coords

    def add_position(self, element=None, coords=None):
        if element is not None and coords is not None:
            c = coords.replace(',', ' ').split()
            if len(c) >= 2:
                self._positions[element] = tuple(float(x) for x in c[0:2])
                if   c[-1].lower() == 'x-fixed':
                    self._fixed_coords[element] = (True, False)
                elif c[-1].lower() == 'y-fixed':
                    self._fixed_coords[element] = (False, True)
                else:
                    self._fixed.append(element)
    '''
    def set_relative_position(self, left_of=None, below=None):
        if left_of is not None:
            self._elements_right.append(left_of)
            left_of._elements_left.append(self)
        if below is not None:
            self._elements_above.append(below)
            below._elements_below.append(self)
    '''

#------------------------------------------------------------------------------
