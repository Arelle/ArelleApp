'''
Created on May 19, 2013

@author: Mark V Systems Limited
(c) Copyright 2013 Mark V Systems Limited, All rights reserved.
'''
from XbrlSemanticGraphDB import XbrlSemanticGraphDatabaseConnection

def viewAspects(request):
    dbConn = XbrlSemanticGraphDatabaseConnection(request)
    results = dbConn.execute(u"View Aspects", 
        dbConn.gDefAspectLabel + u"""
        aspectRows = []
        g.v('""" + dbConn.accessionId + u"""').out('dts').out('dts_aspect_proxy').
                order{aspectLabel(it.a)<=>aspectLabel(it.b)}.each{
            aspectProxy = it
            label = aspectLabel(it)
            it.in('proxy').each {
                dataTypeIt = it.out('data_type')
                baseTypeIt = it.out('base_xbrli_type')
                aspectRows<<['id':aspectProxy.id,'data':[
                                label,it.name,
                                it.periodType?:'',
                                it.balance?:'',
                                dataTypeIt.hasNext() ? dataTypeIt.next().name : '',
                                baseTypeIt.hasNext() ? baseTypeIt.next().name : '']]
            }
        }
        ['rows':aspectRows]
    """)[u"results"][0]  # returned dict from Gremlin is in a list, just want the dict
    dbConn.close()
    return results

def selectAspects(request):
    dbConn = XbrlSemanticGraphDatabaseConnection(request)
    results = dbConn.execute(u"Select Aspects", u"""
        def _id = '""" + dbConn.id.strip() + u"""'
        def n = g.v(_id)
        if (!n) {
            def e = g.e(_id)
            if (e && e.label == 'rel')
                n = e.inV.next()
        }
        def _class = n ? n._class : null
        def result = 0
        if (_class == 'data_point') { 
            result = n.out('base_item')[0].id;
        } else if (_class == 'aspect_proxy') {
            result = n.id
        } else if (_class == 'relationship') {
            result = n.out('target')[0].id
        } else if (_class == 'root') {
            result = n.out('aspect')[0].id
        } else if (_class == 'message') {
            result = n.out('message_ref')[0].id
        }
        result
    """)[u"results"]
    dbConn.close()
    return results