import logging

import igraph

#------------------------------------------------------------------------------

from cell_diagram.parser import Parser, StyleSheet

#------------------------------------------------------------------------------

def parse(file, stylesheet=None):
    parser = Parser()
    return parser.parse(file, stylesheet)

#------------------------------------------------------------------------------

def bond_graph(diagram):
    g = igraph.Graph(directed=True)
    potentials = list(diagram.potentials.keys())
    g.add_vertices(potentials)
    g.vs['label'] = potentials
    for flow in diagram.flows:
        g.add_vertex(flow.id, label=flow.id, color='blue')
        for flux in flow.fluxes:
            for n in range(flux.count):
                g.add_edge(flux.from_potential, flow.id)
                g.add_edge(flow.id, flux.to_potential)
    return g

#------------------------------------------------------------------------------

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)

    stylesheet = StyleSheet('''
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
      ''')



    diagram = parse('bond_graph.xml')

    ## parse('cell_diagram.xml', stylesheet)

    g = bond_graph(diagram)
    layout = g.layout("kk")
    igraph.plot(g, layout=layout)

#------------------------------------------------------------------------------
