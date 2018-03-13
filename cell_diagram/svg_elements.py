from math import cos, sin, asin, pi

class CellMembrane(object):
    SVG_DEFS="""
      <defs>
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
            <use transform="translate({OFFSET}, -2.9)" xlink:href="#{ID_BASE}_base_element"/>
            <use transform="rotate(180) translate({OFFSET}, 0)" xlink:href="#{ID_BASE}_base_element"/>
        </g>
        <!-- Marker for straight segments -->
        <marker id="{ID_BASE}_marker" markerUnits="userSpaceOnUse" style="overflow: visible" orient="auto">
            <use stroke="{STROKE}" fill="{FILL}" xlink:href="#{ID_BASE}_element" transform="rotate(90)"/>
        </marker>
      </defs>"""

    # Number of outer markers in a corner
    OUTER_MARKERS = 9

    # Number of inner markers in a corner
    INNER_MARKERS = 3

    def __init__(self, id, width, height, id_base='cell_membrane',
                 marker_radius=2.4, marker_tail=17, stroke_width=1,
                 stroke_colour='#0092DF', fill_colour='#BFDDFF'):
        self._id = id
        self._id_base = id_base
        self._marker_radius = marker_radius
        self._marker_tail = marker_tail
        self._stroke_width = stroke_width
        self._stroke_colour = stroke_colour
        self._fill_colour = fill_colour
        # Computed parameters
        self._marker_width = 2.0*self._marker_radius + self._stroke_width
        self._outer_marker_angle = 90/self.OUTER_MARKERS
        self._outer_radius = self._marker_width/(2*asin(pi/(4*self.OUTER_MARKERS)))
        self._inner_marker_angle = 90/self.INNER_MARKERS
        self._inner_radius = self._marker_width/(2*asin(pi/(4*self.INNER_MARKERS)))

        self._line_width = self._outer_radius - self._inner_radius
        # We round the width and height to ensure an integral number of line markers will fit on a side
        self._horizontal_markers = int(0.5 + (width-2*self._outer_radius)/self._marker_width)
        self._vertical_markers = int(0.5 + (height-2*self._outer_radius)/self._marker_width)
        self._inner_width = self._marker_width*self._horizontal_markers
        self._inner_height = self._marker_width*self._vertical_markers
        self._width = self._inner_width + 2*self._outer_radius
        self._height = self._inner_height + 2*self._outer_radius

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    def corner_path(self, outer_path):
        transform = [ ]
        if outer_path:
            R = self._outer_radius
            dt = self._outer_marker_angle*pi/180
            marker_id = '{}_inward_marker'.format(self._id_base)
            transform.append('rotate({:g})'.format(self._outer_marker_angle/2.0))
        else:
            R = self._inner_radius
            dt = self._inner_marker_angle*pi/180
            marker_id = '{}_outward_marker'.format(self._id_base)
        transform.append('translate(0, {:g})'.format(R))
        path = ['M0,0']
        t = 0
        while t <= pi/2:
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
        rotation = (180 if position == 'top-left' else
                    270 if position == 'top-right' else
                    90 if position == 'bottom-left' else
                    0)
        translation = ((0, 0) if position == 'top-left' else
                       (0, self._inner_width) if position == 'top-right' else
                       (self._inner_height, 0) if position == 'bottom-left' else
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
                       (self._marker_width/2.0, self._height-self._line_width) if orientation == 'bottom' else
                       (-self._line_width, self._line_width+self._marker_width/2.0) if orientation == 'left' else
                       (self._inner_width+self._line_width, self._line_width))
        path = ['M{:g},{:g}'.format(self._outer_radius, self._line_width/2.0)]
        marker_id = '{}_marker'.format(self._id_base)
        if orientation in ['top', 'bottom']:
            count = self._horizontal_markers
            step_format = 'l{:g},0'
        else:
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

    def svg(self):
        svg = [self.SVG_DEFS.format(RADIUS=self._marker_radius, TAIL=self._marker_tail,
                                    WIDTH=self._stroke_width, STROKE=self._stroke_colour,
                                    FILL=self._fill_colour, ID_BASE=self._id_base,
                                    OFFSET=-self._line_width/2.0)]
        svg.append('<g id="{}">'.format(self._id))
        svg.extend(self.corner('top-left'))
        svg.extend(self.corner('top-right'))
        svg.extend(self.corner('bottom-left'))
        svg.extend(self.corner('bottom-right'))
        svg.extend(self.side('top'))
        svg.extend(self.side('left'))
        svg.extend(self.side('bottom'))
        svg.extend(self.side('right'))
        svg.append('</g>')
        return '\n'.join(svg)

def wrap_svg(svg):
    return """<?xml version="1.0" standalone="no"?>
<svg  version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
      width="800" height="400"
      viewBox="-10 -10 400 200">
      {SVG:s}
</svg>""".format(SVG=svg)

if __name__ == '__main__':
    membrane = CellMembrane('cell', 300, 100)
    svg = wrap_svg(membrane.svg())
    f = open('../m.svg', 'w')
    f.write(svg)
    f.close()
