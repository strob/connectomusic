def inhibit():
    p._state_nodes = []
    p._state_edges = []
    for n in p.graph.get_all_nodes():
        n.release_sound()
button("inhibit", inhibit)
