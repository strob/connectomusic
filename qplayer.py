from PyQt4 import QtGui
from PyQt4 import QtCore
import tempfile
import Image
import numpy as np
import sys
import numm.ui
import threading

from player import Player
import midi
import graph

def _gray(n=125):
    return QtGui.QColor(n,n,n)
def _rgb(r,g,b):
    return QtGui.QColor(r,g,b)

class QEdge(QtGui.QGraphicsLineItem):
    def __init__(self, edge):
        self.edge = edge
        x1,y1 = edge.a.pt
        x2,y2 = edge.b.pt
        QtGui.QGraphicsLineItem.__init__(self, x1, y1, x2, y2)
        # self.setAcceptHoverEvents(True)
        pen = QtGui.QPen()
        pen.setColor(_gray())
        pen.setWidth(2) 
        self.setPen(pen)
        self.setZValue(5)

        # Express directionality with a sub-circle
        self.dircirc = QtGui.QGraphicsEllipseItem()
        self.dircirc.setBrush(_gray(255))
        self.dircirc.setParentItem(self)
        self.update()

    def update(self):
        x1,y1 = self.edge.a.pt
        x2,y2 = self.edge.b.pt

        ratio = self.edge.a.nedges / np.hypot(x2-x1, y2-y1)
        cx = x1 + ratio*(x2-x1)
        cy = y1 + ratio*(y2-y1)
        r = 3
        self.dircirc.setRect(cx-r,cy-r,2*r,2*r)
        

class QStateEdge(QtGui.QGraphicsLineItem):
    def __init__(self, state):
        self.state = state
        x1,y1 = state.edge.a.pt
        x2,y2 = state.get_position()
        QtGui.QGraphicsLineItem.__init__(self, x1, y1, x2, y2)
        # self.setAcceptHoverEvents(True)
        pen = QtGui.QPen()
        pen.setColor(_rgb(255,0,0))
        pen.setWidth(3)
        self.setPen(pen)
        self.setZValue(7)
    def update(self):
        x1,y1 = self.state.edge.a.pt
        x2,y2 = self.state.get_position()
        self.setLine(x1,y1,x2,y2)

class QNode(QtGui.QGraphicsEllipseItem):
    def __init__(self, node):
        self.node = node
        x,y = node.pt
        r = max(3,node.nedges)
        QtGui.QGraphicsEllipseItem.__init__(self, x-r, y-r, 2*r, 2*r)
        if isinstance(node, graph.AmplifierNode):
            self.setBrush(_gray())
        else:
            if node.isloop:
                self.setBrush(_rgb(0,0,255))
            else:
                self.setBrush(_gray(255))

            self.txt = QtGui.QGraphicsSimpleTextItem(str(node.group))
            self.txt.setBrush(_gray())
            self.txt.setParentItem(self)
            self.txt.setPos(x-r, y-r)

        # self.setAcceptHoverEvents(True)
        self.setZValue(10)


class QStateNode(QtGui.QGraphicsEllipseItem):
    def __init__(self, state):
        self.state = state
        x,y = state.node.pt
        r = int(max(3,state.node.nedges) * 1.5)
        QtGui.QGraphicsEllipseItem.__init__(self, x-r, y-r, 2*r, 2*r)
        if state.node.isloop:
            self.setBrush(_rgb(0,255,255))
        else:
            self.setBrush(_rgb(255,0,0))
        self.setZValue(15)
    def update(self):
        state = self.state
        if not hasattr(state.node, 'frames') or state.node.frames is None:
            return

        x,y = state.node.pt
        r = ((len(state.node.frames)-state.frame) / float(len(state.node.frames))) * int(max(3,state.node.nedges) * 1.5)
        self.setRect(x-r, y-r, 2*r, 2*r)
        

class QPlayer(QtGui.QGraphicsScene):
    def __init__(self, player):
        self.player = player
        QtGui.QGraphicsScene.__init__(self)

        self.setBackgroundBrush(_gray(0))

        self.base()
        self._stately = {}
        self._remove = []

    def showrec(self):
        self.rec = QtGui.QGraphicsSimpleTextItem('rec');
        self.rec.setPos(800,10)
        self.rec.setBrush(_rgb(255,0,0))
        self.addItem(self.rec)

    def hiderec(self):
        self.removeItem(self.rec)

    def base(self):
        self.text = QtGui.QGraphicsSimpleTextItem(self.player.get_status())
        self.text.setPos(10, 10)
        self.text.setBrush(_gray(255))
        self.addItem(self.text)
        self.qedges = []

        for edge in self.player.graph.get_edges():
            qedge = QEdge(edge)
            self.qedges.append(qedge)
            self.addItem(qedge)

        for node in self.player.graph.get_nodes():
            self.addItem(QNode(node))

    def remove(self, stately):
        self._remove.append(self._stately[stately])
        del self._stately[stately]

    def update(self):
        while len(self._remove):
            self.removeItem(self._remove.pop())
            
        for edgestate in self.player._state_edges:
            if edgestate not in self._stately:
                self._stately[edgestate] = QStateEdge(edgestate)
                self.addItem(self._stately[edgestate])
                edgestate.onend = self.remove
            self._stately[edgestate].update()

        for nodestate in self.player._state_nodes:
            if nodestate not in self._stately:
                self._stately[nodestate] = QStateNode(nodestate)
                self.addItem(self._stately[nodestate])
                nodestate.onend = self.remove
            self._stately[nodestate].update()

        self.text.setText(self.player.get_status())

        if self.player._recording and len(self.player._out)>0:
            self.rec.setText("%.2fs" % ((1.0/44100) * len(self.player._out) * len(self.player._out[0])))

    def mousePressEvent(self, event):
        print 'press'
        pos = event.scenePos()
        nearest_node = g.nearest(pos.x(), pos.y())
        p.trigger(nearest_node, 1.0)
        p.log('press %d (%d,%d)' % (nearest_node.group, nearest_node.pt[0], nearest_node.pt[1]))
        p.click(nearest_node.pt)

