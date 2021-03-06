import graph

import numpy as np
import cv2
import numm

import glob
import os
import json

R = 44100.0
MAX_VOL = 1.5

def _resize(buf, size):
    out = np.zeros((size[1],size[0],3), dtype=np.uint8)
    x_idx = np.linspace(0, buf.shape[1], out.shape[1], endpoint=False).astype(int)
    y_idx = np.linspace(0, buf.shape[0], out.shape[0], endpoint=False).astype(int)
    y_idx = y_idx.reshape((-1,1))

    out[:] = buf[y_idx,x_idx]
    return out

class EdgeState:
    def __init__(self, edge, decay=1.0, onend=None):
        self.edge = edge
        self.decay = decay
        self.percentage = 0.0
        self.onend = onend

    def iterate(self, t, speed, decay):
        "Returns True if we've reached B, False otherwise"
        npixels = t * speed
        dpercentage = npixels / self.edge.length

        self.percentage += dpercentage

        self.decay *= decay ** npixels

        if self.percentage > 1.0:
            if self.onend:
                self.onend(self)
            return True

        return False

    def get_position(self):
        return tuple([int(self.edge.a.pt[X] + self.percentage * (self.edge.b.pt[X]-self.edge.a.pt[X]))
                      for X in [0, 1]])

class NodeState:
    def __init__(self, node, vol=1.0, frame=0, onend=None):
        self.node = node
        self.vol = vol
        self.frame = frame
        self.onend = onend

    def iterate(self, buf):
        "Mixes into buffer; returns True if finished with sound, False otherwise"

        if isinstance(self.node, graph.AmplifierNode):
            if self.onend:
                self.onend(self)
            return True

        if self.node.frames is None:
            return True

        nframes = min(len(self.node.frames) - self.frame, len(buf))
        if(self.node.isloop):
            nframes = len(buf)

        #pan = self.node.pt[0]  / 400.0
        pan = self.node.pt[0]  / 1250.0
        #snd = (self.vol * self.node.frames[self.frame:self.frame+nframes])
        if self.node.isloop and nframes > len(self.node.frames)-self.frame:
            # Assume nframes < len(self.node.frames) -- beware tiny loops.
            snd = np.roll(self.node.frames, -self.frame, axis=0)[:nframes]
        else:
            snd = self.node.frames[self.frame:self.frame+nframes]

        buf[:nframes,1] += snd * pan
        buf[:nframes,0] += snd * (1-pan)

        self.frame += nframes

        if self.frame >= len(self.node.frames):
            if not self.node.isloop:
                self.node.release_sound()
            if self.onend:
                self.onend(self)
            return True

        return False

