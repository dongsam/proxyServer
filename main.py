#!/usr/bin/python

import re
import sys
from twisted.internet import reactor, protocol

from twisted.web import http
from twisted.python import log

#log.startLogging(sys.stdout)

class ProxyClient(http.HTTPClient):
    
    def __init__(self, method, uri, postData, headers, originalRequest):
        self.method = method
        self.uri = uri
        print "1---" + self.uri
        #print "1---" + self.postData
        #if "se.naver.com" in uri:
        #    print "----------------------------" + self.uri
        #    self.uri = "http://kldp.org"
        #    print "----------------------------" + self.uri
        self.postData = postData
        self.headers = headers
        self.originalRequest = originalRequest
        self.contentLength = None

    def sendRequest(self):
        
        log.msg("Sending request: %s %s" % (self.method, self.uri))
        self.sendCommand(self.method, self.uri)

    def sendHeaders(self):
        for key, values in self.headers:
            if key.lower() == 'connection':
                values = ['close']
            elif key.lower() == 'keep-alive':
                next

            for value in values:
                self.sendHeader(key, value)
        self.endHeaders()

    def sendPostData(self):
        log.msg("Sending POST data")
        self.transport.write(self.postData)

    def connectionMade(self):
        log.msg("HTTP connection made")
        self.sendRequest()
        self.sendHeaders()
        if self.method == 'POST':
            self.sendPostData()

    def handleStatus(self, version, code, message):
        log.msg("Got server response: %s %s %s" % (version, code, message))
        self.originalRequest.setResponseCode(int(code), message)

    def handleHeader(self, key, value):
        if key.lower() == 'content-length':
            self.contentLength = value
        else:
            self.originalRequest.responseHeaders.addRawHeader(key, value)

    def handleResponse(self, data):        
	data = self.originalRequest.processResponse(data)
	if sys.argv[2] in data:
		data.replace(sys.argv[2],sys.argv[3])
	print data
        if self.contentLength != None:
            self.originalRequest.setHeader('Content-Length', len(data))

        self.originalRequest.write(data)

        self.originalRequest.finish()
        self.transport.loseConnection()

class ProxyClientFactory(protocol.ClientFactory):
    def __init__(self, method, uri, postData, headers, originalRequest):
        self.protocol = ProxyClient
        self.method = method
        self.uri = uri

        print "2---" + self.uri
        #print "2---" + self.postData
        
        #if uri == "http://www.google.com":
        #    self.uri = "http://naver.com"
        #    print "----------------------------" + self.uri
        
        self.postData = postData
        self.headers = headers
        self.originalRequest = originalRequest

        
        #print "*******************" + self.protocol
        #print "*******************" + self.method
        #print "*******************" + self.uri
        #if "static.nid.naver.com/login.nhn" in self.uri:
        #    print "########"
        #    self.uri = "kldp.org"
        #print "*******************" + self.postData
        #print "*******************" + self.headers
        #print "*******************" + self.originalRequest


    def buildProtocol(self, addr):
        
        return self.protocol(self.method, self.uri, self.postData,
                             self.headers, self.originalRequest)

    def clientConnectionFailed(self, connector, reason):
        log.err("Server connection failed: %s" % reason)
        self.originalRequest.setResponseCode(504)
        self.originalRequest.finish()

class ProxyRequest(http.Request):
    def __init__(self, channel, queued, reactor=reactor):
        http.Request.__init__(self, channel, queued)
        self.reactor = reactor

    def process(self):
        host = self.getHeader('host')
        #print "************************* " + host
        #host = "zxher.com"
        #log.msg("%s",host)
        #host = "220.95.233.172"
        #log.msg("%s",host)
        if not host:
            log.err("No host header given")
            self.setResponseCode(400)
            self.finish()
            return

        port = 80
        if ':' in host:
            host, port = host.split(':')
            port = int(port)
        
        if "www.naver.com" == host :
                print "www.naver.com -> kldp.org "
                host = "kldp.org"    

        self.setHost(host, port)

        self.content.seek(0, 0)
        postData = self.content.read()
        
        factory = ProxyClientFactory(self.method, self.uri, postData,
                                     self.requestHeaders.getAllRawHeaders(),
                                     self)
        self.reactor.connectTCP( host, port, factory)

    def processResponse(self, data):
	if sys.argv[2] in data:
		data.replace(sys.argv[2],sys.argv[3])
	return data

class TransparentProxy(http.HTTPChannel):
    requestFactory = ProxyRequest
 
class ProxyFactory(http.HTTPFactory):
    protocol = TransparentProxy
 
inputPort=8080
if sys.argv[1]:
	inputPort = sys.argv[1]

reactor.listenTCP(int(inputPort), ProxyFactory())
reactor.run()
