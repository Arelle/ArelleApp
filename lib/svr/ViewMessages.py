'''
Created on May 19, 2013

@author: Mark V Systems Limited
(c) Copyright 2013 Mark V Systems Limited, All rights reserved.
'''
from XbrlSemanticDB import XbrlSemanticDatabaseConnection, decompressResults

def viewMessages(request):
    dbConn = XbrlSemanticDatabaseConnection(request)
    results = dbConn.execute("View Filings", """
        SELECT m.message_id, m.sequence_in_report, m.message_code, m.message_level, m.value
        FROM report r, message m
        WHERE r.filing_id = {filingId} AND m.report_id = r.report_id
        ORDER BY m.sequence_in_report 
        """.format(filingId=dbConn.filingId))
    dbConn.close()
    return {"rows": [{"id": result[0], "data": result[1:]}
                     for result in results]}
