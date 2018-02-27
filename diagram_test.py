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

import logging

# -----------------------------------------------------------------------------

from cell_diagram.parser import Parser

# -----------------------------------------------------------------------------


def parse(file, stylesheet=None):
    parser = Parser()
    return parser.parse(file, stylesheet)

# -----------------------------------------------------------------------------


if __name__ == '__main__':
    # logging.getLogger().setLevel(logging.DEBUG)

    stylesheet = '''
        #q21 {
          colour : pink ;
        }
        .cell {
          shape: (12, 8);
          colour: blue;
          /* closed-cylinder, rectangle, circle/ellipse */
          /* thickness, size, aspect-ratio, ... */
        }
        .sodium {
          colour: yellow;
          /* symbol, ... */
        }
        .potassium {
          colour: green;
        }
        .channel {
          position: bottom;
        }
        #i_Leak {
          position: right;
        }
      '''

    #    diagram, graph = parse('cell_diagram.xml', stylesheet)
    # #  diagram = parse('bond_graph.xml')

    diagram, graph = parse('cell_diagram.xml') # atp.xml')

    t = open('t.svg', 'w')
    t.write(diagram.svg(graph))
    t.close()

#    g.vs['x'] = [0,  2,   2,     0,    2,   2,   1]
#    g.vs['y'] = [0, -0.4, 0.4,  -0.3, -0.7, 0.7, 0]
#    g.vs['size'] = 40
#    layout = g.layout("auto")
#    print(g)
#    for l in layout:
#        print(l)
# #    igraph.plot(g, layout=layout, keep_aspect_ratio=True,
# #                margin=50) ##, target='atp.svg')
# #  bbox=(500, 400),
# -----------------------------------------------------------------------------
