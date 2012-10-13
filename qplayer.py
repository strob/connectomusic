from PyQt4 import QtGui
from PyQt4 import QtCore
import tempfile
import Image
import numpy as np
import sys
import numm
import threading

from player import Player
import midi
import graph


class QPlayer(QtGui.QGraphicsPixmapItem):
    def __init__(self, player):
        self.player = player
        QtGui.QGraphicsPixmapItem.__init__(self)
        self.update()

    def update(self):
        # XXX: avoid passing through disk/png!
        t = tempfile.NamedTemporaryFile(suffix='.png')
        Image.fromarray(self.player.draw()).save(t.name)
        self.setPixmap(QtGui.QPixmap(t.name))
        t.close()

    def mousePressEvent(self, event):
        print 'press'
        pos = event.scenePos()
        nearest_node = g.nearest(pos.x(), pos.y())
        p.trigger(nearest_node, 1.0)

class QView(QtGui.QGraphicsView):
    def __init__(self, player):
        self.qplay = QPlayer(p)
        scene = QtGui.QGraphicsScene()
        scene.addItem(self.qplay)

        QtGui.QGraphicsView.__init__(self, scene)

        self.startTimer(200)

    def keyPressEvent(self, event):
        print event.text()
        print event.key()

        if event.key() == QtCore.Qt.Key_P:
            p._target -= 1
        if event.key() == QtCore.Qt.Key_N:
            p._target += 1
        if event.key() == QtCore.Qt.Key_D:
            p._decay *= 1.1
        if event.key() == QtCore.Qt.Key_E:
            p._decay *= 0.9
        if event.key() == QtCore.Qt.Key_S:
            p._speed *= 1.1
        if event.key() == QtCore.Qt.Key_W:
            p._speed *= 0.9

    def timerEvent(self, ev):
        self.qplay.update()
        QtGui.QGraphicsView.timerEvent(self, ev)

def run():
    def mthread():
        for ev in midi.events():
            "[185, 20, 71, 0]"
            "[185, 21, 4, 0]"
            print ev
            if ev[1] == 20:
                # left knob == target
                p._target = ev[2] / 5.0
            elif ev[1] == 21:
                # right knob == speed
                p._speed = ev[2] * 5.0
    midithread = threading.Thread(target=mthread)
    midithread.start()


    def audio():
        divisor = [1]
        def a_out(a):
            divisor[0] = len(p._state_nodes)
            if divisor[0] == 0:
                divisor[0] = 1

            out = p.next(len(a))
            divisor[0] = max(out.max() / float(2**15-1), divisor[0])

            out /= divisor
            a[:] = out.astype(np.int16)

        numm.run(audio_out=a_out)
    audiothread = threading.Thread(target=audio)
    audiothread.start()

    app.exec_()

if __name__=='__main__':
    app = QtGui.QApplication(sys.argv)
    app.setApplicationName('qplayer')

    print 'load graph'
    g = graph.load_graph(sys.argv[1]=='left')
    print 'connect to samples'
    graph.connect_to_samples(g, sys.argv[2:])

    print 'qview'
    p = Player(g)
    view = QView(p)

    view.show()

    run()

    # import cProfile
    # cProfile.run('run()', 'proofile')
