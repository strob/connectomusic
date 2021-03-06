import sys
from PyQt4 import QtGui
from PyQt4 import QtCore

from svgToGraph import Graph
import numm
import numpy as np

import pickle

graph = Graph('node_map.svg')

app = QtGui.QApplication(sys.argv)
app.setApplicationName('connectomusic')

class MView(QtGui.QGraphicsView):
    def wheelEvent(self, event):
        factor = 1.2
        if (event.delta() < 0):
            factor = 1.0 / factor
        self.scale(factor, factor)

scene = QtGui.QGraphicsScene()
#view = QtGui.QGraphicsView(scene)
view = MView(scene)

# left = QtGui.QPixmap('linke_seite.png')
# scene.addPixmap(left)
 
right = QtGui.QPixmap('right_aligned.png')
scene.addPixmap(right)

EDGES = graph.getEdges()
def saveEdges():
    pickle.dump(EDGES, open('ALL_EDGES.pkl', 'w'))
def addEdge(node1, node2):
    if node1.get_center()[0] < node2.get_center()[0]:
        EDGES.add((node1, node2))
    else:
        EDGES.add((node2, node1))
    saveEdges()
def removeEdge(node1, node2):
    if (node1, node2) in EDGES:
        EDGES.remove((node1, node2))
    else:
        EDGES.remove((node2, node1))
    saveEdges()
def hasEdge(node1, node2):
    return (node1, node2) in EDGES or (node2, node1) in EDGES

nodeToGraphMap = {}

node_arr = np.array([X.get_center() for X in graph.right_nodes])

def nearest_node(fromnode, x, y):
    dists = np.hypot(*(node_arr-[x,y]).T)
    d_sorted = dists.argsort()

    o_idx = 0
    while o_idx < len(dists):
        node = graph.right_nodes[d_sorted[o_idx]]
        if node != fromnode and not hasEdge(node, fromnode):
            return node
        o_idx += 1
    print 'uh-oh -- no more candidate nodes?'

class QGEdge(QtGui.QGraphicsLineItem):
    def __init__(self, node1, node2):
        self.node1 = node1
        self.node2 = node2

        x1,y1 = self.node1.get_center()
        x2,y2 = self.node2.get_center()
        QtGui.QGraphicsLineItem.__init__(self, x1, y1, x2, y2)

        self.setAcceptHoverEvents(True)

        pen = QtGui.QPen()
        pen.setColor(QtCore.Qt.black)
        pen.setWidth(3)

        self.setPen(pen)

        self.setZValue(5)

    def hoverEnterEvent(self, event):
        pen = self.pen()
        pen.setColor(QtCore.Qt.yellow)
        self.setPen(pen)
    def hoverLeaveEvent(self, event):
        pen = self.pen()
        pen.setColor(QtCore.Qt.black)
        self.setPen(pen)

    def mousePressEvent(self, event):
        scene.removeItem(self)
        removeEdge(self.node1, self.node2)

    def setNode2(self, node2):
        self.node2 = node2
        x1,y1 = self.node1.get_center()
        x2,y2 = self.node2.get_center()
        self.setLine(x1, y1, x2, y2)

_EDGES = set()
for n1,n2 in EDGES:
    qe = QGEdge(n1, n2)
    scene.addItem(qe)

class QGNode(QtGui.QGraphicsEllipseItem):
    def __init__(self, node):
        self.node = node

        x,y = node.get_center()
        r = node.get_radius()
        QtGui.QGraphicsEllipseItem.__init__(self, x-r, y-r, 2*r, 2*r)
        self.setBrush(QtCore.Qt.black)
        self.setAcceptHoverEvents(True)

        self.setZValue(10)

    def hoverEnterEvent(self, event):
        self.setBrush(QtCore.Qt.yellow)
        QtGui.QGraphicsEllipseItem.hoverEnterEvent(self, event)

    def mousePressEvent(self, event):
        print 'mousepress', self
        self.setBrush(QtCore.Qt.green)

        pos = event.scenePos()

        self.nearest_node = nearest_node(self.node, pos.x(), pos.y())
        print 'nn', self.node, self.nearest_node

        x1,y1 = self.node.get_center()
        x2,y2 = self.nearest_node.get_center()

        nodeToGraphMap[self.nearest_node].setBrush(QtCore.Qt.white)

        self.edgeline = QGEdge(self.node, self.nearest_node)

        scene.addItem(self.edgeline)

        # If this is called, mouseReleaseEvent/move events aren't fiblack
        # (I'm *sure* it's somehow internally consistent, don't worry)
        # QtGui.QGraphicsEllipseItem.mousePressEvent(self, event)

    def mouseMoveEvent(self, event):
        QtGui.QGraphicsEllipseItem.mouseMoveEvent(self, event)        

        pos = event.scenePos()

        new_nearest_node = nearest_node(self.node, pos.x(), pos.y())
        if self.nearest_node != new_nearest_node:
            # XXX: abstract ...
            nodeToGraphMap[self.nearest_node].setBrush(QtCore.Qt.green)

            self.nearest_node = new_nearest_node
            nodeToGraphMap[self.nearest_node].setBrush(QtCore.Qt.white)            

            self.edgeline.setNode2(self.nearest_node)


    def mouseReleaseEvent(self, event):
        print 'mouserelease', self
        self.setBrush(QtCore.Qt.blue)
        QtGui.QGraphicsEllipseItem.mouseReleaseEvent(self, event)

        nodeToGraphMap[self.nearest_node].setBrush(QtCore.Qt.green)
        addEdge(self.node, self.nearest_node)
    
    def hoverLeaveEvent(self, event):
        self.setBrush(QtCore.Qt.black)
        QtGui.QGraphicsEllipseItem.hoverLeaveEvent(self, event)

# nodebrush = QtGui.QBrush(QtGui.QColor('yellow'));

for node in graph.right_nodes:
# for node in graph.left_nodes:
    # ellipse = QtGui.QGraphicsEllipseItem(x-r, y-r, 2*r, 2*r)
    ellipse = QGNode(node)
    # ellipse.setBrush(nodebrush)
    scene.addItem(ellipse)

    nodeToGraphMap[node] = ellipse



view.show()

if __name__=='__main__':
    app.exec_()
