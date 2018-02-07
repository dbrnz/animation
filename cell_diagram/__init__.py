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
        self._geometry = None

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
    def find(cls, id):
        e = Element._elements.get(id)
        return e if e is not None and isinstance(e, cls) else None

    def set_geometry(self, geometry):
        self._geometry = geometry

    @property
    def geometry(self):
        return self._geometry

#------------------------------------------------------------------------------
