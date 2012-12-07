import json

def graph2json(g, outfile):
    out = {}
    all_nodes = list(g.get_all_nodes())
    out['nodes'] = [{'nedges': len(g.all_node_edges(X)),
                     'pt': X.pt} for X in all_nodes]
    out['edges'] = [{'a': all_nodes.index(E.a),
                     'b': all_nodes.index(E.b)} for E in g.edges]
    json.dump(out, open(outfile, 'w'))

if __name__=='__main__':
    from graph import load_graph
    g1 = load_graph()
    graph2json(g1, 'graph.json')
    g2 = load_graph(bidirectional=True)
    graph2json(g2, 'graph_bi.json')
