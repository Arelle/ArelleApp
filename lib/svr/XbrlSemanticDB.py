'''
Created on May 19, 2013

@author: Mark V Systems Limited
(c) Copyright 2013 Mark V Systems Limited, All rights reserved.
'''
import json, sys, urllib, io, socket, zlib, re
from urllib.parse import unquote
from base64 import b64decode
from urllib import request as proxyhandlers
from urllib.error import URLError, HTTPError
from XbrlStandardRoles import conceptLabel

def noop(*args, **kwargs): return 
class NoopException(Exception):
    pass

try:
    import pg8000
    hasPostgres = True
    pgConnect = pg8000.connect
    pgProgrammingError = pg8000.ProgrammingError
    pgInterfaceError = pg8000.InterfaceError
except ImportError:
    hasPostgres = False
    pgConnect = noop
    pgProgrammingError = pgInterfaceError = NoopException

#TRACEGREMLINFILE = None
#TRACEGREMLINFILE = r"c:\temp\appsvrtrace.log"  # uncomment to trace SQL on connection (very big file!!!)
TRACESQLFILE = None
#TRACESQLFILE = "/tmp/sqltrace.log"
#TRACESQLFILE = r"c:\temp\sqltrace.log"  # uncomment to trace SQL on connection (very big file!!!)
#TRACESQLFILE = "/Users/hermf/temp/sqltrace.log"  # uncomment to trace SQL on connection (very big file!!!)

HTTPHEADERS = {'User-agent':   'Arelle/1.0',
               'Accept':       'application/json',
               'Content-Type': 'application/json'}

normalizeSpacesPattern = re.compile(r"[ ]{2,}")

def testConnection(request):
    # determine if postgres port
    dbConn = XbrlSemanticDatabaseConnection(request)
    # results = dbConn.dbFeatures()
    results = True
    dbConn.close()
    return results

class XbrlSemanticDatabaseConnection:
    def __init__(self, request):
        self.request = request
        connection = unquote(request.get_cookie("rlConnection",default=""))
        host, port, user, password, database, timeout = b64decode(connection.encode('utf-8')).decode('utf-8').split("|")
        if timeout:
            try:
                timeout = int(timeout)
            except Exception:
                timeout = None
        if TRACESQLFILE:
            with io.open(TRACESQLFILE, "a", encoding='utf-8') as fh:
                fh.write("\n\n>>> connecting as {} db {}\n"
                         .format(user, database))
        try:
            self.conn = pgConnect(user=user, password=password, host=host, 
                                  port=int(port or 5432), 
                                  database=database, 
                                  socket_timeout=timeout or 60)
        except Exception as ex:
            if TRACESQLFILE:
                with io.open(TRACESQLFILE, "a", encoding='utf-8') as fh:
                    fh.write("\n\n>>> connection exception {}\n", format(ex))
            raise
        self.cursor = self.conn.cursor()
        if TRACESQLFILE:
            with io.open(TRACESQLFILE, "a", encoding='utf-8') as fh:
                fh.write("\n\n>>> connected as {} db {}\n"
                         .format(user, database))
        
        
    @property
    def filingId(self):
        return self.request.query.filingId

    @property
    def documentId(self):
        return self.request.query.documentId

    @property
    def documentUrl(self):
        return self.request.query.documentUrl

    @property
    def id(self):
        _id = self.request.query.id.strip() # might be mmm_nnn if so return just nnn
        if '_' in _id:
            _id = _id.rpartition('_')[2]
        return _id

    @property
    def id_parent(self):
        _id = self.request.query.id.strip() # might be mmm_nnn if so return just mmm
        return _id.partition('_')[0]

    @property
    def arcrole(self):
        return self.request.query.arcrole

    @property
    def filing(self):
        return self.request.query.filing

    @property
    def name(self):
        return self.request.query.name

    @property
    def date(self):
        return self.request.query.date

    @property
    def documentUrl(self):
        return self.request.query.documentUrl

    @property
    def documentType(self):
        return self.request.query.documentType

    @property
    def namespace(self):
        return self.request.query.namespace

    @property
    def sic(self):
        return self.request.query.sic

    def close(self, rollback=False):
        try:
            self.cursor.close()
            self.conn.close()
            self.__dict__.clear() # dereference everything
        except Exception as ex:
            self.__dict__.clear() # dereference everything
            raise
        
    def execute(self, activity, script, params=None, fetch=True):
        try:
            if isinstance(params, dict):
                self.cursor.execute(script, **params)
            elif isinstance(params, (tuple,list)):
                self.cursor.execute(script, params)
            else:
                self.cursor.execute(script.replace('%', '%%'))
        except (pgProgrammingError,
                socket.timeout) as ex:  # something wrong with SQL
            if TRACESQLFILE:
                with io.open(TRACESQLFILE, "a", encoding='utf-8') as fh:
                    fh.write("\n\n>>> EXCEPTION {} error {}\n sql {}\n"
                             .format(activity, str(ex), script))
            raise

        if fetch:
            result = self.cursor.fetchall()
            if TRACESQLFILE:
                with io.open(TRACESQLFILE, "a", encoding='utf-8') as fh:
                    fh.write("\n\n>>> {0} result row count {1}\n{2}\n"
                             .format(activity, len(result), '\n'.join(str(r) for r in result)))
        else:
            #if cursor.rowcount > 0:
            #    cursor.fetchall()  # must get anyway
            result = None
        return result
            
    @property
    def withAspectLabelRelSetId(self):
        if self.filingId:
            return """
                WITH label_relationship_set(relationship_set_id) AS (
                    SELECT rs.relationship_set_id
                    FROM relationship_set rs, report r
                    WHERE r.filing_id = {filingId}
                    AND rs.document_id = r.report_schema_doc_id
                    AND rs.arc_role = '{arcrole}'
                )""".format(filingId=self.filingId, arcrole=conceptLabel)
        elif self.documentId:
            return """
                WITH label_relationship_set(relationship_set_id) AS (
                    SELECT rs.relationship_set_id
                    FROM relationship_set rs
                    WHERE rs.document_id = {documentId}
                    AND rs.arc_role = '{arcrole}'
                )""".format(documentId=self.documentId, arcrole=conceptLabel)
        else:
            return ""

def decompressResults(results):
    return results
