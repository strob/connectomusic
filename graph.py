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
        self.samplemap = {}

        self._burnededges = []

    def cache_sounds(self):
        self._soundcache = {}
        for s in self.samplemap.values():
            for sound in s:
                self._soundcache[sound] = np.load(sound)

        for sound in self._soundcache.keys():
            if 'loop' in sound:
                print 'new sounds have loop'
                return
        print 'new sounds have no loops'

    def get_sample(self, nedges):
        "returns (payload, frames, isloop)"

        if nedges not in self.samplemap:
            print 'warning: %d not in samplemap' % (nedges)
            nedges = max(self.samplemap.keys())
            print 'using %d instead' % (nedges)

        samplelist = self.samplemap[nedges]
        if len(samplelist) == 0:
            return None

        sample = samplelist[0]

        # cycle samplemap
        self.samplemap[nedges] = samplelist[1:] + [sample]

        isloop = 'loop' in sample

        # frames = np.load(sample)
        frames = self._soundcache[sample]

        return (sample, frames, isloop)

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
            if hasattr(n, 'nedges'):
                self.grpnodes.setdefault(n.nedges, []).append(n)

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

        # Look for Nodes that link to either end, and cleanse their cache.
        self.nodes[edge.a] = filter(lambda x: x != edge, self.nodes[edge.a])
        self.tonodes[edge.b] = filter(lambda x: x != edge, self.tonodes[edge.b])

    def remove_edge(self, edge):
        try:
            self.edges.remove(edge)
            self._burnededges.append(edge)
        except:
            print 'failed to remove the original edge?', edge

        for e in self.tonodes.get(edge.a,[]):
            if e.a == edge.b:
                self._burnededges.append(e)
                self.edges.remove(e)
                self._remove_edge_effects(e)
                self._remove_edge_effects(edge)
                return e
        print 'warning: no bidirectional to remove'
        self._remove_edge_effects(edge)


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
    def __init__(self, pt, graph=None, nedges=0):
        self.pt = pt
        self.nedges = nedges
        self.graph = graph
        self._burned = False

        self.release_sound()

    def burn(self):
        self._burned = True
        self.release_sound()

    def release_sound(self):
        # relinquish current assignment
        self._payload = None
        self._frames = None
        self._isloop = None

    def request_sound(self):
        # get new sound from graph
        if self._burned:
            print 'warning: burned! ignoring request'
            return
        # print 'request new sound, degree %d' % (self.nedges)
        gotsample = self.graph.get_sample(self.nedges)
        if gotsample is None:
            print 'warning: all done with sample'
            return
        self._payload, self._frames, self._isloop = gotsample
        # print 'got %s' % (self._payload)

    @property
    def payload(self):
        if self._payload is None:
            self.request_sound()
        return self._payload

    @property
    def frames(self):
        if self._frames is None:
            self.request_sound()
        return self._frames

    @property
    def isloop(self):
        if self._isloop is None:
            self.request_sound()
        return self._isloop

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

    e2 = [Edge(_node(X[0]), _node(X[1]))#,
                  #cost=np.hypot(*(np.array(X[0].get_center())-X[1].get_center())))
             for X in edges]

    # make all edges (bi-)directional
    if bidirectional:
        e2 += [Edge(_node(X[1]), _node(X[0]))
                       # cost=np.hypot(*(np.array(X[0].get_center())-X[1].get_center())))
                  for X in edges]
    edges = e2

    print '>graph'
    return  Graph(edges)

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

def make_directed_graph(bd=False):
    g = load_graph(bidirectional=bd)

    print '>nedges'
    nodes = g.get_all_nodes()

    # precompute nedges & link to graph 
    for n in nodes:
        n.graph = g
        if bd:
            n.nedges = len(g.node_edges(n))
        else:
            n.nedges = len(g.all_node_edges(n))

    print '>reverse'
    # reverse backwards edges; edges flow `down' from more to fewer
    if not bd:
        for e in g.edges:
            if e.a.nedges < e.b.nedges:
                e.flip()

    g._compute_nodemap()

    return g

def connected_directed_graph(version=None, bd=False, files=None):
    g = make_directed_graph(bd=bd)

    VERSIONS = ['final_material_tt_bearbeit_(314)',
                'final_material_tt_bearbeit_NEU_gekurzt_(170)',
                'final_material_tt_bearbeit_2nd_order_NEUER_(459)',
                '*']
    if version is None:
        version = VERSIONS[-1]

    if files is None:
        files = glob.glob('snd/%s/*.npy' % (version))

    g.version = version

    print '>split'

    # split by nedges
    split = {}
    for f in sorted(files):
        grp = _get_group(f)
        if not split.has_key(grp):
            split[grp] = []
        # if 'loop' in f:
        #     split[grp].insert(0, f)
        else:
            split[grp].append(f)

    g.samplemap = split
    g.cache_sounds()

    return g
