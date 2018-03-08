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

import math
import operator
from collections import OrderedDict

#------------------------------------------------------------------------------

from . import diagram as dia
from . import layout
from . import parser
from .element import Element, PositionedElement

#------------------------------------------------------------------------------

FLOW_OFFSET      = 30  # pixels   ### From stylesheet??
POTENTIAL_OFFSET = 30  # pixels

#------------------------------------------------------------------------------

class BondGraph(Element):
    def __init__(self, diagram, **kwds):
        super().__init__(diagram, class_name='BondGraph', **kwds)
        self._flows = []
        self._potentials = OrderedDict()

    @property
    def flows(self):
        return self._flows

    @property
    def potentials(self):
        return self._potentials

    def add_flow(self, flow):
        self._flows.append(flow)

    def add_potential(self, potential):
        self._potentials[potential] = potential.quantity

    def set_offsets(self):
        for flow in self.flows:
            flow.set_transporter_offsets()

    def svg(self):
        svg = [ ]
        for p, q in self.potentials.items():
            (x, y) = p.coords
            (qx, qy) = q.coords
            svg.append('<path fill="none" stroke="#222222" stroke-width="2.0" opacity="0.6"'
                     + ' d="M{start_x:g},{start_y:g} L{end_x:g},{end_y:g}"/>'
                       .format(start_x=x, start_y=y, end_x=qx, end_y=qy))
            svg.extend(p.svg(fill='#c0ffc0'))
        # Link potentials via flows and fluxes
        for flow in self.flows:
            svg.extend(flow.svg(fill='#ff8080'))
            for flux in flow.fluxes:
                svg.extend(flux.svg())
        return svg

#------------------------------------------------------------------------------

class Flow(Element, PositionedElement):
    def __init__(self, diagram, transporter=None, **kwds):
        self._transporter = diagram.find_element('#' + transporter, dia.Transporter) if transporter else None
        super().__init__(diagram, class_name='Flow', **kwds)
        self._fluxes = []
        self._flux_offsets = {}

    @property
    def fluxes(self):
        return self._fluxes

    @property
    def transporter(self):
        return self._transporter

    def add_flux(self, flux):
        self._fluxes.append(flux)
        self._flux_offsets[flux] = layout.Point()

    def flux_offset(self, flux):
        return self._flux_offsets.get(flux, layout.Point())

    def parse_geometry(self):
        PositionedElement.parse_geometry(self, default_offset=self.diagram.flow_offset,
                                               default_dependency=self.transporter)

    def set_transporter_offsets(self):
        if self.transporter is not None and len(self.fluxes) > 1:
            # Get index of coordinate we want to compare against.
            index = (1 if self.transporter.compartment_side in layout.VERTICAL_BOUNDARIES
                     else 0)
            origin = self.transporter.coords[index]
            flux_offset = {}
            num_fluxes = len(self.fluxes)
            for flux in self.fluxes:
                offset = flux.from_potential.coords[index] - origin
                for to in flux.to_potentials:
                    offset += (to.coords[index] - origin)
                flux_offset[flux] = offset/float(1 + len(flux.to_potentials))
            for n, p in enumerate(sorted(flux_offset.items(), key=operator.itemgetter(1))):
                self._flux_offsets[p[0]][index] = (self.diagram.unit_converter.pixels(
                                                      self.transporter.width,
                                                      index,
                                                      add_offset=False)
                                                 *(-0.5 + n/float(num_fluxes - 1)))

    def get_flow_line(self, flux):
        TRANSPORTER_EXTRA = (10, 'x')  ## Get from CSS ???
        points = []
        if self.transporter is not None:
            compartment = self.transporter.container.geometry
            side = self.transporter.compartment_side
            index = 0 if side in layout.VERTICAL_BOUNDARIES else 1
            if compartment.contains(self.geometry):
                sign = -1 if side in ['top', 'left'] else 1
            else:
                sign = 1 if side in ['top', 'left'] else -1
            transporter_end = self.transporter.coords.copy()
            transporter_end[index] += sign*(self.diagram
                                                .unit_converter.pixels(
                                                      TRANSPORTER_EXTRA,
                                                      index,
                                                      add_offset=False))
            offset = self._flux_offsets[flux]
            # Are the from and flow elements on the same side
            # of the transporter's compartment?
            if (compartment.contains(self.geometry)
             == compartment.contains(flux.from_potential.geometry)):
                points.extend([offset+self.coords, offset+transporter_end])
            else:
                points.extend([offset+transporter_end, offset+self.coords])
        else:
            points.append(self.coords)
        return points

#------------------------------------------------------------------------------

