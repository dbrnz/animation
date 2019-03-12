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

from math import cos, sin, asin, pi

# -----------------------------------------------------------------------------

from . import mathjax

# -----------------------------------------------------------------------------

from . import utils

# -----------------------------------------------------------------------------

LINE_WIDTH  = 2

# -----------------------------------------------------------------------------

def generate(elements, layer, excludes):
    svg = []
    for e in elements:
        if utils.layer_matches(layer, e.classes, excludes):
            svg.extend(e.svg())
    return svg

# -----------------------------------------------------------------------------

class SvgElement(object):
    def __init__(self, id, id_base):
        self._id = id
        self._id_base = id_base

# -----------------------------------------------------------------------------

class DefinesStore(object):
    _ids = []
    _svg_to_id = {}
    _id_to_svg = {}

    @classmethod
    def add(cls, id, svg):
        if id not in cls._ids:
            cls._ids.append(id)
            cls._svg_to_id[svg] = id
            cls._id_to_svg[id] = svg
        return "url(#{})".format(id)

    @classmethod
    def get_url(cls, svg):
        id = cls._svg_to_id.get(svg, None)
        if id is not None:
            return "url(#{})".format(id)

    @classmethod
    def defines(cls):
        return cls._id_to_svg.values()

    @classmethod
    def reset(cls, top):
        for id in cls._ids[top:]:
            svg = cls._id_to_svg.pop(id)
            cls._svg_to_id.pop(svg)
        del cls._ids[top:]

    @classmethod
    def top(cls):
        return len(cls._ids)

# -----------------------------------------------------------------------------


class Gradient(object):
    _next_id = 0

    @classmethod
    def next_id(cls):
        cls._next_id += 1
        return "_GRADIENT_{}_".format(cls._next_id)

    def __init__(self, gradient, stop_colours):
        self._gradient = gradient
        self._stop_colours = stop_colours

    @classmethod
    def url(cls, gradient, stop_colours):
        self = cls(gradient, stop_colours)
        url = DefinesStore.get_url(self)
        if url is None:
            id = cls.next_id()
            url = DefinesStore.add(id, self.svg(id))
        return url

    def __eq__(self, other):
        return (isinstance(other, Gradient)
            and self._gradient == other._gradient
            and self._stop_colours == other._stop_colours)

    def __hash__(self):
        return hash((self._gradient, str(self._stop_colours)))

    def svg(self, id):
        stops = []
        nstops = len(self._stop_colours)
        for n, stop in enumerate(self._stop_colours):
            if n > 0:
                offset = ' offset="{}%"'.format(stop[1] if stop[1] is not None else n*100.0/(nstops-1))
            else:
                offset = ' offset="{}%"'.format(stop[1]) if stop[1] is not None else ''
            stops.append('<stop{} stop-color="{}"/>'.format(offset, stop[0]))
        return ('<{gradient}Gradient id="{id}">{stops}</{gradient}Gradient>'
                .format(gradient=self._gradient, id=id, stops='/n'.join(stops)))

# -----------------------------------------------------------------------------


