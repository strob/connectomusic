import numpy as np
import os
import numm
import svgToGraph
import glob
import pickle

class Graph:
    def __init__(self, edges):
        self.edges = edges
        self._compute_nodemap()
        self.version = ""

    def _compute_nodemap(self):
        self.nodes = {}         # {node -> [edges]}
        self.tonodes = {}       # {node -> [edges]} (edges that point to this node)
        for e in self.edges:
            # undirected
            # for N in [e.a, e.b]:
            #     if N in self.nodes:
            #         self.nodes[N].append(e)
            #     else:
            #         self.nodes[N] = [e]

            # directed
            self.nodes.setdefault(e.a, []).append(e)
            self.tonodes.setdefault(e.b, []).append(e)

        self.grpnodes = {}      # {grp -> [nodes]}
        for n in self.get_all_nodes():
            if hasattr(n, 'group'):
                self.grpnodes.setdefault(n.group, []).append(n)

    def node_edges(self, node):
        return self.nodes.get(node, [])

    def all_node_edges(self, node):
        # ... in both directions
        return self.nodes.get(node,[]) + self.tonodes.get(node,[])
        # return filter(lambda x: x.a == node or x.b == node, self.edges)

    def get_nodes(self):
        return self.nodes.keys()

    def get_all_nodes(self):
        #not only those with outbound edges
        return set([X.a for X in self.edges] + [X.b for X in self.edges])

    def get_edges(self):
        return self.edges

    def _remove_edge_effects(self, edge):
        # Remove all mentions from nodemap
        for node,edges in self.nodes.items():
            self.nodes[node] = filter(lambda x: x != edge, edges)

    def remove_edge(self, edge, biremoval=False):
        try:
            self.edges.remove(edge)
        except:
            pass
        self._remove_edge_effects(edge)
        if biremoval:
            for e in self.edges:
                if e.a == edge.b and e.b == edge.a:
                    self.edges.remove(e)
                    self._remove_edge_effects(e)
                    break

    def node_outbound_cost(self, node):
        return len(self.node_edges(node))
        #return sum([E.cost for E in self.node_edges(node)])

    def nearest(self, x, y):
        nodes = list(self.get_all_nodes())
        terrain = np.array([X.pt for X in nodes])
        dist = np.hypot(*(terrain - np.array([x,y])).T)
        return nodes[dist.argmin()]

    def sub(self, oldnode, newnode, recompute_nodemap=True):
        # Replace in all edges
        #edges = self.all_node_edges(oldnode)
        for e in self.nodes.get(oldnode,[]):
            e.a = newnode
        for e in self.tonodes.get(oldnode,[]):
            e.b = newnode

        if recompute_nodemap:
            # can opt out if doing a bunch of subs
            self._compute_nodemap()

class Edge:
    def __init__(self, a, b, cost=1):
        self.a = a
        self.b = b

        self.cost = cost

    @property
    def length(self):
        return np.hypot(self.a.pt[0]-self.b.pt[0],
                        self.a.pt[1]-self.b.pt[1])

    def flip(self):
        c = self.a
        self.a = self.b
        self.b = c

class Node:
    def __init__(self, pt, payload=None, group=None, nedges=0):
        self.pt = pt
        self.nedges = nedges
        self.set_payload(payload, group)

    def set_payload(self, payload, group):
        self.payload = payload
        self.group = group
        self.isloop = payload is not None and 'loop' in payload

        if self.payload is None:
            self.frames = None
        else:
            #self.frames = numm.sound2np(payload)
            self.frames = np.load(payload)

class AmplifierNode(Node):
    pass

def load_graph(left=False, bidirectional=False):
    print '>svgToGraph'
    if left:
        edges = svgToGraph.Graph('node_map.svg').getLeftEdges()
    else:
        edges = svgToGraph.Graph('node_map.svg').getEdges()

    print '>nodes'
    id_to_node = {}
    def _intpt(pt):
        return (int(pt[0]), int(pt[1]))

    def _node(X):
        if X._id not in id_to_node:
            id_to_node[X._id] = Node(_intpt(X.get_center()))
        return id_to_node[X._id]

    edges = [Edge(_node(X[0]), _node(X[1]))#,
                  #cost=np.hypot(*(np.array(X[0].get_center())-X[1].get_center())))
             for X in edges]

    # make all edges (bi-)directional
    if bidirectional:
        edges += [Edge(_node(X[0]), _node(X[1]),
                       cost=np.hypot(*(np.array(X[0].get_center())-X[1].get_center())))
                  for X in edges]

    print '>graph'
    return Graph(edges)

def _get_group(x):
    return int(os.path.basename(x).split('_')[0])


def in_the_void(graph):
    "Do something with those poor nodes lacking payload"
    nodes = graph.get_nodes()
    print '>sub'
    for node in nodes:
        if node.payload is None:
            graph.sub(node, AmplifierNode(node.pt), recompute_nodemap=False)
    print '>nodemap'
    graph._compute_nodemap()

def connect_to_samples(graph, files):
    print '>sorting'
    # Sort files based on numerical basename before first `_.'
    files.sort(key=_get_group)

    # Sort nodes by total outbound cost
    nodes = graph.get_nodes()
    nodes.sort(key=graph.node_outbound_cost)

    assert len(nodes) >= len(files), "More sounds than nodes!"

    print '>loading'
    for idx,f in enumerate(files):
        node = nodes[int((idx / float(len(files))) * len(nodes))]
        node.set_payload(f, _get_group(f))

    print '>amplifier nodes'
    in_the_void(graph)
    print '>done'

def make_directed_graph():
    g = load_graph()

    print '>nedges'
    nodes = g.get_all_nodes()

    # precompute nedges
    for n in nodes:
        n.nedges = len(g.all_node_edges(n))

    print '>reverse'
    # reverse backwards edges; edges flow `down' from more to fewer
    for e in g.edges:
        if e.a.nedges < e.b.nedges:
            e.flip()

    g._compute_nodemap()

    return g

def connected_directed_graph(version=None):
    g = make_directed_graph()

    VERSIONS = ['final_material_tt_bearbeit', 
                'final_material_tt_bearbeit_NEU_gekurzt',
                'final_material_tt_bearbeit_2nd_order_NEUER',
                '*']
    if version is None:
        version = VERSIONS[0]

    # files = glob.glob('snd/*/*.npy')
    # files = glob.glob('snd/final_material_tt_bearbeit_2nd_order_NEUER/*.npy')
    files = glob.glob('snd/%s/*.npy' % (version))

    g.version = version

    print '>split'

    # split by nedges
    split = {}
    for f in files:
        grp = _get_group(f)
        if not split.has_key(grp):
            split[grp] = []
        if 'loop' in f:
            split[grp].insert(0, f)
        else:
            split[grp].append(f)

    print '>assign'

    # assign sounds & amplifiers
    for n in g.get_all_nodes():
        grp = n.nedges
        if len(split.get(grp,[])) > 0:
            n.set_payload(split[grp].pop(), grp)
        else:
            # swap n with an amp
            g.sub(n, AmplifierNode(n.pt, nedges=n.nedges), recompute_nodemap=False)

    # un-used sounds?
    print 'unused sounds', split

    g._compute_nodemap()

    return g
