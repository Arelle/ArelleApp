'''
Created on May 19, 2013

@author: Mark V Systems Limited
(c) Copyright 2013 Mark V Systems Limited, All rights reserved.
'''
from XbrlSemanticDB import XbrlSemanticDatabaseConnection

def viewFilings(request):
    dbConn = XbrlSemanticDatabaseConnection(request)
    results = dbConn.execute("View Filings", """
        SELECT f.filing_id, f.filing_number, e.name, f.accepted_timestamp, f.entry_url, f.creation_software,
        'XML: ' || (SELECT count(*) FROM message m WHERE m.report_id = r.report_id AND m.message_code LIKE 'xml%') ||
        ', XBRL: ' || (SELECT count(*) FROM message m WHERE m.report_id = r.report_id AND m.message_code LIKE 'xbrl%') ||
        ', EFM: ' || (SELECT count(*) FROM message m WHERE m.report_id = r.report_id AND m.message_code LIKE 'EFM%') ||
        ', BPG: ' || (SELECT count(*) FROM message m WHERE m.report_id = r.report_id AND m.message_code LIKE 'US-BPG%') 
        FROM entity e, filing f, report r 
        WHERE f.entity_id = e.entity_id AND f.filing_id = r.filing_id
        LIMIT 100
        """)
    dbConn.close()
    return {"rows": [{"id": result[0], "data": result[1:]}
                     for result in results]}
