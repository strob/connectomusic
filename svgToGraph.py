import xml
import re

class Node:
    def __init__(self, el):
        self._id = el.getAttribute('id')
        for key in ['cx', 'cy', 'rx']:
            setattr(self, key, float(el.getAttribute('sodipodi:'+key)))

    def get_center(self):
        return (self.cx, self.cy)
    def get_radius(self):
        return self.rx

    def __repr__(self):
        return '<node: (%.2f,%.2f) r=%.2f>' % (self.get_center()[0], self.get_center()[1], self.get_radius())

class Correction(Node):
    def __init__(self, transform, node):
        self._id = transform.getAttribute('id')
        self.node = node

        # XXX: assume that only a single translation has been applied.
        self.transform = transform.getAttribute('transform')
        if 'translate' in self.transform:
            self.tx, self.ty = [float(X) for X in re.findall(r'[-\d\.]+', self.transform)]
        else:
            self.tx = 0
            self.ty = 0

    def get_center(self):
        return (self.node.cx+self.tx, self.node.cy+self.ty)

    @classmethod
    def fromlist(cls, transform, nodelist):
        nodeid = transform.getAttribute('xlink:href')[1:]
        node = filter(lambda x: x._id==nodeid, nodelist)[0]
        return cls(transform, node)

class Graph:
    def __init__(self, path):
        self.doc = xml.dom.minidom.parse(path)

        self.layers = {}
        for layer in self.doc.getElementsByTagName('g'):
            self.layers[layer.getAttribute('inkscape:label')] = layer

        self.left_nodes = [Node(X) for X in self.layers['Dots'].getElementsByTagName('path')]
        self.right_nodes = [Node(X) for X in self.layers['Right_Dots'].getElementsByTagName('path')] + \
                           [Correction.fromlist(X, self.left_nodes) for X in self.layers['Right_Adjustments'].getElementsByTagName('use')]
