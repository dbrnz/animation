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
    g.vs['color'] = 'green'
    g.vs['label'] = potentials
    for p in potentials:
        q = p.replace('u', 'q')
        g.add_vertex(q, label=q)
        g.add_edge(p, q)
    for flow in diagram.flows:
        g.add_vertex(flow.id, label=flow.id, color='blue')
        for flux in flow.fluxes:
            for n in range(flux.count):
                g.add_edge(flux.from_potential, flow.id)
                for p in flux.to_potential.split(): g.add_edge(flow.id, p)
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

##  parse('cell_diagram.xml', stylesheet)
##  diagram = parse('bond_graph.xml')

    diagram = parse('atp.xml')

    g = bond_graph(diagram)
    g.vs['x'] = [0,  2,   2,     0,    2,   2,   1]
    g.vs['y'] = [0, -0.2, 0.2,  -0.1, -0.3, 0.3, 0]
    layout = g.layout("auto")
    print(g)
    for l in layout:
        print(l)
    igraph.plot(g, layout=layout) ##, bbox=(200, 100)) ## , target='atp.svg')

#------------------------------------------------------------------------------
