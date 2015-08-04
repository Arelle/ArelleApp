'''
Created on Jan 4, 2015

@author: Mark V Systems Limited
(c) Copyright 2015 Mark V Systems Limited, All rights reserved.
'''
from XbrlSemanticDB import XbrlSemanticDatabaseConnection

def viewDocuments(request):
    dbConn = XbrlSemanticDatabaseConnection(request)
    where = ""
    _url = dbConn.documentUrl
    _type = dbConn.documentType
    _namespace = dbConn.namespace
    if _url:
        if _url.startswith('~'):
            where += " d.document_url ~* '{}'".format(_url[1:])
        else:
            where += " d.document_url like '{}'".format(_url.replace('*','%').replace('?','_'))
    if _type:
        if where:
            where += " AND "
        if _type.startswith('~'):
            where += " d.document_type ~* '{}'".format(_type[1:])
        else:
            where += " d.document_type ilike '{}'".format(_type.replace('*','%').replace('?','_'))
    if _namespace:
        if where:
            where += " AND "
        if _namespace.startswith('~'):
            where += " d.namespace ~* '{}'".format(_namespace[1:])
        else:
            where += " d.namespace like '{}'".format(_namespace.replace('*','%').replace('?','_'))
    results = dbConn.execute("View Filings", """
        SELECT d.document_id, d.document_url, d.document_type, d.namespace
        FROM document d
        WHERE {}true
        LIMIT 100
        """.format(where + " AND " if where else ""))
    dbConn.close()
    return {"rows": [{"id": result[0], "data": result[1:]}
                     for result in results]}

            