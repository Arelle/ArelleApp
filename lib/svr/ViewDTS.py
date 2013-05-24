'''
Created on May 19, 2013

@author: Mark V Systems Limited
(c) Copyright 2013 Mark V Systems Limited, All rights reserved.
'''
from XbrlSemanticGraphDB import XbrlSemanticGraphDatabaseConnection

def viewDTS(request):
    dbConn = XbrlSemanticGraphDatabaseConnection(request)
    results = dbConn.execute(u"View DTS", u"""
        def dtsRows(docs, visited) {
            def rows = []
            docs.each {
                  def row = ['id':it.id,'data':[new File(it.url).getName() + '-' + it.document_type]]
                  if (!visited.contains(it.url)) {
                    visited.add(it.url)
                    def refs = dtsRows(it.out('referenced_document'), visited)
                    if (refs) {
                        row['rows'] = refs
                    }
                    visited.remove(it.url)
                  rows << row
                  }
            }
            rows
        }
        ['rows':dtsRows(g.v(""" + dbConn.accessionId + u""").out('entry_document'),new HashSet())]
    """)[u"results"][0]  # returned dict from Gremlin is in a list, just want the dict
    dbConn.close()
    return results