class Player:
    def __init__(self, graph, speed=50, decay=0.95, target_nnodes=10, burnbridges=False, flipped=False, scale=1, thick=1, bidirectional=False):
        self.graph = graph

        self._state_edges = []  # [EdgeState]
        self._state_nodes = []  # [NodeState]

        self._selection = []

        self._speed = speed     # px/sec
        self._decay = decay     # %/px

        self._target = target_nnodes

        self._flipped = False
        if flipped:
            self.flip()

        self._bidirectional = bidirectional

        self.burnbridges = burnbridges

        self._burnededges = {}  # edge -> True

        self._recording = False
        self._actions = []
        self._mouse = []
        self._samples = []
        self._divisor = 10000

        self.scale = scale
        self.thick = thick

        self._version = 0

    def flip(self):
        for e in self.graph.edges:
            e.flip()
        self.graph._compute_nodemap()
        self._flipped = not self._flipped
        self._baseframe = None

    def click(self, pos):
        # just for logging
        if self._recording:
            self._mouse.append(pos)
    def nummap(self, num):
        # logging
        if self._recording:
            self._nummap.append(num)

    def burntoggle(self):
        if self.burnbridges:
            # un-burn edges
            self._burnededges = {}

            # un-burn nodes
            for n in self.graph.get_all_nodes():
                n._burned = False
            self._baseframe = None
        else:
            pass
        
        self.burnbridges = not self.burnbridges

    def bidirectionaltoggle(self):
        if self._bidirectional:
            equal = filter(lambda x: x.a.nedges == x.b.nedges, self.graph.edges)
            if self._flipped:
                self.graph.edges = filter(lambda x: x.a.nedges < x.b.nedges, self.graph.edges)
            else:
                self.graph.edges = filter(lambda x: x.a.nedges > x.b.nedges, self.graph.edges)

            # reinsert ties -- in arbitrary (*gasp*) order
            ties = set()
            add = []
            for e in equal:
                if (e.a, e.b) in ties:
                    continue
                ties.add((e.b, e.a))
                add.append(e)
            self.graph.edges.extend(add)

        else:
            newedges = [graph.Edge(e.b, e.a) for e in self.graph.edges]
            self.graph.edges += newedges

        self.graph._compute_nodemap()
        self._baseframe = None
        self._bidirectional = not self._bidirectional

    def toggle_recording(self):
        if self._recording:
            # save recording
            numm.np2sound(np.concatenate(self._out), 'out.wav')
            print 'recording saved to out.wav'

            # save parameters
            params = {'target': self._target,
                      'flipped': self._flipped,
                      'sounds': self.graph.version,
                      'actions': self._actions,
                      'nummap': self._nummap,
                      'mouse': self._mouse,
                      'speed': self._speed}
            json.dump(params, open('out.params.json', 'w'))
            open('out.samples.txt', 'w').write('\n'.join(self._samples))

        else:
            print 'start recording'
        self._out = []
        self._actions = []
        self._mouse = []
        self._nummap = []
        self._samples = []
        self._recording = not self._recording
        return self._recording

    def mix(self, a):
        # return a
        divisor = max(max(1, a.max() / float(2**15-1)),
                      pow(len(self._state_nodes), 0.5))

        if divisor != self._divisor:
            div = np.linspace(self._divisor, divisor, len(a)).reshape((len(a),-1))
            # print 'fade', self._divisor, divisor
        else:
            div = divisor
        # print divisor

        self._divisor = divisor

        # print 'div', div
        a /= div
        return a.astype(np.int16)


    def set_sound_version(self, N=2):
        VERSIONS = ['final_material_tt_bearbeit_(138)',
                    'final_material_tt_bearbeit_NEU_gekurzt_(171)',
                    'final_material_tt_bearbeit_2nd_order_NEUER_(450)']
        version = VERSIONS[N]

        files = glob.glob('snd/%s/*.npy' % (version))

        # split by nedges
        split = {}

        def _get_group(x):
            return int(os.path.basename(x).split('_')[0])

        for f in sorted(files):
            grp = _get_group(f)
            if not split.has_key(grp):
                split[grp] = []
            else:
                split[grp].append(f)

        self.graph.samplemap = split
        self.graph.cache_sounds()

        self._version = N

    def next(self, buffer_size=2048):
        "Increment time unit and return sound buffer (as np-array)"

        # print '%d active edges' % (len(self._state_edges))
        t = buffer_size / R
        for edgestate in self._state_edges:
            # print '    %d%% (%.2f)' % (edgestate.percentage * 100, edgestate.decay)
            if edgestate.iterate(t, self._speed, self._decay):
                if not self.burnbridges:
                    # BB takes care of this.
                    self._state_edges.pop(self._state_edges.index(edgestate))

                if not edgestate.edge.b._burned:
                    self.trigger(edgestate.edge.b)

                # # destroy edge
                if self.burnbridges:
                    self.destroy_edge(edgestate.edge)

        out = np.zeros((buffer_size, 2), dtype=np.float32)
        # print '%d active nodes' % (len(self._state_nodes))
        for nodestate in self._state_nodes:
            # print '    %.2f (%d)' % (nodestate.vol, nodestate.frame)
            if nodestate.iterate(out):
                # Use looping nodes as regulators; pop only when regulation is negative.
                self._state_nodes.pop(self._state_nodes.index(nodestate))

                if self.burnbridges:
                    # burn sound
                    nodestate.node.burn()

                if nodestate.node.isloop and self.get_regulation() > 0 and not self.burnbridges:
                    # smoothly retrigger
                    self.trigger(nodestate.node, frame=(nodestate.frame % len(nodestate.node.frames)))

                if self.get_regulation() > 0:
                    # all nodes become regulatory

                    for target_edge in self.graph.node_edges(nodestate.node):
                        active_edges = filter(lambda x: x.edge == target_edge, self._state_edges)
                        if len(active_edges) == 0 and target_edge not in self._burnededges:
                            self._state_edges.append(EdgeState(target_edge, nodestate.vol))

        mixed = self.mix(out)
        if self._recording:
            self._out.append(mixed)
        return mixed

    def active(self):
        return len(self._state_edges) > 0 or len(self._state_nodes) > 0

    def log(self, action):
        if self._recording:
            self._actions.append(action)

    def trigger(self, node, vol=1.0, frame=0):
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
            # vol = max(0.0, vol + self.get_regulation())
            # binary regulation
            if self.get_regulation() < 0:
                return

        # log trigger
        if self._recording and node.frames is not None:
            timestamp = 0
            if len(self._out) > 0:
                timestamp = len(self._out) * len(self._out[0]) / 44100.0
            payload = node.payload
            pan = node.pt[0]  / 1250.0
            if payload:
                duration = len(node.frames) / 44100.0
                self._samples.append("%f\t%f\t%f\t%s" % (timestamp, timestamp+duration, pan, payload.replace('.npy', '')))

        self._state_nodes.append(NodeState(node, vol, frame=frame))

    def get_regulation(self):
        return (self._target - len(self._state_nodes)) / 5.0

    def trigger_selection(self):
        for n in self._selection:
            self.trigger(n)
        self._selection = []

    def select_by_nedges(self, N, limit=999):
        self._selection = self.graph.grpnodes.get(N, [])[:limit]

    def select_by_coords(self, pts):
        self._selection = [self.graph.nearest(*pt) for pt in pts]

    def destroy_edge(self, edge):
        self._burnededges[edge] = True
        base = self._get_base_frame()
        cv2.line(base, self.s(edge.a.pt), self.s(edge.b.pt), (200, 0, 0), int(np.ceil(self.scale*self.thick)))

        # look at edges FROM "B" that END AT "A"
        otheredge = filter(lambda x: x.b==edge.a, self.graph.nodes.get(edge.b,[]))
        if len(otheredge) == 1:
            otheredge = otheredge[0]
            self._burnededges[otheredge] = True
        else:
            print 'no other edge'

        # remove in-progress traversals
        self._state_edges = filter(lambda x: x.edge != edge and x.edge != otheredge, self._state_edges)

    def destroy_edge_old(self, edge):
        otheredge = self.graph.remove_edge(edge)
        # Update base frame, if it exists
        base = self._get_base_frame()
        cv2.line(base, self.s(edge.a.pt), self.s(edge.b.pt), (200, 0, 0), int(np.ceil(self.scale*self.thick)))

        # remove in-progress traversals
        self._state_edges = filter(lambda x: x.edge != edge and x.edge != otheredge, self._state_edges)

    def s(self, pt):
        return (int(pt[0]*self.scale), int(pt[1]*self.scale))

    def _get_base_frame(self):
        if not hasattr(self, '_baseframe') or self._baseframe is None:
            nodes = self.graph.get_all_nodes()
            w = max([X.pt[0] for X in nodes]) + 20
            h = max([X.pt[1] for X in nodes]) + 20
            self.origw = w
            self.origh = h
            w *= self.scale
            h *= self.scale

            out = np.zeros((h,w,3), dtype=np.uint8)
            direction = np.zeros((h,w,3), dtype=np.uint8)

            direction_px = 4

            for edge in self.graph.get_edges():
                cv2.line(out, self.s(edge.a.pt), self.s(edge.b.pt), (100, 100, 100), int(np.ceil(self.scale*self.thick)))

                # indicate direction of edge with a small green startline
                dir_percent = direction_px / edge.length
                dir_pt = (edge.a.pt[0]+dir_percent*(edge.b.pt[0]-edge.a.pt[0]),
                          edge.a.pt[1]+dir_percent*(edge.b.pt[1]-edge.a.pt[1]))
                cv2.line(direction, self.s(edge.a.pt), self.s(dir_pt), (255, 255, 255), int(np.ceil(self.scale*self.thick)))

            for edge in self._burnededges.keys():
                cv2.line(out, self.s(edge.a.pt), self.s(edge.b.pt), (200, 0, 0), int(np.ceil(self.scale*self.thick)))

            # for node in nodes:
            #     if isinstance(node, graph.AmplifierNode):
            #         cv2.circle(out, self.s(node.pt), int(3*scale), (50, 50, 50), -1)
            #     else:
            #         cv2.circle(out, self.s(node.pt), int(3*scale), (200, 200, 200), -1)
                    # cv2.putText(out, "%d" % (node.group), node.pt, cv2.FONT_HERSHEY_PLAIN, 1, (255,255,255))

            out[direction>0] = direction[direction>0]
            self._baseframe = out

        return self._baseframe


    def draw(self):
        "Return a np-array representing instantaneous state of the Player"
        out = self._get_base_frame().copy()

        for edgestate in self._state_edges:
            cv2.line(out, self.s(edgestate.edge.a.pt), self.s(edgestate.get_position()), (0, 255, 255), int(np.ceil(self.scale*self.thick)))
        for nodestate in self._state_nodes:
            if nodestate.node.frames is not None:
                r = ((len(nodestate.node.frames)-nodestate.frame) / float(len(nodestate.node.frames))) * 10
            else:
                r = 5
            color = (0, 255, 255)
            if nodestate.node.isloop:
                color = (255, 0, 255)
            cv2.circle(out, self.s(nodestate.node.pt), int(r*self.scale), color, -1)

        for node in self._selection:
            r = 10
            cv2.circle(out, self.s(node.pt), int(r*self.scale), (255, 255, 0), -1)

        status = self.get_status()
        cv2.putText(out, status, (10, 20), cv2.FONT_HERSHEY_PLAIN, 1, (150,150,150))

        return out

    def zoom(self, node, factor=5):
        "zoom in on a node and return a buffer the same size as the baseframe"

        # XXX: we *could* re-render, clipping at scale...

        out = self.draw()

        w = out.shape[1]/factor
        h = out.shape[0]/factor

        center = self.s(node.pt)
        center = (max(w/2, center[0]),
                  max(h/2, center[1]))

        return _resize(out[center[1]-h/2:center[1]+h/2,
                           center[0]-w/2:center[0]+w/2],
                       (out.shape[1],out.shape[0]))
        # return cv2.resize(out[center[1]-h/2:center[1]+h/2,
        #                       center[0]-w/2:center[0]+w/2],
        #                   (out.shape[1],out.shape[0]))

        

    def get_status(self):
        return "%02d active (T=%02d,S=%d,F=%d,Bi=%d,Bu=%d,V=%d)" % (len(self._state_nodes), self._target, self._speed, self._flipped, self._bidirectional, self.burnbridges, self._version)

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

    # out /= out.max() / float(2**15-1)

    numm.np2sound(out, 'out.wav')
