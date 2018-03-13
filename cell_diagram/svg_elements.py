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
            <use transform="translate({OFFSET}, {SPACING})" xlink:href="#{ID_BASE}_base_element"/>
            <use transform="rotate(180) translate({OFFSET}, 0)" xlink:href="#{ID_BASE}_base_element"/>
        </g>
        <!-- Marker for straight segments -->
        <marker id="{ID_BASE}_marker" markerUnits="userSpaceOnUse" style="overflow: visible" orient="auto">
            <use stroke="{STROKE}" fill="{FILL}" xlink:href="#{ID_BASE}_element" transform="rotate(90)"/>
        </marker>
      </defs>"""

    def __init__(self, id, width, height, id_base='cell_membrane',
                 outer_markers=9, inner_markers=3, marker_radius=2.4, marker_tail=17,
                 stroke_width=1, stroke_colour='#0092DF', fill_colour='#BFDDFF'):
        """
        :param outer_markers: Number of outer markers in a corner.
        :param immer_markers: Number of inner markers in a corner.
        """
        self._id = id
        self._id_base = id_base
        self._outer_markers = outer_markers
        self._inner_markers = inner_markers
        self._marker_radius = marker_radius
        self._marker_tail = marker_tail
        self._stroke_width = stroke_width
        self._stroke_colour = stroke_colour
        self._fill_colour = fill_colour
        # Computed parameters
        self._marker_width = 2.0*self._marker_radius + self._stroke_width
        self._outer_marker_angle = 90/self._outer_markers
        self._outer_radius = self._marker_width/(2*asin(pi/(4*self._outer_markers)))
        self._inner_marker_angle = 90/self._inner_markers
        self._inner_radius = self._marker_width/(2*asin(pi/(4*self._inner_markers)))
        # The thickness of straight lines
        self._line_width = self._outer_radius - self._inner_radius
        # We round the width and height to ensure an integral number of line markers will fit on a side
        self._horizontal_markers = int(0.5 + (width - self._line_width/2.0 - self._inner_radius)/self._marker_width)
        self._vertical_markers = int(0.5 + (height - self._line_width/2.0 - self._inner_radius)/self._marker_width)
        # The size of the straight line portion
        self._inner_width = self._marker_width*self._horizontal_markers
        self._inner_height = self._marker_width*self._vertical_markers
        # The size of the bounding box
        self._outer_width = self._inner_width + 2*self._outer_radius
        self._outer_height = self._inner_height + 2*self._outer_radius

    @property
    def width(self):
        return self._outer_width - self._line_width

    @property
    def height(self):
        return self._outer_height - self._line_width

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
        svg = [self.SVG_DEFS.format(RADIUS=self._marker_radius, TAIL=self._marker_tail,
                                    WIDTH=self._stroke_width, STROKE=self._stroke_colour,
                                    FILL=self._fill_colour, ID_BASE=self._id_base,
                                    OFFSET=-self._line_width/2.0, SPACING=-self._marker_width/2.0)]
        svg.append('<g id="{}" transform="translate({:g},{:g})">'.format(self._id, -self._line_width/2.0, -self._line_width/2.0))
        svg.extend(self.corner('top-left'))
        svg.extend(self.corner('top-right'))
        svg.extend(self.corner('bottom-left'))
        svg.extend(self.corner('bottom-right'))
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

def wrap_svg(svg):
    return """<?xml version="1.0" standalone="no"?>
<svg  version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
      width="800" height="400"
      viewBox="-10 -10 400 300">
      {SVG:s}
</svg>""".format(SVG=svg)

if __name__ == '__main__':
    membrane = CellMembrane('cell', 300, 200)
      #, outer_markers=12, inner_markers=8, marker_tail=10, stroke_width=0.5)
      #, marker_radius=5, marker_tail=35)
    svg = wrap_svg(membrane.svg())
    f = open('../m.svg', 'w')
    f.write(svg)
    f.close()
