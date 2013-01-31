import argparse
import json
import sys
import os

from twisted.internet import reactor, inotify
from twisted.python import filepath
from twisted.web import resource, server, static

import autobahn.websocket as ws

class Protocol(ws.WebSocketServerProtocol):
    def onOpen(self):
        self.factory.register(self)

    def connectionLost(self, reason):
        ws.WebSocketServerProtocol.connectionLost(self, reason)
        self.factory.unregister(self)

    def onMessage(self, msg, binary=False):
        self.factory.relay(self, msg)

class Factory(ws.WebSocketServerFactory):
   def __init__(self, url, debug=False):
      ws.WebSocketServerFactory.__init__(self, url, debug=debug)
      self.clients = []
      self.params = {
          "speed": 0.3,
          "target": 0.1,
          "sounds": "s2",
          "mode": "down"}

   def relay(self, client, msg):
       try:
           d = json.loads(msg)
       except Exception:
           print 'bad message :(', msg
           return

       if d.get("type") == "set":
           self.params[d["key"]] = d["value"]

       for c in self.clients:
           if c != client:
               c.sendMessage(msg)

   def register(self, client):
      if not client in self.clients:
         print "registered client " + client.peerstr
         self.clients.append(client)
         client.sendMessage(json.dumps({"params": self.params, "type": "reset"}))

   def unregister(self, client):
      if client in self.clients:
         print "unregistered client " + client.peerstr
         self.clients.remove(client)

class Root(resource.Resource):
    def __init__(self):
        resource.Resource.__init__(self)
        site = "Nothing to see here!"
        self.putChild('', static.Data(site, 'text/html'))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port',
                        type=int, default=8123, help='port')
    parser.add_argument('--wsport',
                        type=int, default=8124, help='websocket port')

    args = parser.parse_args()

    site = server.Site(Root())
    reactor.listenTCP(args.port, site)

    factory = Factory("ws://localhost:%d" % (args.wsport))
    factory.protocol = Protocol
    ws.listenWS(factory)

    print 'running on port %d' % (args.port)

    # XXX: How to run websockets without site?
    reactor.run()

if __name__=='__main__':
    main()