class Flux(Element, PositionedElement):
    def __init__(self, diagram, flow, from_=None, to=None, count=1, line=None, **kwds):
        super().__init__(diagram, class_name='Flux', **kwds)
        self._from_potential = diagram.find_element('#' + from_, Potential)
        self._to_potentials = [diagram.find_element('#' + name, Potential) for name in to.split()]
        self._count = int(count)
        self._curve_tokens = dict(start=parser.StyleTokens.create(self._style, 'curve-start'),
                                  end=parser.StyleTokens.create(self._style, 'curve-end'))
        self._curve_segments = dict(start=[], end=[])
        self._flow = flow

    @property
    def from_potential(self):
        return self._from_potential

    @property
    def to_potentials(self):
        return self._to_potentials

    @property
    def count(self):
        return self._count

    def parse_geometry(self):
        for pos, tokens in self._curve_tokens.items():
            self._curve_segments[pos] = self._parse_curve_segments(tokens)

    def _parse_curve_segments(self, tokens):
        """
        <line-point> ::= <coord-pair> | <line-angle> <constraint>
        <coord-pair> ::= '(' <length> ',' <length> ')'
        <constraint> ::= ('until-x' | 'until-y') <relative-point>
        <relative-point> ::= <id-list> | [ <offset> <reln> ] <id-list>

        """
        # "210 until-x #u16 #v5, -90 until-y #NCE"
        segments = []
        while tokens is not None:
            angle, tokens = parser.get_number(tokens)
            # Normalise angle...
            token = tokens.next()
            if (token.type != 'ident'
             or token.lower_value not in ['until-x', 'until-y']):
                raise SyntaxError("Unknown constraint for curve segment.")
            constraint = 0 if token.lower_value == 'until-x' else 1
            # Check that angle != +/-90 if until-x
            # Check that angle != 0/180 if until-y
            token = tokens.peek()
            if token.type == '() block':
                offset, _ = parser.get_coordinates(parser.StyleTokens(token.content), allow_local=False)
                token = tokens.next()
                if token.type != 'ident' or token.lower_value != 'from':
                    raise SyntaxError("'from' expected.")
                token = tokens.next()
            elif token.type in ['number', 'dimension']:
                length, tokens = parser.get_length(tokens)
                token = tokens.next()
                if (token.type != 'ident'
                 or token.lower_value not in layout.POSITION_RELATIONS):
                    raise SyntaxError("Unknown relationship for offset.")
                reln = token.lower_value
                if reln in layout.HORIZONTAL_RELATIONS:
                    offset = ((length[0] if reln == 'right' else -length[0], length[1]), (0, ''))
                else:   # VERTICAL_RELATIONS
                    offset = ((0, ''), (length[0] if reln == 'right' else -length[0], length[1]))
                token = tokens.next()
            else:
                offset = ((0, ''), (0, ''))
            dependencies = []
            while token.type == 'hash':
                try:
                    dependency = self.diagram.find_element('#' + token.value)
                    if dependency is None:
                        raise KeyError("Unknown element '#{}".format(token.value))
                    dependencies.append(dependency)
                    token = tokens.next()
                except StopIteration:
                    break
            if not dependencies:
                raise SyntaxError("Identifier(s) expected.")

            if token.type == 'ident' and token.lower_value == 'offset':
                token = tokens.next()
                if token.type == '() block':
                    line_offset, _ = parser.get_coordinates(parser.StyleTokens(token.content), allow_local=False)
                    token = tokens.peek()
                else:
                    raise SyntaxError("Offset expected.")
            else:
                line_offset = None

            segments.append((angle, constraint, offset, dependencies, line_offset))
            if token == ',':
                continue
            elif tokens.peek() is None:
                break
            else:
                raise SyntaxError("Invalid syntax")
        return segments

    def _get_curve_segments(self, start_pos, segments, reverse=False):
        last_pos = start_pos
        points = [start_pos]
        for segment in segments:
            angle = segment[0]
            offset = self.diagram.unit_converter.pixel_pair(segment[2], add_offset=False)
            end_pos = offset + layout.Position.centroid(segment[3])  # Centre of dependencies
            if segment[1] == 0:   #  until-x
                dx = end_pos[0] - last_pos[0]
                dy = dx*math.tan(angle*math.pi/180)
                end_pos[1] = last_pos[1] - dy
            else: ##  segment[1] == y:   #  until-y
                dy = last_pos[1] - end_pos[1]
                dx = dy*math.tan((90-angle)*math.pi/180)
                end_pos[0] = last_pos[0] + dx
            if segment[4] is not None:
                line_offset = self.diagram.unit_converter.pixel_pair(segment[4], add_offset=False)
                points[-1] += line_offset
                end_pos += line_offset
            points.append(end_pos)
            last_pos = end_pos
        if self._flow.transporter is not None:
            trans_coords = self._flow.transporter.coords
            if (trans_coords[0] == points[-1][0]
             or trans_coords[1] == points[-1][1]):
                points[-1] += self._flow.flux_offset(self)
        return points if not reverse else list(reversed(points))

    def svg(self):
        svg = []
        flux_points = self._get_curve_segments(self.from_potential.coords, self._curve_segments['start'])
        flux_points.extend(self._flow.get_flow_line(self))
        for to in self.to_potentials:
            # Can have multiple `to` potentials
            points = list(flux_points)
            points.extend(self._get_curve_segments(to.coords, self._curve_segments['end'], reverse=True))
            svg.append('<path fill="none" stroke="#222222" stroke-width="{:g}" opacity="0.6"'
                .format(self.count*2.5)
              + ' d="M{:g},{:g} {:s}"/>'
                .format(points[0][0], points[0][1],
                       ' '.join(['L{:g},{:g}'.format(*point) for point in points[1:]])))
        # repeated flux.count times
        return svg

#------------------------------------------------------------------------------

class Potential(Element, PositionedElement):
    def __init__(self, diagram, quantity=None, **kwds):
        self._quantity = diagram.find_element('#' + quantity, dia.Quantity)
        self._quantity.set_potential(self)
        super().__init__(self._quantity.container, class_name='Potential', **kwds)

    @property
    def quantity_id(self):
        return self._quantity.id

    @property
    def quantity(self):
        return self._quantity

    def parse_geometry(self):
        PositionedElement.parse_geometry(self, default_offset=self.diagram.quantity_offset,
                                               default_dependency=self.quantity)

#------------------------------------------------------------------------------
