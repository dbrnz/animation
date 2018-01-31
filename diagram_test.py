import logging

import igraph

#------------------------------------------------------------------------------

from cell_diagram.parser import Parser

#------------------------------------------------------------------------------

def parse(file, stylesheet=None):
    parser = Parser()
    return parser.parse(file, stylesheet)

#------------------------------------------------------------------------------

def bond_graph(graph):
    g = igraph.Graph(directed=True)
    potentials = [p.id for p in graph.potentials.keys()]
    print(potentials)
    g.add_vertices(potentials)
    g.vs['color'] = 'green'
    g.vs['label'] = potentials
    # Link potentials to corresponding quantities
    for p, q in graph.potentials.items():
        g.add_vertex(q.id, label=q.id)
        g.add_edge(p.id, q.id)
    # Link potentials via flows and fluxes
    for flow in graph.flows:
        g.add_vertex(flow.id, label=flow.id, color='blue')
        for flux in flow.fluxes:
            for n in range(flux.count):
                g.add_edge(flux.from_potential, flow.id)
                for p in flux.to_potential.split(): g.add_edge(flow.id, p)
    return g

#------------------------------------------------------------------------------

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

    diagram, graph = parse('atp.xml')

    g = bond_graph(graph)
    g.vs['x'] = [0,  2,   2,     0,    2,   2,   1]
    g.vs['y'] = [0, -0.4, 0.4,  -0.3, -0.7, 0.7, 0]
    g.vs['size'] = 40
    layout = g.layout("auto")
#    print(g)
#    for l in layout:
#        print(l)
    igraph.plot(g, layout=layout, keep_aspect_ratio=True, margin=50) ##, target='atp.svg')
##  bbox=(500, 400),
#------------------------------------------------------------------------------
