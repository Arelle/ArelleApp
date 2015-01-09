'''
Created on May 19, 2013

@author: Mark V Systems Limited
(c) Copyright 2013 Mark V Systems Limited, All rights reserved.
'''
from XbrlSemanticDB import XbrlSemanticDatabaseConnection

def viewFilings(request):
    dbConn = XbrlSemanticDatabaseConnection(request)
    where = ""
    _filing = dbConn.filing
    _name = dbConn.name
    _date = dbConn.date
    _sic = dbConn.sic
    if _filing:
        if _filing.startswith('~'):
            where += " f.filing_number ~* '{}'".format(_filing[1:])
        else:
            where += " f.filing_number like '{}'".format(_filing.replace('*','%').replace('?','_'))
    if _name:
        if where:
            where += " AND "
        if _name.startswith('~'):
            where += " e.name ~* '{}'".format(_name[1:])
        else:
            where += " e.name ilike '{}'".format(_name.replace('*','%').replace('?','_'))
    if _date:
        if where:
            where += " AND "
        if _date.startswith('~'):
            where += " f.filing_date::varchar ~* '{}'".format(_date[1:])
        else:
            where += " f.filing_date::varchar like '{}'".format(_date.replace('*','%').replace('?','_'))
    if _sic:
        if where:
            where += " AND "
        if _sic.startswith('~'):
            where += " e.standard_industry_code::varchar ~* '{}'".format(_sic[1:])
        elif _sic.isnumeric():
            where += " e.standard_industry_code = {}".format(_sic)
        else:
            where += " e.standard_industry_code::varchar like '{}'".format(_sic.replace('*','%').replace('?','_'))
    results = dbConn.execute("View Filings", """
        SELECT f.filing_id, f.filing_number, e.name, f.accepted_timestamp, f.entry_url, e.standard_industry_code, f.creation_software,
        'XML: ' || (SELECT count(*) FROM message m WHERE m.report_id = r.report_id AND m.message_code LIKE 'xml%') ||
        ', XBRL: ' || (SELECT count(*) FROM message m WHERE m.report_id = r.report_id AND m.message_code LIKE 'xbrl%') ||
        ', EFM: ' || (SELECT count(*) FROM message m WHERE m.report_id = r.report_id AND m.message_code LIKE 'EFM%') ||
        ', BPG: ' || (SELECT count(*) FROM message m WHERE m.report_id = r.report_id AND m.message_code LIKE 'US-BPG%') 
        FROM entity e, filing f, report r 
        WHERE {}f.entity_id = e.entity_id AND f.filing_id = r.filing_id
        LIMIT 100
        """.format(where + " AND " if where else ""))
    dbConn.close()
    return {"rows": [{"id": result[0], "data": result[1:]}
                     for result in results]}