class QView(QtGui.QGraphicsView):
    def __init__(self, player):
        self.qplay = QPlayer(p)
        # scene = QtGui.QGraphicsScene()
        # scene.addItem(self.qplay)

        QtGui.QGraphicsView.__init__(self, self.qplay)

        self.startTimer(50)

    def wheelEvent(self, event):
        factor = 1.1
        if (event.delta() < 0):
            factor = 1.0 / factor
        self.scale(factor, factor)

    def keyPressEvent(self, event):
        print event.text()
        print event.key()

        key = event.key()

        if key == QtCore.Qt.Key_F:
            # Flip all edges
            print 'flip'
            p.flip()
            for qe in self.qplay.qedges:
                qe.update()
        elif key == QtCore.Qt.Key_R:
            is_rec = p.toggle_recording()
            if is_rec:
                self.qplay.showrec()
            else:
                self.qplay.hiderec()
        

        elif key == QtCore.Qt.Key_P:
            p._target -= 1
        elif key == QtCore.Qt.Key_N:
            p._target += 1
        elif key == QtCore.Qt.Key_S:
            p._speed *= 1.1
        elif key == QtCore.Qt.Key_W:
            p._speed *= 0.9

    def timerEvent(self, ev):
        self.qplay.update()
        QtGui.QGraphicsView.timerEvent(self, ev)

def run():
    def mthread():
        onetosixteen = [
            [153, 61, 42, 0],
            [153, 69, 85, 0],
            [153, 65, 71, 0],
            [153, 63, 95, 0],
            [153, 60, 109, 0],
            [153, 59, 121, 0],
            [153, 57, 121, 0],
            [153, 55, 126, 0],
            [153, 49, 124, 0],
            [153, 51, 117, 0],
            [153, 68, 117, 0],
            [153, 56, 126, 0],
            [153, 48, 121, 0],
            [153, 52, 121, 0],
            [153, 54, 114, 0],
            [153, 58, 117, 0]]
        nummap = {}
        for idx,(_f1,num,_f2,_f3) in enumerate(onetosixteen):
            nummap[num] = idx+1

        for ev in midi.events():
            "[185, 20, 71, 0]"
            "[185, 21, 4, 0]"
            print ev
            if ev[1] == 20:
                # left knob == target
                p._target = ev[2] / 5.0
            elif ev[1] == 21:
                # right knob == speed
                p._speed = ev[2] * 2.5
            elif ev[0] == 201:
                # flip
                p.flip()
                for qe in view.qplay.qedges:
                    qe.update()
                
            elif ev[0] == 153 and ev[1] in nummap:
                num = nummap[ev[1]]
                for node in p.graph.grpnodes.get(num,[]):
                    p.trigger(node, ev[2] / 100.0)
                p.log('nummap %d' % (num))
                p.nummap(num)
    midithread = threading.Thread(target=mthread)
    midithread.start()


    def audio():
        divisor = [1]
        def a_out(a=None, **kw):
            # divisor[0] = max(1, len(p._state_nodes))

            # out = p.next(len(a))
            # divisor[0] = max(out.max() / float(2**15-1), divisor[0])

            # out /= divisor
            # a[:] = out.astype(np.int16)
            a[:] = p.next(len(a))

        numm.ui.NummRun(a_out).run()
    audiothread = threading.Thread(target=audio)
    audiothread.start()

    app.exec_()

if __name__=='__main__':
    app = QtGui.QApplication(sys.argv)
    app.setApplicationName('qplayer')

    print 'load graph'
    # g = graph.load_graph(sys.argv[1]=='left')
    # print 'connect to samples'
    # graph.connect_to_samples(g, sys.argv[2:])
    sounds = None
    if len(sys.argv) > 1:
        sounds = sys.argv[1]
    g = graph.connected_directed_graph(sounds)

    print 'qview'
    p = Player(g)
    view = QView(p)

    view.show()

    run()

    # import cProfile
    # cProfile.run('run()', 'proofile')
