def saturate():
    p._selection = list(g.get_all_nodes())[:p._target]
button("saturate", saturate)