'''
Created on May 19, 2013

@author: Mark V Systems Limited
(c) Copyright 2013 Mark V Systems Limited, All rights reserved.
'''
from XbrlSemanticGraphDB import XbrlSemanticGraphDatabaseConnection

def viewAccessions(request):
    dbConn = XbrlSemanticGraphDatabaseConnection(request)
    results = dbConn.execute(u"View Accessions", u"""
        def messagesLevelsCount(accessionV) {
            def levelCounts = [:]
            def codetypeCounts = [:]
            accessionV.out('validation_messages').out('message').each {
                if (levelCounts.containsKey(it.level)) {
                    levelCounts[it.level] = levelCounts[it.level] + 1
                } else {
                    levelCounts[it.level] = 1
                }
                def code = it.code.startsWith('xml') ? 'XML' : (it.code.startsWith('xbrl') ? 'XBRL' : (it.code.startsWith('EFM') ? 'EFM' : (it.code.startsWith('US-BPG') ? 'BPG' : null)))
                if (code)
                    if (codetypeCounts.containsKey(code)) {
                        codetypeCounts[code] = codetypeCounts[code] + 1
                    } else {
                        codetypeCounts[code] = 1
                    }
            }
            def l = []
            levelCounts.each{k,v->l<<[k,v].join(' - ')}
            def c = []
            codetypeCounts.each{k,v->c<<[k,v].join(' - ')}
            [l.join(', '), c.join(', ')].join(', ')
        }
        ['rows':g.V('_class','accessions').out.as('data').as('id').select{it.id}{
            [it.filing_accession_number,
             it.accepted_timestamp,
             it.entry_url,it.creation_software?:'',
             messagesLevelsCount(it)] 
          }]
    """)[u"results"][0]  # returned dict from Gremlin is in a list, just want the dict
    dbConn.close()
    return results