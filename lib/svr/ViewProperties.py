'''
Created on May 19, 2013

@author: Mark V Systems Limited
(c) Copyright 2013 Mark V Systems Limited, All rights reserved.
'''
from XbrlSemanticGraphDB import XbrlSemanticGraphDatabaseConnection, decompressResults

def viewProperties(request):
    dbConn = XbrlSemanticGraphDatabaseConnection(request)
    results = dbConn.execute(u"View Properties", 
        dbConn.gDefAspectLabel + u"""
        def n = null
        def e = null
        def _id = '""" + dbConn.id.strip() + u"""'
        try {
            n = g.v(_id)
            if (!n)
                e = g.e(_id)
        } catch (Exception e1) {
            try {
                e = g.e(_id)
            } catch (Exception e2) {
            }
        }
        def _class = n ? n._class : null
        def _label = e ? e.label : null
        def rows = []
        if (_class == 'data_point') { \
            rows << ['id':1, 'data':['source line', n.source_line]]
            rows << ['id':2, 'data':['base item', aspectLabel(n.out('base_item')[0])]]
            if (n.context) { \
                aspects = []
                n.out('entity_identifier').each { \
                    aspects << ['id':3, 'data':['entity', it.identifier], \
                                'rows':[['id':4, 'data':['scheme', it.scheme]]]]
                }
                n.out('period').each { \
                    if (it.hasNot('forever',null)) { \
                        aspects << ['id':5, 'data':['forever', '']]
                    } else if (it.hasNot('start_date',null)) { \
                        aspects << ['id':5, 'data':['start date', it.start_date]]
                        aspects << ['id':6, 'data':['end date', it.end_date]]
                    } else if (it.hasNot('instant',null)) { \
                        aspects << ['id':5, 'data':['instant', it.instant]]
                    }
                }
                n.out('aspect_value_selection').order{it.a.name <=> it.b.name}.each { \
                    if (it.out('aspect')) { \
                        aspects << ['id':it.id, 'data':[ \
                                        aspectLabel(it.out('aspect')[0]), \
                                        it.out('aspect_value') ? aspectLabel(it.out('aspect_value')[0]) : \
                                                                (it.typed_value?: '')]]
                    }
                }
                rows << ['id':7, 'data':['contextRef', n.context?:''], rows: aspects]
            }
            rows << ['id':8, 'data':['unitRef', n.unit?:'']]
            if (n.precision) {rows << ['id':9, 'data':['precision', n.precision]]}
            if (n.decimals) {rows << ['id':10, 'data':['decimals', n.decimals]]}
            rows << ['id':11, 'data':['value', n.effective_value?:n.value?:'']]
        } else if (_class == 'aspect_proxy') { \
            rows << ['id':1, 'data':['aspect label', aspectLabel(n)]]
            def aspectIt = n.in('proxy')
            if (aspectIt.hasNext()) { \
                aspect = aspectIt.next()
                rows << ['id':2, 'data':['aspect name', aspect.name]]
                dataTypeIt = aspect.out('data_type')
                baseTypeIt = aspect.out('base_xbrli_type')
                rows << ['id':3, 'data':['period type', aspect.periodType?:'']]
                rows << ['id':4, 'data':['balance', aspect.balance?:'']]
                rows << ['id':5, 'data':['data type', dataTypeIt.hasNext() ? dataTypeIt.next().name : '']]
                rows << ['id':6, 'data':['base type', baseTypeIt.hasNext() ? baseTypeIt.next().name : '']]
            }
        } else if (_label == 'rel') { \
            def a = e.inV.next()
            rows << ['id':1, 'data':['aspect label', aspectLabel(a)]]
            def aspectIt = a.in('proxy')
            if (aspectIt.hasNext()) { \
                aspect = aspectIt.next()
                rows << ['id':2, 'data':['aspect name', aspect.name]]
                dataTypeIt = aspect.out('data_type')
                baseTypeIt = aspect.out('base_xbrli_type')
                rows << ['id':3, 'data':['period type', aspect.periodType?:'']]
                rows << ['id':4, 'data':['balance', aspect.balance?:'']]
                rows << ['id':5, 'data':['data type', dataTypeIt.hasNext() ? dataTypeIt.next().name : '']]
                rows << ['id':6, 'data':['base type', baseTypeIt.hasNext() ? baseTypeIt.next().name : '']]
            }
            def relSet = g.v(e.rel_set)
            rows << ['id':7, 'data':['linkrole', relSet.linkrole?:'']]
            rows << ['id':8, 'data':['definition', relSet.linkdefinition?:'']]
            rows << ['id':9, 'data':['arcrole', relSet.arcrole?:'']]
            if (e.hasNot('preferred_label', null)) { \
                rows << ['id':10, 'data':['preferred label', e.preferred_label?:'']]
            }
        } else if (_label == 'root') { \
            def a = e.inV.next()
            def aspectIt = e.out('aspect').in('proxy')
            if (aspectIt.hasNext()) { \
                aspect = aspectIt.next()
                rows << ['id':1, 'data':['aspect label', aspectLabel(aspect)]]
                rows << ['id':2, 'data':['aspect name', aspect.name]]
                dataTypeIt = aspect.out('data_type')
                baseTypeIt = aspect.out('base_xbrli_type')
                rows << ['id':3, 'data':['period type', aspect.periodType?:'']]
                rows << ['id':4, 'data':['balance', aspect.balance?:'']]
                rows << ['id':5, 'data':['data type', dataTypeIt.hasNext() ? dataTypeIt.next().name : '']]
                rows << ['id':6, 'data':['base type', baseTypeIt.hasNext() ? baseTypeIt.next().name : '']]
            }
            def relSetIt = e.inV
            if (relSetIt.hasNext()) { \
                relSet = relSetIt.next()
                rows << ['id':7, 'data':['linkrole', relSet.linkrole?:'']]
                rows << ['id':8, 'data':['definition', relSet.linkdefinition?:'']]
                rows << ['id':9, 'data':['arcrole', relSet.arcrole?:'']]
            }
        }
        ['rows':rows]
    """)[u"results"][0]  # returned dict from Gremlin is in a list, just want the dict
    decompressResults(results)
    dbConn.close()
    return results
