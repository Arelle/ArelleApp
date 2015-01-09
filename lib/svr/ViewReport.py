'''
Created on May 19, 2013

@author: Mark V Systems Limited
(c) Copyright 2013 Mark V Systems Limited, All rights reserved.
'''
from XbrlSemanticDB import XbrlSemanticDatabaseConnection
import os

def viewDTS(request):
    dbConn = XbrlSemanticDatabaseConnection(request)
    results = dbConn.execute("View Report", """
        WITH RECURSIVE doc_graph(parent_doc_id, child_doc_id, depth, path, cycle) as (
           SELECT 0::bigint, r.report_data_doc_id, 1, ARRAY[r.report_data_doc_id], false
           FROM report r
           WHERE r.filing_id = {filingId}
        UNION ALL
           SELECT rd.object_id, rd.document_id,
                  dg.depth + 1, 
                  path || rd.document_id,
                  rd.document_id = ANY(path)
           FROM referenced_documents rd, doc_graph dg
           WHERE rd.object_id = dg.doc_id AND NOT cycle
        )
        SELECT dg.parent_doc_id, dg.child_doc_id, d.document_url, d.document_type FROM doc_graph dg
        JOIN document d on dg.child_doc_id = d.document_id 
        """.format(filingId=dbConn.filingId))
    dbConn.close()
    docTree = {}
    parentSubtree = {0: docTree}
    # results are in dependeny order due to recursive descent in doc_graph
    for result in results:
        parentId, childId, url, type = result
        if parentId in parentSubtree:
            parentRows = parentSubtree[parentId]
            row = {"id": childId, "data": [os.path.basename(url)]}
            parentSubtree[childId] = row
            if "rows" not in parentRows:
                parentRows["rows"] = []
            parentRows["rows"].append(row)
    return docTree