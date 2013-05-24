'''
Created on May 19, 2013

@author: Mark V Systems Limited
(c) Copyright 2013 Mark V Systems Limited, All rights reserved.
'''
from XbrlSemanticGraphDB import XbrlSemanticGraphDatabaseConnection
import os

def viewRelationships(request):
    dbConn = XbrlSemanticGraphDatabaseConnection(request)
    results = dbConn.execute(u"View Relationships " + os.path.basename(dbConn.arcrole), 
        dbConn.gDefAspectLabel + 
        (u"""
        def relSetRows(relSetId, arcrole, relEs){
            def rows = []
            relEs.each {
                def targetAspectProxyIt = it.inV
                if (targetAspectProxyIt.hasNext()) {
                    def targetAspectProxy = targetAspectProxyIt.next()
                    def data = [aspectLabel(targetAspectProxy)]
                    if (arcrole.endsWith('summation-item')) {
                      data<<it.weight?:''
                      data<< targetAspectProxy.in('proxy').balance ?: ''
                    } else if (arcrole.endsWith('parent-child')) {
                      dataTypeIt = targetAspectProxy.in('proxy').out('data_type')
                      data<< (dataTypeIt.hasNext() ? dataTypeIt.next().name : '')
                    }
                    def row = ['id':it.id,'data':data]
                    if (targetAspectProxy.outE('rel').has('rel_set', relSetId)) {
                        row['rows'] = relSetRows(relSetId, arcrole, 
                                                 targetAspectProxy.outE('rel')
                                                     .has('rel_set', relSetId)
                                                     .order{it.a._order <=> it.b._order})
                    }
                    rows << row
                }
            }
            rows
        }
        def relSetRoots(relSetId, arcrole, rootEs){
            def rootRows = []
            rootEs.each{
                def rootAspectProxyIt = it.inV
                if (rootAspectProxyIt.hasNext()) {
                    def rootAspectProxy = rootAspectProxyIt.next()
                    rootRows << ['id':it.id,
                                 'data':[aspectLabel(rootAspectProxy)],
                                 'rows':relSetRows(relSetId, arcrole,
                                                   rootAspectProxy.outE('rel')
                                                       .has('rel_set', relSetId)
                                                       .order{it.a._order <=> it.b._order})]
               }
            }
            rootRows
        }
        relSets=g.v(""" + dbConn.accessionId + u""").out('dts').out('relationship_sets').out('relationship_set').has('arcrole','""" + dbConn.arcrole + u"""')
        def elrRows = []
        relSets.order{it.a.linkdefinition <=> it.b.linkdefinition}.each{
            elrRows<<['id':it.id,
                     'data':[it.linkdefinition],
                     'rows':relSetRoots(it.id.toInteger(), it.arcrole, it.outE('root'))]
        }
        ['rows':elrRows]
    """ if dbConn.arcrole != u"XBRL-dimensions" else u"""
        def relSetRows(relSetId, linkrole, relEs){
            def rows = []
            relEs.each {
                def targetAspectProxyIt = it.inV
                if (targetAspectProxyIt.hasNext()) {
                    def targetAspectProxy = targetAspectProxyIt.next()
                    def row = ['id':it.id,
                               'data':[aspectLabel(targetAspectProxy),
                                       it.arcrole?:'',
                                       it.cube_closed?:'',
                                       it.aspect_value_usable?:'']]
                    if (targetAspectProxy.outE('rel').has('rel_set', relSetId)) {
                        row['rows'] = relSetRows(relSetId,
                                                 it.target_linkrole ?: linkrole,
                                                 targetAspectProxy.outE('rel')
                                                         .has('rel_set', relSetId)
                                                         .order{it.a._order <=> it.b._order})
                    }
                    rows << row
                }
            }
            rows
        }
        def relSetRoots(relSetId, linkrole, rootEs){
            def rootRows = []
            rootEs.each{
                def rootAspectProxyIt = it.inV
                if (rootAspectProxyIt.hasNext()) {
                    def rootAspectProxy = rootAspectProxyIt.next()
                    rootRows << ['id':it.id,
                                 'data':[aspectLabel(rootAspectProxy)],
                                 'rows':relSetRows(relSetId, 
                                                   linkrole, 
                                                   rootAspectProxy.outE('rel')
                                                         .has('rel_set', relSetId)
                                                         .order{it.a._order <=> it.b._order})]
                }
            }
            rootRows
        }
        def relSets=g.v(""" + dbConn.accessionId + u""").out('dts').out('relationship_sets').out('relationship_set').has('arcrole','XBRL-dimensions')
        def elrRows = []
        relSets.order{it.a.linkdefinition <=> it.b.linkdefinition}.each{
            elrRows<<['id':it.id,
                     'data':[it.linkdefinition],
                     'rows':relSetRoots(it.id.toInteger(), it.linkrole, it.outE('root'))]
        }
        ['rows':elrRows]
    """))[u"results"][0]  # returned dict from Gremlin is in a list, just want the dict
    dbConn.close()
    return results

def selectRelationships(request):
    dbConn = XbrlSemanticGraphDatabaseConnection(request)
    results = dbConn.execute(u"Select Relationships " + os.path.basename(dbConn.arcrole), u"""
        def n = g.v(""" + dbConn.id + u""")
        def _class = n._class
        def aspectProxy
        def result = 0
        if (_class == 'aspect_proxy') {
            aspectProxy = n
        } else {
            def aspectProxyIt
            if (_class == 'data_point') {
                aspectProxyIt = n.out('base_item')
            } else if (_class == 'relationship') {
                aspectProxyIt = n.out('target')
            } else if (_class == 'message') {
                aspectProxyIt = n.out('message_ref')
            } else {
                aspectProxyIt = n.out('aspect')
            }
            aspectProxy = aspectProxyIt.hasNext() ? aspectProxyIt.next() : null
        }
        if (aspectProxy) {
            relIt = aspectProxy.in('target').in('relationship').has('arcrole','""" + dbConn.arcrole + u"""').back(2)
            result = relIt.hasNext() ? relIt.next().id : 0
        }
        result
    """)[u"results"]
    dbConn.close()
    return results