'''
Created on May 19, 2013

@author: Mark V Systems Limited
(c) Copyright 2013 Mark V Systems Limited, All rights reserved.
'''
from XbrlSemanticDB import XbrlSemanticDatabaseConnection, decompressResults
from urllib import request as httpReq
import os, re, json

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

LOGLINEPATTERN = re.compile(r"[\d:, -]{23} (\[.+\].*)")
def viewDQCmessages(request):
    dbConn = XbrlSemanticDatabaseConnection(request)
    results = dbConn.execute("View Filings", """
        SELECT f.entry_url, f.filing_number
        FROM filing f
        WHERE f.filing_id = {filingId}
        """.format(filingId=dbConn.filingId))
    _filingUrl = results[0][0]
    _filingNbr = results[0][1]
    # form request zip file
    _filingZip = "{}/{}-xbrl.zip/{}".format(os.path.dirname(_filingUrl),
                                            _filingNbr,
                                            os.path.basename(_filingUrl))
    _request = httpReq.Request("http://rltest.markv.com/cgi-bin/arelle/arelleCmdLine/rest/xbrl/validation"
                               "?file={}&media=json&plugins=validate/DQC|logging/dqcParameters.py"
                               "&disclosureSystem=efm-pragmatic-all-years"
                               .format(_filingZip))
    _response = httpReq.urlopen(_request)
    _result = []
    '''
    _msg = []
    for l in _response.read().decode().splitlines():
        if l or len(_result) > 0:
            m = LOGLINEPATTERN.match(l)
            if m or len(_msg) == 0: # new message
                if (_msg):
                    _result.append(("_{}".format(len(_result)+1), len(_result)+1, '<br>'.join(_msg)))
                _msg = [m.group(1)]
            elif len(_msg) > 0:
                _msg.append(l)
    if (_msg):
        _result.append(("_{}".format(len(_result)+1), len(_result)+1, '<br>'.join(_msg)))
    _msg = [m.group(1)]
    '''
    _msgNum = 0
    _dpElts = set()
    for _msg in json.loads(_response.read().decode()).get("log",[]):
        if _msg['code'] != "info":
            _eltId = _msg['refs'][0]['href'].rpartition('#')[2]
            if _eltId.startswith("element("):
                _dpElts.add(_eltId[8:-1])
                _eltId = _eltId[8:-1]
            elif not all(c.isalnum() for c in _eltId):
                _msgNum += 1
                _eltId = "dpXid.{}".format(_msgNum)
            _txt = _msg['message']['text']
            m = LOGLINEPATTERN.match(_txt)
            if m:
                _txt = m.group(1)
            _result.append((_eltId, len(_result) + 1,
                            _txt.replace("\n","<br>")))
    _response.close()
    # get datapoint object numbers
    dpEltIds = {}
    if _dpElts:
        results = dbConn.execute("View DataPoints", """
            SELECT d.xml_child_seq, d.datapoint_id
            FROM report r, data_point d
            WHERE r.filing_id = {filingId} AND d.report_id = r.report_id AND d.xml_child_seq in ({childIds})
            """.format(filingId=dbConn.filingId,
                       childIds=",".join("'{}'".format(i) for i in _dpElts)))
        dpEltIds = dict((x,i) for x,i in results)
    if not _result:
        _result.append(("", 1, "(no errors)"))
    dbConn.close()
    return {"rows": [{"id": "{}:{}".format(_seq, dpEltIds.get(id,0)), 
                      "data": [_seq, _row]}
                     for id, _seq, _row in _result]}
