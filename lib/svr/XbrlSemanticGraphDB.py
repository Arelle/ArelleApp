'''
Created on May 19, 2013

@author: Mark V Systems Limited
(c) Copyright 2013 Mark V Systems Limited, All rights reserved.
'''
from __future__ import division
from __future__ import with_statement
import json, sys, urllib, io, socket
from urllib import unquote
from base64 import b64decode
import urllib2 as proxyhandlers
from urllib2 import URLError, HTTPError

TRACEGREMLINFILE = None
TRACEGREMLINFILE = r"c:\temp\appsvrtrace.log"  # uncomment to trace SQL on connection (very big file!!!)

HTTPHEADERS = {'User-agent':   'Arelle/1.0',
               'Accept':       'application/json',
               'Content-Type': 'application/json'}

def testConnection(request):
    # determine if postgres port
    dbConn = XbrlSemanticGraphDatabaseConnection(request)
    results = dbConn.dbFeatures()
    dbConn.close()
    return results

class XbrlSemanticGraphDatabaseConnection:
    def __init__(self, request):
        self.request = request
        connection = unquote(request.get_cookie(u"rlConnection",default=u""))
        host, port, user, password, database = unicode(b64decode(connection)).split(u"|")
        connectionUrl = u"http://{0}:{1}".format(host, port or u'8182')
        self.url = connectionUrl + u'/graphs/' + database
        # Create an OpenerDirector with support for Basic HTTP Authentication...
        auth_handler = proxyhandlers.HTTPBasicAuthHandler()
        if user:
            auth_handler.add_password(realm=u'rexster',
                                      uri=connectionUrl,
                                      user=user,
                                      passwd=password)
        self.conn = proxyhandlers.build_opener(auth_handler)
        self.timeout = 30
        
    @property
    def accessionId(self):
        return self.request.query.accessionId

    @property
    def id(self):
        return self.request.query.id

    @property
    def arcrole(self):
        return self.request.query.arcrole

    def close(self, rollback=False):
        try:
            self.conn.close()
            self.__dict__.clear() # dereference everything
        except Exception as ex:
            self.__dict__.clear() # dereference everything
            raise
        
    def execute(self, activity, script, params=None):
        gremlin = {"script": script}
        if params:
            gremlin[u"params"] = params
        if TRACEGREMLINFILE:
            with io.open(TRACEGREMLINFILE, u"a", encoding=u'utf-8') as fh:
                fh.write(u"\n\n>>> sent: \n{0}".format(unicode(gremlin)))
        request = proxyhandlers.Request(self.url + "/tp/gremlin",
                                        data=json.dumps(gremlin, ensure_ascii=False).encode('utf-8'),
                                        headers=HTTPHEADERS)
        fp = None
        try:
            fp = self.conn.open(request, timeout=self.timeout)
            results = json.loads(fp.read().decode(u'utf-8'))
        except HTTPError as err:
            if err.code == 500: # results are not successful but returned nontheless
                results = json.loads(err.fp.read().decode(u'utf-8'))
            else:
                raise  # reraise any other errors
        finally:
            if fp:
                fp.close()
        if TRACEGREMLINFILE:
            with io.open(TRACEGREMLINFILE, u"a", encoding=u'utf-8') as fh:
                fh.write(u"\n\n>>> received: \n{0}".format(unicode(results)))
        if results['success'] == False:
            raise Exception(u"%(activity)s not successful: %(error)s" % {
                            u"activity": activity, "error": results.get(u'error')}) 
        return results
        
    def dbFeatures(self, timeout=10):
        t = 2
        while t < timeout:
            try:
                request = proxyhandlers.Request(self.url, headers=HTTPHEADERS)
                fp = None
                try:
                    fp = self.conn.open(request, timeout=self.timeout)
                    results = json.loads(fp.read().decode(u'utf-8'))
                except HTTPError as err:
                    if err.code == 500: # results are not successful but returned nontheless
                        results = json.loads(err.fp.read().decode(u'utf-8'))
                    else:
                        raise  # reraise any other errors
                finally:
                    if fp:
                        fp.close()
                if hasattr(results, u'message'):
                    raise Exception(u"Opening of Database not successful: %(error)s" % {
                                    "error": results.get(u'message')}) 
                return results
            except HTTPError:
                return [u"ok"]
            except URLError:
                raise # something is there but not postgres
            except socket.timeout:
                t = t + 2  # relax - try again with longer timeout
        raise Exception(u"Opening of Database not successful: timed out") 

    @property
    def gDefAspectLabel(self):
        return u"""
            def aspectLabel(aspectProxyVertex) {
                labelIt = aspectProxyVertex
                    .outE('rel').has('resource_role','http://www.xbrl.org/2003/role/label')
                    .inV.value
                if (labelIt.hasNext()) {
                    label = labelIt.next()
                } else {
                    label = ''
                    aspectProxyVertex.in('proxy').each{
                        label = it.name
                    }
                }
                label
            }
        """

        
    