import logging

import matplotlib.pyplot as plt
import networkx as nx

#------------------------------------------------------------------------------

from cell_diagram.parser import Parser

#------------------------------------------------------------------------------

def parse(file, stylesheet=None):
    parser = Parser()
    return parser.parse(file, stylesheet)

#------------------------------------------------------------------------------

def bond_graph(graph):
    g = nx.Graph()
    # Link potentials to corresponding quantities
    for p, q in graph.potentials.items():
        g.add_node(p.id, label=p.id) # x, y from p.style
        g.add_node(q.id, label=q.id) # relative position wrt potential?
        g.add_edge(p.id, q.id)
    # Link potentials via flows and fluxes
    for flow in graph.flows:
        g.add_node(flow.id, label=flow.id, color='blue')
        for flux in flow.fluxes:
            g.add_edge(flux.from_potential, flow.id)
            to_potentials = flux.to_potential.split()
            weighting = 1.0/float(len(to_potentials))
            for p in to_potentials: g.add_edge(flow.id, p, weight=weighting)


    layout = nx.spring_layout(g, k=0.1,
                                 pos={'u24': (0, 0.5), 'u25': (1, 0.8), 'u26': (1, 0.2),
                                      'q24': (0, 0.7), 'q25': (1, 1),   'q26': (1, 0), 'v35': (0.5, 0.5)},
                                 fixed=['u24', 'u25', 'u26'],
                                 fixed_coords={'q24': (True, False), 'u25': (True, False), 'u26': (True, False),
                                               'q25': (True, False), 'q26': (True, False), 'v35': (False, True)})
    nx.draw(g, layout)
    plt.show()


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)

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
##  diagram = parse('bond_graph.xml')

    diagram, graph, geometry = parse('cell_diagram.xml') # atp.xml')

    print(geometry.svg())
#    bond_graph(graph, layout)

#    g.vs['x'] = [0,  2,   2,     0,    2,   2,   1]
#    g.vs['y'] = [0, -0.4, 0.4,  -0.3, -0.7, 0.7, 0]
#    g.vs['size'] = 40
#    layout = g.layout("auto")
#    print(g)
#    for l in layout:
#        print(l)
##    igraph.plot(g, layout=layout, keep_aspect_ratio=True, margin=50) ##, target='atp.svg')
##  bbox=(500, 400),
#------------------------------------------------------------------------------
