'''
Created on May 19, 2013

@author: Mark V Systems Limited
(c) Copyright 2013 Mark V Systems Limited, All rights reserved.
'''
from XbrlSemanticDB import XbrlSemanticDatabaseConnection
import re

accessionPattern = re.compile(r"[\d]{10}-[\d]{2}-[\d]{6}")
datePattern = re.compile(r"20[\d]{2}")
formPattern = re.compile(r"((8|10)-?([kKqQ](/?[aA])?))|POS-?AM|S-?\d{1,2}|((20|40)-?([fF](/?[aA])?))")
form1digitkNoDash = re.compile(r"8([kKqQ](/?[aA])?)|S-?\d")
form2digitkNoDash = re.compile(r"(10|20|40)([kKqQfF](/?[aA])?)|S-?1\d")
formAmdmtnoSlash = re.compile(r"(.*[^/])([aA].*)")
namePattern = re.compile(r"[\w?*]+[\w\d_*?-]*")
sicPattern = re.compile(r"^sic[\d]{1,4}$")
cikPattern = re.compile(r"^cik[\d]{1,10}$")

def viewFilings(request):
    dbConn = XbrlSemanticDatabaseConnection(request)
    where = ""
    _filing = dbConn.request.query.filing
    _name = dbConn.request.query.name
    _date = dbConn.request.query.date
    _sic = dbConn.request.query.sic
    _formType = dbConn.request.query.formtype
    _ticker = dbConn.request.query.ticker
    _search = dbConn.request.query.search
    hasTicker = "ticker" in dbConn.request.query # specifies whether to return ticker & creation software
    if _filing and _filing != "undefined":
        if _filing.startswith('~'):
            where += " f.filing_number ~* '{}'".format(_filing[1:])
        else:
            if not _filing.endswith("*"): _filing += "*"
            where += " f.filing_number like '{}'".format(_filing.replace('*','%').replace('?','_'))
    if _name and _name != "undefined":
        if where:
            where += " AND "
        if _name.startswith('~'):
            where += " e.name ~* '{}'".format(_name[1:])
        else:
            if not _name.endswith("*"): _name += "*"
            where += " e.name ilike '{}'".format(_name.replace('*','%').replace('?','_'))
    if _date and _date != "undefined":
        if where:
            where += " AND "
        if _date.startswith('~'):
            where += " f.filing_date::varchar ~* '{}'".format(_date[1:])
        else:
            if not _date.endswith("*"): _date += "*"
            where += " f.filing_date::varchar like '{}'".format(_date.replace('*','%').replace('?','_'))
    if _sic and _sic != "undefined":
        if where:
            where += " AND "
        if _sic.startswith('~'):
            where += " e.standard_industry_code::varchar ~* '{}'".format(_sic[1:])
        elif _sic.isnumeric():
            if not _sic.endswith("*"): _sic += "*"
            where += " e.standard_industry_code = {}".format(_sic)
        else:
            where += " e.standard_industry_code::varchar like '{}'".format(_sic.replace('*','%').replace('?','_'))
    if _formType and _formType != "undefined":
        if where:
            where += " AND "
        if _formType.startswith('~'):
            where += " f.form_type ~* '{}'".format(_formType[1:])
        else:
            where += " f.form_type ilike '{}'".format(_formType.replace('*','%').replace('?','_'))
    if _ticker and _ticker != "undefined":
        if where:
            where += " AND "
        if _formType.startswith('~'):
            where += " e.trading_symbol ~* '{}'".format(_ticker[1:])
        else:
            where += " e.trading_symbol ilike '{}'".format(_ticker.replace('*','%').replace('?','_'))
    if _search and _search != "undefined":
        _accessions = []
        _dates = []
        _searchWords = _search.split()
        _forms = []
        _sicNbrs = []
        _cikNbrs = []
        _names = []
        _newName = True
        for _word in _searchWords:
            if accessionPattern.match(_word):
                _accessions.append(_word)
            elif datePattern.match(_word):
                _dates.append(_word)
            elif formPattern.match(_word):
                if _word == "POSAM": _word = "POS-AM"
                elif _word == "S1": _word = "S-1"
                elif form1digitkNoDash.match(_word): _word = _word[0] + '-' + _word[1:]
                elif form2digitkNoDash.match(_word): _word = _word[0:2] + '-' + _word[2:]
                if formAmdmtnoSlash.match(_word): 
                    _groups = formAmdmtnoSlash.match(_word).groups()
                    _word = _groups[0] + "/" + _groups[1]
                _forms.append(_word)
            elif sicPattern.match(_word):
                _sicNbrs.append(_word[3:])
            elif cikPattern.match(_word):
                _cikNbrs.append("'{:0>10}'".format(_word[3:])) # pad on left with zeros
            elif _word == "OR":
                _newName = True
            elif namePattern.match(_word):
                if _newName:
                    _names.append(_word)
                    _newName = False
                else:
                    _names[-1] += " " + _word
        where = ""
        if _accessions:
            where = "f.filing_number in ({})".format(
                    ", ".join("'{}'".format(a) for a in _accessions))
        if _dates:
            if where: where += " AND "
            where += "({})".format(
                    " OR ".join("f.filing_date::varchar like '{}%'".format(d) for d in _dates))
        if _forms:
            if where: where += " AND "
            where += "f.form_type in ({})".format(
                    ", ".join("'{}'".format(f.upper()) for f in _forms))
        if _sicNbrs:
            if where: where += " AND "
            where += "e.standard_industry_code in ({})".format(
                    ", ".join(_sicNbrs))
        if _cikNbrs:
            if where: where += " AND "
            where += "e.reference_number in ({})".format(
                    ", ".join(_cikNbrs))
        if _names:
            if where: where += " AND "
            where += "({})".format(
                     " OR ".join("name ilike '{}%'".format(n.replace("*","%").replace("?","_"))
                                 for n in _names))
        
    results = dbConn.execute("View Filings", """
        SELECT f.filing_id, f.filing_number, e.name, {1}f.form_type, f.accepted_timestamp, f.entry_url, e.standard_industry_code{2}
        FROM entity e, filing f, report r 
        WHERE {0}f.entity_id = e.entity_id AND f.filing_id = r.filing_id
        LIMIT 100
        """.format(where + " AND " if where else "",
                    "e.trading_symbol, " if hasTicker else "",
                    """
                    , f.creation_software,
                    'XML: ' || (SELECT count(*) FROM message m WHERE m.report_id = r.report_id AND m.message_code LIKE 'xml%') ||
                    ', XBRL: ' || (SELECT count(*) FROM message m WHERE m.report_id = r.report_id AND m.message_code LIKE 'xbrl%') ||
                    ', EFM: ' || (SELECT count(*) FROM message m WHERE m.report_id = r.report_id AND m.message_code LIKE 'EFM%') ||
                    ', BPG: ' || (SELECT count(*) FROM message m WHERE m.report_id = r.report_id AND m.message_code LIKE 'US-BPG%') 
                    """ if hasTicker else ""
                    ))
    dbConn.close()
    _rows = []
    for resultRow in results:
        if not hasTicker:
            resultRow[4] = str(resultRow[4])[:10]
        _rows.append(resultRow)
            
    return {"rows": [{"id": result[0], "data": [r if r is not None else '' 
                                                for r in result[1:]]}
                     for result in _rows]}
    
def getPrimaryDocument(request):
    dbConn = XbrlSemanticDatabaseConnection(request)
    results = dbConn.execute("View Filings", """
        SELECT f.authority_html_url
        FROM filing f 
        WHERE f.filing_id = {}
        LIMIT 1
        """.format(dbConn.filingId))
    docHtml = ""
    if results:
        import urllib.request
        with urllib.request.urlopen(results[0][0]) as response:
            docHtml = response.read().decode('utf-8')
    return docHtml