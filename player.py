import graph

import numpy as np
import cv2

R = 44100.0
MAX_VOL = 1.5

class EdgeState:
    def __init__(self, edge, decay=1.0):
        self.edge = edge
        self.decay = decay
        self.percentage = 0.0

    def iterate(self, t, speed, decay):
        "Returns True if we've reached B, False otherwise"
        npixels = t * speed
        dpercentage = npixels / self.edge.length

        self.percentage += dpercentage

        self.decay *= decay ** npixels

        if self.percentage > 1.0:
            return True

        return False

    def get_position(self):
        return tuple([int(self.edge.a.pt[X] + self.percentage * (self.edge.b.pt[X]-self.edge.a.pt[X]))
                      for X in [0, 1]])

class NodeState:
    def __init__(self, node, vol=1.0):
        self.node = node
        self.vol = vol
        self.frame = 0

    def iterate(self, buf):
        "Mixes into buffer; returns True if finished with sound, False otherwise"

        if isinstance(self.node, graph.AmplifierNode):
            return True

        if self.node.frames is None:
            #import pdb; pdb.set_trace()
            #print 'fail!'
            return True

        nframes = min(len(self.node.frames) - self.frame, len(buf))

        #pan = self.node.pt[0]  / 400.0
        pan = self.node.pt[0]  / 1250.0
        snd = (self.vol * self.node.frames[self.frame:self.frame+nframes])

        buf[:nframes,1] += snd * pan
        buf[:nframes,0] += snd * (1-pan)

        self.frame += nframes

        if self.frame == len(self.node.frames):
            return True

        return False

DECAY_CUTOFF = 0.05

class Player:
    def __init__(self, graph, speed=50, decay=0.95, target_nnodes=10):
        self.graph = graph

        self._state_edges = []  # [EdgeState]
        self._state_nodes = []  # [NodeState]

        self._speed = speed     # px/sec
        self._decay = decay     # %/px

        self._target = target_nnodes

    def next(self, buffer_size=2048):
        "Increment time unit and return sound buffer (as np-array)"

        # print '%d active edges' % (len(self._state_edges))
        t = buffer_size / R
        for edgestate in self._state_edges:
            # print '    %d%% (%.2f)' % (edgestate.percentage * 100, edgestate.decay)
            if edgestate.iterate(t, self._speed, self._decay):
                self._state_edges.pop(self._state_edges.index(edgestate))
                self.trigger(edgestate.edge.b, vol=edgestate.decay)

        out = np.zeros((buffer_size, 2), dtype=np.int)
        # print '%d active nodes' % (len(self._state_nodes))
        for nodestate in self._state_nodes:
            # print '    %.2f (%d)' % (nodestate.vol, nodestate.frame)
            if nodestate.iterate(out):
                self._state_nodes.pop(self._state_nodes.index(nodestate))
                if nodestate.vol >= DECAY_CUTOFF:
                    for target_edge in self.graph.node_edges(nodestate.node):
                        active_edges = filter(lambda x: x.edge == target_edge, self._state_edges)
                        if len(active_edges) > 0:
                            active_edges[0].decay = min(MAX_VOL, active_edges[0].decay + nodestate.vol)
                        else:
                            self._state_edges.append(EdgeState(target_edge, nodestate.vol))

        return out

    def active(self):
        return len(self._state_edges) > 0 or len(self._state_nodes) > 0

    def trigger(self, node, vol=1.0):
        """Schedule playback & cascade of node at next time unit."""

        # If node is already active, amplify
        playing_node = filter(lambda x: x.node == node, self._state_nodes)
        if len(playing_node) > 0:
            playing_node = playing_node[0]
            playing_node.vol = min(MAX_VOL, playing_node.vol + vol)
            # print 'amp'
            return

        # If node is an AmplifierNode, regulate
        elif isinstance(node, graph.AmplifierNode):
            # print 'amplify'
            vol = max(0.0, vol + self.get_regulation())

        self._state_nodes.append(NodeState(node, vol))

    def get_regulation(self):
        return (self._target - len(self._state_nodes)) / 5.0

    def _get_base_frame(self):
        if not hasattr(self, '_baseframe'):
            nodes = self.graph.get_nodes()
            w = max([X.pt[0] for X in nodes])
            h = max([X.pt[1] for X in nodes])

            out = np.zeros((h,w,3), dtype=np.uint8)

            for edge in self.graph.get_edges():
                cv2.line(out, edge.a.pt, edge.b.pt, (100, 100, 100))

            for node in nodes:
                if isinstance(node, graph.AmplifierNode):
                    cv2.circle(out, node.pt, 3, (50, 50, 50), -1)
                else:
                    cv2.circle(out, node.pt, 3, (200, 200, 200), -1)
                    # cv2.putText(out, "%d" % (node.group), node.pt, cv2.FONT_HERSHEY_PLAIN, 1, (255,255,255))

            self._baseframe = out

        return self._baseframe


    def draw(self):
        "Return a np-array representing instantaneous state of the Player"
        out = self._get_base_frame().copy()

        for edgestate in self._state_edges:
            cv2.line(out, edgestate.edge.a.pt, edgestate.get_position(), (0, 255, 255))
        for nodestate in self._state_nodes:
            cv2.circle(out, nodestate.node.pt, 5, (0, 255, 255), -1)

        status = "%02d active (t=%02d,d=%.2f,s=%d)" % (len(self._state_nodes), self._target, self._decay, self._speed)
        cv2.putText(out, status, (10, 20), cv2.FONT_HERSHEY_PLAIN, 1, (255,255,255))

        return out

if __name__=='__main__':
    import sys
    import numm

    USAGE = 'python player.py EDGES SOUND [SOUND [SOUND ...]]'

    if len(sys.argv) < 3:
        print USAGE
        sys.exit(1)

    g = graph.load_graph(sys.argv[1])
    graph.connect_to_samples(g, sys.argv[2:])

    p = Player(g, speed=50)

    # # Trigger everything
    # for n in g.get_nodes():
    #     if n.frames is not None:
    #         p.trigger(n, 1.0)

    # Trigger *something*
    p.trigger(g.get_nodes()[50], 1.0)

    out = []
    v_out = cv2.VideoWriter()
    fr = p._get_base_frame()
    if not v_out.open('out.avi', cv2.cv.CV_FOURCC(*'MJPG'), int(R/2048), (fr.shape[1], fr.shape[0]), True):
        raise RuntimeError

    while p.active() and len(out) < 21*60:
        v_out.write(p.draw())
        out.append(p.next())

        print len(out)

    out = np.concatenate(out)

    out /= out.max() / float(2**15-1)

    numm.np2sound(out.astype(np.int16),
                  'out.wav')
