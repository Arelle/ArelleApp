'''
Created on May 19, 2013

@author: Mark V Systems Limited
(c) Copyright 2013 Mark V Systems Limited, All rights reserved.
'''
from XbrlSemanticDB import XbrlSemanticDatabaseConnection, decompressResults

def viewProperties(request):
    dbConn = XbrlSemanticDatabaseConnection(request)
    _id = dbConn.id.rpartition(":")[2]
    _id_parent = dbConn.id_parent.rpartition(":")[2]
    results = dbConn.execute("View Properties", """
        SELECT
        CASE WHEN (SELECT TRUE FROM aspect WHERE aspect_id = {objectId})
        THEN (
          SELECT (('aspect name', a.name),
                  ('period type', a.period_type),
                  ('balance', a.balance),
                  ('data type', dt.name),
                  ('base type', a.base_type)) AS properties
          FROM aspect a, data_type dt 
          WHERE aspect_id = {objectId} AND dt.data_type_id = a.datatype_id
        ) ELSE (
          CASE WHEN (SELECT TRUE from relationship where relationship_id = {objectId})
          THEN (
            SELECT (('aspect name', a.name),
                    ('period type', a.period_type),
                    ('balance', a.balance),
                    ('data type', dt.name),
                    ('base type', a.base_type),
                    ('linkrole', rs.link_role),
                    ('definition', rt.definition),
                    ('arcrole', rs.arc_role),
                    ('preferred lbl', r.preferred_label_role)) AS properties
            FROM relationship_set rs, role_type rt, relationship r, aspect a, data_type dt 
            WHERE rs.relationship_set_id = {parentId} AND
                  r.relationship_id = {objectId} AND
                  rt.document_id = rs.document_id AND rs.link_role = rt.role_uri AND
                  a.aspect_id = r.to_id AND dt.data_type_id = a.datatype_id
          ) ELSE (
            CASE WHEN (SELECT TRUE from data_point where datapoint_id = {objectId})
            THEN (
               SELECT (('name', a.name),
                       ('source line', d.source_line),
                       ('entity', e.identifier),
                       CASE WHEN p.is_instant
                         THEN ('', '')
                         ELSE ('start date', p.start_date)
                         END,
                       CASE WHEN p.is_instant
                         THEN ('instant', p.end_date)
                         ELSE ('end date', p.end_date)
                         END,
                       (SELECT ('dimensions',count(*))
                         FROM aspect_value_selection avs
                         WHERE avs.aspect_value_selection_id = d.aspect_value_selection_id),
                       CASE WHEN d.is_nil
                         THEN ('xsi:nil','true')
                         ELSE ('value', d.value)
                         END
                       ) AS properties
               FROM data_point d, aspect a, entity_identifier e, period p
               WHERE d.datapoint_id = {objectId} AND
                     d.aspect_id = a.aspect_id AND
                     p.period_id = d.period_id AND
                     e.entity_identifier_id = d.entity_identifier_id
            ) ELSE (
               SELECT (('','')) AS properties
            ) END
          ) END
        ) END
        """.format(objectId=_id, parentId=_id_parent))
    try:
        resultList = results[0][0]
        props = []
        if resultList and resultList.startswith('(') and resultList.endswith(')'):
            strLists = resultList[1:-1].split(')","(')
            for n, strList in enumerate(strLists):
                if strList.startswith('"('):
                    strList = strList[2:]
                if strList.endswith(')"'):
                    strList = strList[:-2]
                strList = strList.replace('""', '"')
                if '","' in strList:
                    k, _s, v = strList.partition('","')
                elif '",' in strList:
                    k, _s, v = strList.partition('",')
                else:
                    k, _s, v = strList.partition(',')
                if k.startswith('"'):
                    k = k[1:]
                if v.endswith('"'):
                    v = v[:-1]
                if k: # skip empty list entries (like start date for an instant)
                    _row = {"id": n+1, "data": [k, v]}
                    props.append(_row)
                    if k == 'dimensions' and v > "0":
                        _dimRows = []
                        _row["rows"] = _dimRows
                        _dims = dbConn.execute("View Dimension Properties", """
                            SELECT avs.aspect_value_selection_id, dim.aspect_id, dim.name, mem.name
                            FROM data_point d, aspect_value_selection avs,
                                   aspect dim, aspect mem
                            WHERE d.datapoint_id = {objectId} AND
                                  avs.aspect_value_selection_id = d.aspect_value_selection_id AND
                                  dim.aspect_id = avs.aspect_id AND
                                  mem.aspect_id = avs.aspect_value_id
                            """.format(objectId=_id))
                        for _avsId, _dimId, _dimName, _memName in _dims:
                            _dimRows.append({"id":"{}_{}".format(_avsId, _dimId), 
                                             "data":[_dimName, _memName]})
        dbConn.close()
        return {"rows": props}
    except Exception as ex:
        dbConn.close()
        return None
