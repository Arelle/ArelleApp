'''
Created on May 19, 2013

@author: Mark V Systems Limited
(c) Copyright 2013 Mark V Systems Limited, All rights reserved.
'''
from XbrlSemanticGraphDB import XbrlSemanticGraphDatabaseConnection

def viewDataPoints(request):
    dbConn = XbrlSemanticGraphDatabaseConnection(request)
    results = dbConn.execute(u"View Data Points", 
        dbConn.gDefAspectLabel + u"""
        ['rows':g.v(""" + dbConn.accessionId + u""").out('entry_document')
            .out('data_points').out('data_point')
            .order{it.a.source_line <=> it.b.source_line}
            .as('data').as('id').select{it.id}{
               [aspectLabel(it.out('base_item')[0]),
                   it.source_line,it.context?:'', it.unit?:'',
                   it.effective_value?:it.value?:'']
             }
        ]
    """)[u"results"][0]  # returned dict from Gremlin is in a list, just want the dict
    dbConn.close()
    return results

def selectDataPoints(request):
    dbConn = XbrlSemanticGraphDatabaseConnection(request)
    results = dbConn.execute(u"Select Data Points", u"""
        def n = g.v(""" + dbConn.id + u""")
        def _class = n._class
        def result = 0
        if (_class == 'data_point') {
            result = n.id
        } else {
            def aspectProxyIt
            if (_class == 'aspect_proxy') {
                aspectProxyIt = n._()
            } else if (_class == 'data_point') {
                aspectProxyIt = n.out('base_item')
            } else if (_class == 'relationship') {
                aspectProxyIt = n.out('target')
            } else if (_class == 'root') {
                aspectProxyIt = n.out('aspect')
            } else if (_class == 'message') {
                aspectProxyIt = n.out('message_ref')
            } else {
                aspectProxyIt = n.out('proxy')
            }
            result = aspectProxyIt.hasNext() ? aspectProxyIt.next().in('base_item')[0].id : null
        }
        result
    """)[u"results"]
    dbConn.close()
    return results