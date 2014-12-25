'''
Created on May 19, 2013

@author: Mark V Systems Limited
(c) Copyright 2013 Mark V Systems Limited, All rights reserved.
'''
from XbrlSemanticDB import XbrlSemanticDatabaseConnection
import os

def viewRelationships(request):
    dbConn = XbrlSemanticDatabaseConnection(request)
    # tree roots before tree descendants of roots
    results = dbConn.execute("View Report", """
        -- get roots
        SELECT rs.relationship_set_id, rt.definition, rel.relationship_id, rel.tree_sequence, 0 AS tree_depth, a.aspect_id, a.name
        FROM report r, role_type rt, relationship_set rs, relationship rel, aspect a
        WHERE r.filing_id = {0}
        AND rt.document_id = r.report_schema_doc_id
        AND rs.document_id = r.report_schema_doc_id
        AND rs.link_role = rt.role_uri
        AND rs.arc_role = '{1}'
        AND rel.relationship_set_id = rs.relationship_set_id 
        AND a.aspect_id = rel.from_id AND rel.tree_sequence = 1
        UNION -- get descendants of root
        SELECT rs.relationship_set_id, rt.definition, rel.relationship_id, rel.tree_sequence, rel.tree_depth, a.aspect_id, a.name
        FROM report r, role_type rt, relationship_set rs, relationship rel, aspect a
        WHERE r.filing_id = {0}
        AND rt.document_id = r.report_schema_doc_id
        AND rs.document_id = r.report_schema_doc_id
        AND rs.link_role = rt.role_uri
        AND rs.arc_role = '{1}'
        AND rel.relationship_set_id = rs.relationship_set_id 
        AND a.aspect_id = rel.to_id
        -- order by link role definition, sequence, and depth
        ORDER BY definition, tree_sequence, tree_depth
        """.format(dbConn.filingId, dbConn.arcrole))
    dbConn.close()
    docTree = {"rows": []}
    parentSubtree = {}
    prevRelSetId = None
    # results are in dependeny order due to recursive descent in doc_graph
    for result in results:
        relSetId, definition, relId, _seq, depth, aspectId, name = result
        if relSetId != prevRelSetId:
            prevRelSetId = relSetId
            parentSubtree.clear()
            # add link role
            rsRow = {"id": str(relSetId), "data": [definition], "rows": []}
            parentSubtree[-1] = rsRow # link role row
            docTree["rows"].append(rsRow)
        _parentDepth = depth - 1
        if _parentDepth in parentSubtree:
            _parentRow = parentSubtree[_parentDepth]
            if "rows" not in _parentRow:
                _parentRow["rows"] = []
            _rows = _parentRow["rows"]
            _row = {"id": "{}_{}".format(relSetId, aspectId if depth == 0 else relId),
                    "data": [name]}
            _rows.append(_row)
            parentSubtree[depth] = _row
    return docTree

def selectRelationships(request):
    return 0