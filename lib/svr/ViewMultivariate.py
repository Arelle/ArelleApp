'''
Created on Jan 5, 2015

@author: Mark V Systems Limited
(c) Copyright 2015 Mark V Systems Limited, All rights reserved.
'''
from XbrlSemanticDB import XbrlSemanticDatabaseConnection

def viewMultivariateRules(request):
    dbConn = XbrlSemanticDatabaseConnection(request)
    results = dbConn.execute("View Multivariate Rules", """
        SELECT fl.sequence, fl.label, fl.name, array_agg(f2u.uname)
        FROM _fsbm_to_ugt f2u, _fsbm_labels fl
        WHERE f2u.cname = fl.name
        GROUP BY fl.sequence, fl.label, fl.name
        ORDER BY fl.sequence
        """)
    dbConn.close()
    return {"rows": [{"id": result[0], 
                      "data": [str(r)
                               for r in result[1:]]}
                     for result in results]}

def selectMultivariateRules(request):
    dbConn = XbrlSemanticDatabaseConnection(request)
    results = dbConn.execute("Select Rules", """
        SELECT fl.sequence
        FROM _fsbm_labels fl
        WHERE fl.name = '{name}'
        LIMIT 1
        """.format(name=dbConn.request.query.name))
    dbConn.close()
    return results

def viewMultivariateFilings(request):
    dbConn = XbrlSemanticDatabaseConnection(request)
    results = dbConn.execute("View Multivariate Filings", """
        SELECT f.filing_id, f.filing_number, e.name, f.form_type, f.accepted_timestamp, f.entry_url, e.standard_industry_code, f.creation_software 
        FROM entity e, filing f, report r 
        WHERE r.filing_id in ({filingIds}) AND f.entity_id = e.entity_id AND f.filing_id = r.filing_id
        """.format(filingIds=dbConn.request.query.filingIds or 0))
    dbConn.close()
    return {"rows": [{"id": result[0], 
                      "data": [str(r)
                               for r in result[1:]]}
                     for result in results]}

def selectMultivariateFilings(request):
    dbConn = XbrlSemanticDatabaseConnection(request)
    if ("selectHtmlUrl" in dbConn.request.query):
        results = dbConn.execute("Select Filing HTML URL", """
            SELECT f.authority_html_url, (e.name || ' - ' || f.filing_number || ' - ' || f.accepted_timestamp)
            FROM filing f, entity e
            WHERE f.filing_id = {filingId} AND e.entity_id = f.entity_id
            LIMIT 1
            """.format(filingId=dbConn.request.query.filingId or 0))
    elif ("selectXbrlUrl" in dbConn.request.query):
        results = dbConn.execute("Select Filing XBRL ENTRY URL", """
            SELECT f.entry_url 
            FROM filing f
            WHERE f.filing_id = {filingId}
            LIMIT 1
            """.format(filingId=dbConn.request.query.filingId or 0))
    else:
        results = dbConn.execute("Select Filings", """
            SELECT {filingId}
            LIMIT 1
            """.format(filingId=dbConn.request.query.filingId or 0))
    dbConn.close()
    return results

def viewMultivariateGrid(request):
    dbConn = XbrlSemanticDatabaseConnection(request)
    variables = dbConn.request.query.variables.split(',')
    if variables:
        if dbConn.request.query.heatMap == "true":
            _colSelects = "".join(""",
                (SELECT array_agg(DISTINCT f2u.uname) 
                FROM _fsbm_to_ugt f2u, aspect a, data_point d
                WHERE d.report_id = r.report_id
                    AND f2u.cname = '{variable}'
                    AND a.aspect_id = d.aspect_id
                    AND a.name = f2u.uname)
                """.format(variable=variable)
                for variable in variables)
        else:
            _colSelects = "".join(""",
                (SELECT SUM(d.effective_value) 
                FROM _fsbm_to_ugt f2u, aspect a, data_point d
                WHERE d.report_id = r.report_id
                    AND d.context_xml_id = default_cntx.context_xml_id
                    AND f2u.cname = '{variable}'
                    AND a.aspect_id = d.aspect_id
                    AND a.name = f2u.uname)
                """.format(variable=variable)
                for variable in variables)
    else:
        _colSelects = ""
        
    results = dbConn.execute("View Multivariate Filings", """
        SELECT f.filing_id, (e.name || ' - ' || f.filing_number || ' - ' || f.accepted_timestamp)
               {colSelects}
        FROM entity e, filing f, report r, data_point default_cntx, aspect aspect_doc_per_end_date
        WHERE r.filing_id in ({filingIds}) AND f.entity_id = e.entity_id AND f.filing_id = r.filing_id
        AND default_cntx.report_id = r.report_id 
        AND aspect_doc_per_end_date.aspect_id = default_cntx.aspect_id 
        AND aspect_doc_per_end_date.name = 'DocumentPeriodEndDate'
        GROUP BY f.filing_id, e.name, r.report_id, default_cntx.context_xml_id   
        """.format(filingIds=dbConn.request.query.filingIds or '0',
                   colSelects=_colSelects))
    dbConn.close()
    return {"rows": [{"id": result[0], 
                      "data": [result[1]] +
                              ["{:,.2f}".format(r) if isinstance(r,(float,int)) else str(r)
                               for r in result[2:]]}
                     for result in results]}

def selectMultivariateGrid(request):
    dbConn = XbrlSemanticDatabaseConnection(request)
    results = dbConn.execute("Select Filings", """
        SELECT {filingId}
        LIMIT 1
        """.format(dbConn.request.query.filingId or 0))
    dbConn.close()
    return results

def viewMultivariateProperties(request):
    dbConn = XbrlSemanticDatabaseConnection(request)
    results = dbConn.execute("Select Filings", """
       WITH default_cntx(context_xml_id) as (
          SELECT d.context_xml_id from entity e, filing f, report r, aspect a, data_point d
          WHERE r.filing_id = '{filingId}' AND f.entity_id = e.entity_id AND f.filing_id = r.filing_id
          AND d.report_id = r.report_id
          AND a.aspect_id = d.aspect_id
          AND a.name = 'DocumentPeriodEndDate'
          LIMIT 1)
       SELECT f2u.uname || '[' || d.context_xml_id || ']', d.effective_value
        FROM entity e, filing f, report r, _fsbm_to_ugt f2u, aspect a, data_point d, default_cntx 
        WHERE r.filing_id = '{filingId}' AND f.entity_id = e.entity_id AND f.filing_id = r.filing_id
        AND d.report_id = r.report_id
        AND d.context_xml_id = default_cntx.context_xml_id
        AND f2u.cname = '{name}'
        AND a.aspect_id = d.aspect_id
        AND a.name = f2u.uname
        ORDER BY a.name, d.context_xml_id
        """.format(filingId=dbConn.request.query.filingId or 0,
                   name=dbConn.request.query.name or ''))
    dbConn.close()
    return {"rows": [{"id": i+1, 
                      "data": [result[0],
                               "{:,.2f}".format(result[1]) 
                               if isinstance(result[1],(float,int)) 
                               else str(result[1])]}
                     for i, result in enumerate(results)]}