class CellMembrane(SvgElement):
    SVG_DEFS="""
        <g id="{ID_BASE}_base_element">
            <circle cx="0" cy="0" r="{RADIUS}" stroke-width="{WIDTH}"/>
            <line x1="{RADIUS}" y1="0" x2="{TAIL}" y2="0" stroke-width="{WIDTH}"/>
        </g>
        <!-- Inward pointing marker -->
        <marker id="{ID_BASE}_inward_marker" markerUnits="userSpaceOnUse" style="overflow: visible" orient="auto">
            <use stroke="{STROKE}" fill="{FILL}" xlink:href="#{ID_BASE}_base_element" transform="rotate(270)"/>
        </marker>
        <!-- Outward pointing marker -->
        <marker id="{ID_BASE}_outward_marker" markerUnits="userSpaceOnUse" style="overflow: visible" orient="auto">
            <use stroke="{STROKE}" fill="{FILL}" xlink:href="#{ID_BASE}_base_element" transform="rotate(90)"/>
        </marker>
        <!-- Straight segments are built from two base elements at 180 degrees to each other -->
        <g id="{ID_BASE}_element">
            <use transform="translate({OFFSET}, {SPACING})" xlink:href="#{ID_BASE}_base_element"/>
            <use transform="rotate(180) translate({OFFSET}, 0)" xlink:href="#{ID_BASE}_base_element"/>
        </g>
        <!-- Marker for straight segments -->
        <marker id="{ID_BASE}_marker" markerUnits="userSpaceOnUse" style="overflow: visible" orient="auto">
            <use stroke="{STROKE}" fill="{FILL}" xlink:href="#{ID_BASE}_element" transform="rotate(90)"/>
        </marker>"""

    def __init__(self, id, width, height, id_base='cell_membrane',
                 outer_markers=9, inner_markers=3, marker_radius=4,
                 stroke_width=1, stroke_colour='#0092DF', fill_colour='#BFDDFF'):
        """
        :param outer_markers: Number of outer markers in a corner.
        :param immer_markers: Number of inner markers in a corner.
        """
        super().__init__(id, id_base)
        self._outer_markers = outer_markers
        self._inner_markers = inner_markers
        self._marker_radius = marker_radius
        self._stroke_width = stroke_width
        self._stroke_colour = stroke_colour
        self._fill_colour = fill_colour
        # Computed parameters
        self._marker_width = 2.0*marker_radius + self._stroke_width
        self._outer_marker_angle = 90/self._outer_markers
        self._outer_radius = self._marker_width/(2*asin(pi/(4*self._outer_markers)))
        self._inner_marker_angle = 90/self._inner_markers
        self._inner_radius = self._marker_width/(2*asin(pi/(4*self._inner_markers)))
        # The thickness of straight lines
        self._line_width = self._outer_radius - self._inner_radius
        self._marker_tail = 0.9*(self._line_width - self._marker_radius - self._stroke_width)
        # We round the width and height to ensure an integral number of line markers will fit on a side
        self._horizontal_markers = int(0.5 + (width - self._line_width/2.0 - 3*self._inner_radius)/self._marker_width)
        self._vertical_markers = int(0.5 + (height - self._line_width/2.0 - 3*self._inner_radius)/self._marker_width)
        # The size of the straight line portion
        self._inner_width = self._marker_width*self._horizontal_markers
        self._inner_height = self._marker_width*self._vertical_markers
        # The size of the bounding box
        self._outer_width = self._inner_width + 2*self._outer_radius
        self._outer_height = self._inner_height + 2*self._outer_radius
        # The <defs> element for the membrane
        DefinesStore.add(id_base, self.SVG_DEFS.format(RADIUS=marker_radius,
                                                       TAIL=self._marker_tail,
                                                       WIDTH=stroke_width,
                                                       STROKE=stroke_colour,
                                                       FILL=fill_colour,
                                                       ID_BASE=id_base,
                                                       OFFSET=-self._line_width/2.0,
                                                       SPACING=-self._marker_width/2.0))

    @property
    def width(self):
        return self._outer_width - self._line_width

    @property
    def height(self):
        return self._outer_height - self._line_width

    @property
    def thickness(self):
        return self._line_width

    def corner_path(self, outer_path):
        transform = [ ]
        if outer_path:
            R = self._outer_radius
            dt = self._outer_marker_angle*pi/180
            marker_id = '{}_inward_marker'.format(self._id_base)
            count = self._outer_markers
            transform.append('rotate({:g})'.format(self._outer_marker_angle/2.0))
        else:
            R = self._inner_radius
            dt = self._inner_marker_angle*pi/180
            marker_id = '{}_outward_marker'.format(self._id_base)
            count = self._inner_markers
        transform.append('translate(0, {:g})'.format(R))
        path = ['M0,0']
        t = 0
        for n in range(count+1):
            path.append('a0,0 0 0,0 {:g},{:g}'.format(R*(sin(t+dt)-sin(t)), R*(cos(t+dt)-cos(t))))
            t += dt
        return '''
      <g transform="{transform}">
        <path stroke="none" fill="none" marker-mid="url(#{marker})" d="{path}"/>
      </g>'''.format(transform=' '.join(transform), marker=marker_id, path=' '.join(path))

    def corner(self, position):
        outer_radius = self._outer_radius
        outer_path = self.corner_path(True)
        svg = []
        rotation = (180 if position == 'top_left' else
                    270 if position == 'top_right' else
                    90 if position == 'bottom_left' else
                    0)
        translation = ((0, 0) if position == 'top_left' else
                       (0, self._inner_width) if position == 'top_right' else
                       (self._inner_height, 0) if position == 'bottom_left' else
                       (self._inner_width, self._inner_height)
                      )
        svg.append('<g id="{}_{}"'.format(self._id_base, position)
            + ' transform="translate({:g}, {:g}) rotate({:g}) translate({:g}, {:g})">'
               .format(outer_radius, outer_radius, rotation, *translation))
        svg.append(outer_path)
        svg.append(self.corner_path(False))
        svg.append('</g>')
        return svg

    def side(self, orientation):
        translation = ((0, 0) if orientation == 'top' else
                       (self._marker_width/2.0, self.height) if orientation == 'bottom' else
                       (0, self._marker_width/2.0) if orientation == 'left' else
                       (self.width, 0))
        marker_id = '{}_marker'.format(self._id_base)
        if orientation in ['top', 'bottom']:
            path = ['M{:g},{:g}'.format(self._outer_radius, self._line_width/2.0)]
            count = self._horizontal_markers
            step_format = 'l{:g},0'
        else:
            path = ['M{:g},{:g}'.format(self._line_width/2.0, self._outer_radius)]
            count = self._vertical_markers
            step_format = 'l0,{:g}'
        for n in range(count):
            path.append(step_format.format(self._marker_width))
        return ['''
      <g id="{id}_{orientation}" transform="translate({trans_x}, {trans_y})">
        <path stroke="none" fill="none"  d="{path}"
              marker-start="url(#{marker})" marker-mid="url(#{marker})"/>
      </g>'''.format(id=self._id_base, orientation=orientation,
                     trans_x=translation[0], trans_y=translation[1],
                     path=' '.join(path), marker=marker_id)]

    def svg(self, outline=False):
        svg = []
        svg.append('<g transform="translate({:g},{:g})">'.format(-self._line_width/2.0, -self._line_width/2.0))
        svg.extend(self.corner('top_left'))
        svg.extend(self.corner('top_right'))
        svg.extend(self.corner('bottom_left'))
        svg.extend(self.corner('bottom_right'))
        svg.extend(self.side('top'))
        svg.extend(self.side('left'))
        svg.extend(self.side('bottom'))
        svg.extend(self.side('right'))
        if outline:
            svg.append('<path stroke="#0000FF" fill="none" d="M0,0 L{R:g},0 L{R:g},{B:g} L0,{B:g} z"/>'
                       .format(R=self._outer_width, B=self._outer_height))
        svg.append('</g>')
        if outline:
            svg.append('<path stroke="#FF0000" fill="none" d="M0,0 L{R:g},0 L{R:g},{B:g} L0,{B:g} z"/>'
                       .format(R=self.width, B=self.height))
        return '\n'.join(svg)

