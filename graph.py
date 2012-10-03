import numpy as np
import os
import numm
import svgToGraph

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

    def all_node_edges(self, node):
        # ... in both directions
        return filter(lambda x: x.a == node or x.b == node, self.edges)

    def get_nodes(self):
        return self.nodes.keys()

    def get_edges(self):
        return self.edges

    def node_outbound_cost(self, node):
        return len(self.node_edges(node))
        #return sum([E.cost for E in self.node_edges(node)])

    def nearest(self, x, y):
        nodes = self.get_nodes()
        terrain = np.array([X.pt for X in nodes])
        dist = np.hypot(*(terrain - np.array([x,y])).T)
        return nodes[dist.argmin()]

    def sub(self, oldnode, newnode, recompute_nodemap=True):
        # Replace in all edges
        edges = self.all_node_edges(oldnode)
        for e in edges:
            if e.a == oldnode:
                e.a = newnode
            else:
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

class AmplifierNode(Node):
    def __init__(self, pt):
        self.pt = pt

def load_graph():
    edges = svgToGraph.Graph('node_map.svg').getEdges()

    id_to_node = {}
    def _intpt(pt):
        return (int(pt[0]), int(pt[1]))

    def _node(X):
        if X._id not in id_to_node:
            id_to_node[X._id] = Node(_intpt(X.get_center()))
        return id_to_node[X._id]

    edges = [Edge(_node(X[0]), _node(X[1]),
                        cost=np.hypot(*(np.array(X[0].get_center())-X[1].get_center())))
             for X in edges]

    return Graph(edges)


def _get_group(x):
    return int(os.path.basename(x).split('_')[0])


def in_the_void(graph):
    "Do something with those poor nodes lacking payload"
    nodes = graph.get_nodes()
    for node in nodes:
        if node.payload is None:
            graph.sub(node, AmplifierNode(node.pt), recompute_nodemap=False)
    graph._compute_nodemap()

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

    in_the_void(graph)
