import numpy as np
import os
import numm

class Graph:
    def __init__(self, edges):
        self.edges = edges
        self._compute_nodemap()

    def _compute_nodemap(self):
        self.nodes = {}         # {node -> [edges]}
        for e in self.edges:
            # undirected
            # for N in [e.a, e.b]:
            #     if N in self.nodes:
            #         self.nodes[N].append(e)
            #     else:
            #         self.nodes[N] = [e]

            # directed
            if e.a in self.nodes:
                self.nodes[e.a].append(e)
            else:
                self.nodes[e.a] = [e]

    def node_edges(self, node):
        return self.nodes.get(node, [])

    def get_nodes(self):
        return self.nodes.keys()

    def get_edges(self):
        return self.edges

    def node_outbound_cost(self, node):
        return sum([E.cost for E in self.node_edges(node)])

    def nearest(self, x, y):
        nodes = self.get_nodes()
        terrain = np.array([X.pt for X in nodes])
        dist = np.hypot(*(terrain - np.array([x,y])).T)
        return nodes[dist.argmin()]

class Edge:
    def __init__(self, a, b, cost=1):
        self.a = a
        self.b = b

        self.cost = cost

    @property
    def length(self):
        return np.hypot(self.a.pt[0]-self.b.pt[0],
                        self.a.pt[1]-self.b.pt[1])

class Node:
    def __init__(self, pt, payload=None, group=None):
        self.pt = pt
        self.set_payload(payload, group)

    def set_payload(self, payload, group):
        self.payload = payload
        self.group = group

        if self.payload is None:
            self.frames = None
        else:
            self.frames = numm.sound2np(payload)

def load_graph(pkl, directed=True):
    import pickle
    edges = pickle.load(open(pkl))

    ptToNode = {}

    edgeObjs = []

    for a,b in edges:
        for N in [a,b]:
            if N not in ptToNode:
                ptToNode[N] = Node(N)

        if directed and len(filter(lambda x: x.b==ptToNode[a] and x.a==ptToNode[b], edgeObjs)) > 0:
            print 'skipping the other direction'
            continue
        cost = np.hypot(a[0]-b[0], a[1]-b[1])
        edgeObjs.append(Edge(ptToNode[a], ptToNode[b], cost))

    return Graph(edgeObjs)

def _get_group(x):
    return int(os.path.basename(x).split('_')[0])

def connect_to_samples(graph, files):
    # Sort files based on numerical basename before first `_.'
    files.sort(key=_get_group)

    # Sort nodes by total outbound cost
    nodes = graph.get_nodes()
    nodes.sort(key=graph.node_outbound_cost)

    assert len(nodes) >= len(files), "More sounds than nodes!"

    for idx,f in enumerate(files):
        node = nodes[int((idx / float(len(files))) * len(nodes))]
        node.set_payload(f, _get_group(f))