# -----------------------------------------------------------------------------


class _TransporterElement(SvgElement):
    def __init__(self, id, coords, rotation, height, defs, defined_height, id_base):
        super().__init__(id, id_base)
        self._coords = coords
        self._rotation = rotation
        self._height = height
        self._defined_height = defined_height
        DefinesStore.add(id_base, defs.format(ID_BASE=id_base))

    def svg(self):
        svg = ['<use xlink:href="#{ID_BASE}_element" transform="translate({X:g}, {Y:g})'
               .format(ID_BASE=self._id_base, X=self._coords[0], Y=self._coords[1])]
        scaling = self._height/float(self._defined_height)
        if scaling != 1.0:
            svg.append(' scale({})'.format(scaling))
        if self._rotation != 0:
            svg.append(' rotate({})'.format(self._rotation))
        svg.append('" />')
        return ''.join(svg)

# -----------------------------------------------------------------------------


class Channel(_TransporterElement):
    SVG_DEFS="""
        <linearGradient id="{ID_BASE}_fill">
          <stop offset="0%"    stop-color="#57FAFF"/>
          <stop offset="13.5%" stop-color="#45C8D2"/>
          <stop offset="30.4%" stop-color="#328F9F"/>
          <stop offset="46.8%" stop-color="#216175"/>
          <stop offset="62.4%" stop-color="#153C54"/>
          <stop offset="76.8%" stop-color="#0B223C"/>
          <stop offset="89.8%" stop-color="#06132E"/>
          <stop offset="100%"  stop-color="#040D29"/>
        </linearGradient>
        <path id="{ID_BASE}_sub_element" fill="url(#{ID_BASE}_fill)"
          d="M0,0 a10,10 0 0 1 20,0 v80 a10,10 0 0 1 -20,0 v-80 z"/>
        <g id="{ID_BASE}_element" transform="translate(-10, -40)">
          <use opacity="0.85" xlink:href="#{ID_BASE}_sub_element" transform="translate(  0, -5)"/>
          <use opacity="0.85" xlink:href="#{ID_BASE}_sub_element" transform="translate( 15,  0)" />
          <use opacity="0.75" xlink:href="#{ID_BASE}_sub_element" transform="translate(-15,  0)" />
          <use opacity="0.60" xlink:href="#{ID_BASE}_sub_element" transform="translate( -1,  5)" />
        </g>"""

    HEIGHT = 100
    WIDTH = 50

    def __init__(self, id, coords, rotation, height=0.6*HEIGHT, id_base='channel'):
        super().__init__(id, coords, rotation, height, self.SVG_DEFS, self.HEIGHT, id_base)

