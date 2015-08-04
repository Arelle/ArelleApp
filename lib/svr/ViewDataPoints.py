'''
Created on May 19, 2013

@author: Mark V Systems Limited
(c) Copyright 2013 Mark V Systems Limited, All rights reserved.
'''
from XbrlSemanticDB import XbrlSemanticDatabaseConnection, decompressResults

def viewDataPoints(request):
    dbConn = XbrlSemanticDatabaseConnection(request)
    results = dbConn.execute("View Data Points", """
        {relSetForLabels} -- relationship set for labels
        SELECT d.datapoint_id, lbl.value, d.source_line, d.context_xml_id, u.xml_id, d.effective_value, d.value 
        FROM report r
        JOIN label_relationship_set lrs ON true
        JOIN data_point d ON r.filing_id = {filingId} AND 
            d.document_id = r.report_data_doc_id 
        JOIN relationship lrel ON lrel.relationship_set_id = lrs.relationship_set_id AND lrel.from_id = d.aspect_id
        JOIN resource lbl on lrel.to_id = lbl.resource_id and lbl.role = 'http://www.xbrl.org/2003/role/label'
        LEFT OUTER JOIN unit u ON u.unit_id = d.unit_id
        ORDER BY d.source_line 
        """.format(filingId=dbConn.filingId, 
                   relSetForLabels=dbConn.withAspectLabelRelSetId))
    dbConn.close()
    return {"rows": [{"id": result[0], "data": [result[1], result[2], result[3], result[4],
                                                (result[5] if result[5] is not None else result[6])]}
                     for result in results]}

def selectDataPoints(request):
    dbConn = XbrlSemanticDatabaseConnection(request)
    _id = dbConn.id.rpartition(":")[2]
    results = dbConn.execute("Select Data Points", """
        SELECT
        CASE WHEN (SELECT TRUE FROM data_point d, report r 
                   WHERE aspect_id = {objectId} AND 
                         r.filing_id = {filingId} AND 
                         d.report_id = r.report_id
                   LIMIT 1)
        THEN
          (SELECT d.datapoint_id from data_point d, report r
           WHERE aspect_id = {objectId} AND 
                 r.filing_id = {filingId} AND 
                 d.report_id = r.report_id
           LIMIT 1)
        ELSE (
          CASE WHEN (SELECT TRUE FROM relationship rel, report r, data_point d 
                     WHERE relationship_id = {objectId} AND 
                           rel.to_id = d.aspect_id AND 
                           d.report_id = r.report_id 
                           and r.filing_id = {filingId}
                     LIMIT 1)
          THEN (SELECT d.datapoint_id FROM relationship rel, report r, data_point d 
                WHERE relationship_id = {objectId} AND 
                      rel.to_id = d.aspect_id AND 
                      d.report_id = r.report_id and 
                      r.filing_id = {filingId}
                LIMIT 1)
          ELSE (
            CASE WHEN (SELECT TRUE from data_point where datapoint_id = {objectId})
            THEN {objectId}::bigint
            ELSE 0::bigint
            END
          ) END
        ) END
        """.format(objectId=_id, filingId=dbConn.filingId))
    dbConn.close()
    return results