'''
Created on May 19, 2013

@author: Mark V Systems Limited
(c) Copyright 2013 Mark V Systems Limited, All rights reserved.
'''
from XbrlSemanticGraphDB import XbrlSemanticGraphDatabaseConnection

def viewMessages(request):
    dbConn = XbrlSemanticGraphDatabaseConnection(request)
    results = dbConn.execute(u"View Messages", u"""
        ['rows':g.v(""" + dbConn.accessionId + u""").out('validation_messages').out('message') \
            .order{it.a.seq <=> it.b.seq} \
            .as('data').as('id').select{it.id}{ \
               [it.seq, it.code, it.level, it.text?:''] \
        }]
    """)[u"results"][0]  # returned dict from Gremlin is in a list, just want the dict
    dbConn.close()
    return results