# -----------------------------------------------------------------------------


class Exchanger_TO_FINISH(_TransporterElement):
    def __init__(self, id, coords, rotation, height=40, id_base='exchanger'):
        super().__init__(id, coords, rotation, height, '', height, id_base)

# -----------------------------------------------------------------------------


class PMRChannel(_TransporterElement):
    SVG_DEFS="""
        <radialGradient id="{ID_BASE}_fill">
            <stop offset="0%"     stop-color="#FBFAE2"/>
            <stop offset="12.03%" stop-color="#FCFADD"/>
            <stop offset="26.62%" stop-color="#FFF9CD"/>
            <stop offset="42.55%" stop-color="#FCF6B4"/>
            <stop offset="59.43%" stop-color="#FDEF90"/>
            <stop offset="77.06%" stop-color="#FEE863"/>
            <stop offset="95.06%" stop-color="#FEE12A"/>
            <stop offset="100%"   stop-color="#FEDE12"/>
        </radialGradient>
        <path id="{ID_BASE}_element" fill="url(#{ID_BASE}_fill)"  transform="scale(1.1) translate(-22, -25)"
            stroke="#010101" stroke-width="2" stroke-linejoin="miter"
            d="M0,0 c0,-25 15,-30 22,-12 c7,-18 22,-13 22,12 v50 c0,25 -15,30 -22,12 c-7,18 -22,13 -22,-12 v-50 z"/>
        <marker id="{ID_BASE}_arrow" orient="auto" style="overflow: visible">
            <path fill="010101" transform="rotate(90) translate(0, 0) scale(0.5)"
                  d="M0,0l5,3.1l0.1-0.2l-3.3-8.2l-1.9-8.6l-1.9,8.6l-3.3,8.2l0.1,0.2l5-3.1z"/>
        </marker>
        <g id="{ID_BASE}_in_element">
          <path stroke="#010101" stroke-width="2" d="M0,-65 v130" marker-end="url(#{ID_BASE}_arrow)"/>
          <use xlink:href="#{ID_BASE}_element"/>
        </g>
        <g id="{ID_BASE}_out_element">
          <use xlink:href="#{ID_BASE}_in_element" transform="rotate(180)"/>
        </g>
        <g id="{ID_BASE}_inout_element">
          <use xlink:href="#{ID_BASE}_in_element"/>
          <use xlink:href="#{ID_BASE}_in_element" transform="rotate(180)"/>
        </g>"""

    HEIGHT = 80
    WIDTH = 44

    def __init__(self, id, coords, rotation, height=0.6*HEIGHT, id_base='pmr_channel'):
        super().__init__(id, coords, rotation, height, self.SVG_DEFS, self.HEIGHT, id_base)

# -----------------------------------------------------------------------------

