'''
Created on May 19, 2013

@author: Mark V Systems Limited
(c) Copyright 2013 Mark V Systems Limited, All rights reserved.
'''
from XbrlSemanticDB import XbrlSemanticDatabaseConnection

def viewAspects(request):
    dbConn = XbrlSemanticDatabaseConnection(request)
    if dbConn.filingId:
        _fromReport = "report r,"
        _whereDocument = """
           r.filing_id = {filingId} AND 
           (a.document_id = r.report_schema_doc_id OR
            a.document_id = r.standard_schema_doc_id)
           """.format(filingId=dbConn.filingId)
    elif dbConn.documentId: # query from documentId
        _fromReport = ""
        _whereDocument = """
           a.document_id = {documentId}
           """.format(documentId=dbConn.documentId)
    elif dbConn.documentUrl:
        _fromReport = "document d,"
        _whereDocument = """
           d.document_url = '{documentUrl}' 
           """.format(documentUrl=dbConn.documentUrl)
    else:
        _fromReport = ""
        _whereDocument = "FALSE"
    results = dbConn.execute("View Aspects", """
        {relSetForLabels} -- relationship set for labels
        SELECT a.aspect_id, lbl.value, a.name, a.period_type, a.balance, dt.name, a.base_type
        FROM {fromReport} label_relationship_set lrs, aspect a, data_type dt,
             relationship lrel, resource lbl
        WHERE {whereDocument} AND
           dt.data_type_id = a.datatype_id AND
           lrel.relationship_set_id = lrs.relationship_set_id AND lrel.from_id = a.aspect_id
           AND lrel.to_id = lbl.resource_id AND lbl.role = 'http://www.xbrl.org/2003/role/label'
        ORDER BY lbl.value, a.name 
        """.format(relSetForLabels=dbConn.withAspectLabelRelSetId,
                   fromReport=_fromReport,
                   whereDocument=_whereDocument))
    dbConn.close()
    return {"rows": [{"id": result[0], "data": result[1:]}
                     for result in results]}

def selectAspects(request):
    dbConn = XbrlSemanticDatabaseConnection(request)
    _id = dbConn.id.rpartition(":")[2]
    results = dbConn.execute("Select Aspects", """
        SELECT
        CASE WHEN (SELECT TRUE FROM aspect WHERE aspect_id = {0})
        THEN
          {0}::bigint
        ELSE (
          CASE WHEN (SELECT TRUE from relationship where relationship_id = {0})
          THEN (SELECT r.to_id FROM relationship r WHERE relationship_id = {0})
          ELSE (
            CASE WHEN (SELECT TRUE from data_point where datapoint_id = {0})
            THEN (SELECT d.aspect_id from data_point d where datapoint_id = {0})
            ELSE 0::bigint
            END
          ) END
        ) END
        """.format(_id))
    dbConn.close()
    return results