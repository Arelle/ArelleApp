'''
Created on May 19, 2013

@author: Mark V Systems Limited
(c) Copyright 2013 Mark V Systems Limited, All rights reserved.
'''
from XbrlSemanticDB import XbrlSemanticDatabaseConnection

def viewAspects(request):
    dbConn = XbrlSemanticDatabaseConnection(request)
    results = dbConn.execute("View Aspects", """
        SELECT a.aspect_id, '', a.name, a.period_type, a.balance, dt.name, a.base_type
        FROM report r, aspect a, data_type dt
        WHERE r.filing_id = {} AND 
           (a.document_id = r.report_schema_doc_id OR
            a.document_id = r.standard_schema_doc_id) AND
           dt.data_type_id = a.datatype_id
        ORDER BY a.name 
        """.format(dbConn.filingId))
    dbConn.close()
    return {"rows": [{"id": result[0], "data": result[1:]}
                     for result in results]}

def selectAspects(request):
    dbConn = XbrlSemanticDatabaseConnection(request)
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
        """.format(dbConn.id))
    dbConn.close()
    return results