class PMRChannelIn(PMRChannel):
    def __init__(self, id, coords, rotation, height=0.6*PMRChannel.HEIGHT, id_base='pmr_channel'):
        super().__init__(id, coords, rotation, height, id_base)
        self._id_base = self._id_base + '_in'

# -----------------------------------------------------------------------------

class PMRChannelOut(PMRChannel):
    def __init__(self, id, coords, rotation, height=0.6*PMRChannel.HEIGHT, id_base='pmr_channel'):
        super().__init__(id, coords, rotation, height, id_base)
        self._id_base = self._id_base + '_out'

# -----------------------------------------------------------------------------

class PMRChannelInOut(PMRChannel):
    def __init__(self, id, coords, rotation, height=0.6*PMRChannel.HEIGHT, id_base='pmr_channel'):
        super().__init__(id, coords, rotation, height, id_base)
        self._id_base = self._id_base + '_inout'

# -----------------------------------------------------------------------------

class Arrow(object):
    _next_id = 0

    @classmethod
    def next_id(cls):
        cls._next_id += 1
        return "_ARROW_{}_".format(cls._next_id)

    def __init__(self, colour):
        self._colour = colour

    @classmethod
    def url(cls, colour):
        self = cls(colour)
        url = DefinesStore.get_url(self)
        if url is None:
            id = cls.next_id()
            url = DefinesStore.add(id, self.svg(id))
        self._url = url
        return url

    def __eq__(self, other):
        return (isinstance(other, Arrow)
            and self._colour == other._colour)

    def __hash__(self):
        return hash(self._colour)

    def svg(self, id):
        return """
            <marker id="{id}" orient="auto" style="overflow: visible">
                <path fill="{fill}" transform="rotate(90) translate(0, 5) scale(0.5)"
                      d="M0,0l5,3.1l0.1-0.2l-3.3-8.2l-1.9-8.6l-1.9,8.6l-3.3,8.2l0.1,0.2l5-3.1z"/>
            </marker>""".format(id=id, fill=self._colour)

# -----------------------------------------------------------------------------

def svg_line(line, colour, reverse=False, display='', style=''):
    points = list(reversed(line.coords)) if reverse else line.coords
    dash = ' stroke-dasharray="10,5"' if style == 'dashed' else ''
    return ('<path fill="none" stroke="{}" stroke-width="{}" {} {}'
            ' marker-end="{}" d="M{:g},{:g} {:s}"/>').format(colour, LINE_WIDTH,
                   display, dash, Arrow.url(colour), points[0][0], points[0][1],
                   ' '.join(['L{:g},{:g}'.format(*point) for point in points[1:]]))

# -----------------------------------------------------------------------------

class Text(object):
    _next_id = 0

    @classmethod
    def next_id(cls):
        cls._next_id += 1
        return "_TEXT_{}_".format(cls._next_id)

    @classmethod
    def typeset(cls, s, x, y, rotation=0):
        svg, size = mathjax.typeset(s, cls.next_id())
        w, h, va = (6*float(size[0][:-2]), 6*float(size[1][:-2]), 6*float(size[2][:-2]))
        # Use viewBox in size[3] to calculate scaling
        # Rotate text but first need to find center
        return ('<g transform="translate({}, {}) scale(0.015)">{}</g>'
                .format(x-w/2, y+h/2 + va, svg))
#        return ('<g transform="translate({}, {}) rotate({}, {}, {}) scale(0.017)">{}</g>'
#                .format(x-w/2, y+h/2 + va, rotation, w, -h, svg))

# -----------------------------------------------------------------------------

if __name__ == '__main__':

    def wrap_svg(svg):
        return """<?xml version="1.0" standalone="no"?>
    <svg  version="1.1" xmlns="http://www.w3.org/2000/svg"
          width="800" height="400"
          viewBox="-10 -10 400 300">
          {SVG:s}
    </svg>""".format(SVG=svg)

    membrane = CellMembrane('cell', 300, 200)
      #, outer_markers=12, inner_markers=8, marker_tail=10, stroke_width=0.5)
      #, marker_radius=5, marker_tail=35)
    svg = wrap_svg(membrane.svg())
    f = open('../m.svg', 'w')
    f.write(svg)
    f.close()
