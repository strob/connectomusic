class Graph:
  def __init__(self, edges):
    self.edges = edges

class Edge:
  def __init__(self, a, b):
    self.a = a
    self.b = b
    self.length = math.sqrt(
      pow(self.a.pt[0]-self.b.pt[0], 2)+
      pow(self.a.pt[1]-self.b.pt[1], 2))

class Node:
  def __init__(self, pt, frames):
    self.pt = pt
    self.frames = frames

class EdgeState:
  def __init__(self, edge):
    self.edge = edge
    self.percentage = 0.0

  def iterate(self, t, speed):
    "Returns True if we've reached B"
    npixels = t * speed
    dpercentage = npixels / self.edge.length

    self.percentage += dpercentage

    if self.percentage > 1.0:
      return True
    return False

class NodeState:
  def __init__(self, node, frame=0):
    self.node = node
    self.frame = frame

  def iterate(self, buf):
    "Mixes into buffer; True if finished"

    nframes = min(
      len(self.node.frames)-self.frame,
      len(buf))
    pan = self.node.pt[0]  / WIDTH
    snd = self.node.frames[self.frame:self.frame+nframes]

    buf[:nframes,1] += snd * pan
    buf[:nframes,0] += snd * (1-pan)

    self.frame += nframes

    if self.frame >= len(self.node.frames):
      return True

    return False

class Player:
  def __init__(self, graph):
    self.graph = graph

    self._state_edges = []  # [EdgeState]
    self._state_nodes = []  # [NodeState]

  def trigger(self, node, frame=0):
    "Schedule playback of node at next time unit."
    self._state_nodes.append(NodeState(node, frame))

  def next(self, buffer_size=2048):
    "Increment time unit and return sound buffer"

    t = buffer_size / R
    for edgestate in self._state_edges:
      if edgestate.iterate(t, SPEED):
        self._state_edges.pop(
          self._state_edges.index(edgestate))

        self.trigger(edgestate.edge.b)

        # destroy edge
        if BURN_BRIDGES:
          self.graph.edges.remove(edgestate.edge)

    out = np.zeros((buffer_size, 2), dtype=np.float32)
    for nodestate in self._state_nodes:
      if nodestate.iterate(out):
        self._state_nodes.pop(
          self._state_nodes.index(nodestate))

        if LOOPED_LETTERS and nodestate.node.isloop:
          # smoothly retrigger
          self.trigger(nodestate.node,
                 frame=(
              nodestate.frame % len(
                      nodestate.node.frames)))

        # propagate
        next_edge = lambda x:x.a==nodestate.node
        if BIDIRECTIONAL:
          next_edge = lambda x:x.a==nodestate.node or
                               x.b==nodestate.node
        for target_edge in filter(next_edge,
                                  self.graph.edges):
          self._state_edges.append(EdgeState(target_edge))

    return out
