'''
Created on May 16, 2013

This module is Arelle's controller for app server (web service and ajax operation)

@author: Mark V Systems Limited
(c) Copyright 2013 Mark V Systems Limited, All rights reserved.
'''
import time, datetime, os, shlex, sys, traceback, threading, json
from datetime import datetime
from optparse import OptionParser, SUPPRESS_HELP
from webserver.bottle import route, get, post, request, response, run, static_file
import Version
import logging
libDir = None
cliDir = None
imagesDir = None
uiDir = None
hasFileSystem = True
isGAE = False
isCGI = False
_os_pid = os.getpid()
__version__ = "1.0.0"

def main():
    """Main program to initiate application from command line or as a separate process (e.g, java Runtime.getRuntime().exec).  May perform
    a command line request, or initiate a web server on specified local port.
       
       :param argv: Command line arguments.  (Currently supported arguments can be displayed by the parameter *--help*.)
       :type message: [str]
       """
    envArgs = os.getenv(u"ARELLE_ARGS")
    if envArgs:
        args = shlex.split(envArgs)
    else:
        args = None # defaults to sys.argv[1:]
        
    global libDir, cliDir, imagesDir, uiDir, hasFileSystem, isGAE, isCGI

    libDir = None
    serverSoftware = os.getenv("SERVER_SOFTWARE", "")
    if serverSoftware.startswith("Google App Engine/") or serverSoftware.startswith("Development/"):
        hasFileSystem = False # no file system, userAppDir does not exist
        isGAE = True
    else:
        gatewayInterface = os.getenv("GATEWAY_INTERFACE", "")
        if gatewayInterface.startswith("CGI/"):
            isCGI = True
            libDir = os.path.join(os.path.dirname(sys.argv[0]), u'lib')

    if not libDir:
        libDir = os.path.dirname(os.path.dirname(__file__))
    cliDir = os.path.join(libDir, u'cli')
    imagesDir = os.path.join(cliDir, u"images")
    uiDir = os.path.join(libDir, u"UI")
    
    usage = u"usage: %prog [options]"
    
    parser = OptionParser(usage, version="Arelle(r) {0}".format(Version.version))
    parser.add_option("--logFile", action="store", dest="logFile",
                      help="Write log messages into file, otherwise they go to standard output.  " 
                           "If file ends in .xml it is xml-formatted, otherwise it is text. ")
    parser.add_option("--logfile", action="store", dest="logFile", help=SUPPRESS_HELP)
    parser.add_option("--logFormat", action="store", dest="logFormat",
                      help="Logging format for messages capture, otherwise default is \"[%(messageCode)s] %(message)s - %(file)s\".")
    parser.add_option("--logformat", action="store", dest="logFormat", help=SUPPRESS_HELP)
    parser.add_option("--logLevel", action="store", dest="logLevel",
                      help="Minimum level for messages capture, otherwise the message is ignored.  " 
                           "Current order of levels are debug, info, info-semantic, warning, warning-semantic, warning, assertion-satisfied, inconsistency, error-semantic, assertion-not-satisfied, and error. ")
    parser.add_option("--loglevel", action="store", dest="logLevel", help=SUPPRESS_HELP)
    parser.add_option("--logLevelFilter", action="store", dest="logLevelFilter",
                      help="Regular expression filter for logLevel.  " 
                           "(E.g., to not match *-semantic levels, logLevelFilter=(?!^.*-semantic$)(.+). ")
    parser.add_option("--loglevelfilter", action="store", dest="logLevelFilter", help=SUPPRESS_HELP)
    parser.add_option("--logCodeFilter", action="store", dest="logCodeFilter",
                      help="Regular expression filter for log message code.")
    parser.add_option("--logcodefilter", action="store", dest="logCodeFilter", help=SUPPRESS_HELP)
    parser.add_option("--webserver", action="store", dest="webserver",
                      help="start web server on host:port[:server] for REST and web access, e.g., --webserver locahost:8080, "
                           "or specify nondefault a server name, such as cherrypy, --webserver locahost:8080:cherrypy")
    parser.add_option("-a", "--about",
                      action="store_true", dest="about",
                      help="Show product version, copyright, and license.")
    
    if args is None:
        if isGAE:
            args = ["--webserver=::gae"]
        elif isCGI:
            args = ["--webserver=::cgi"]
        
    (options, leftoverArgs) = parser.parse_args(args)
    if options.about:
        print( ("\narelle(r) {0}\n\n"
                "An open source XBRL platform\n"
                "(c) 2010-2015 Mark V Systems Limited\n"
                "All rights reserved\nhttp://www.arelle.org\nsupport@arelle.org\n\n"
                "Licensed under the Apache License, Version 2.0 (the \"License\"); "
                "you may not \nuse this file except in compliance with the License.  "
                "You may obtain a copy \nof the License at "
                "'http://www.apache.org/licenses/LICENSE-2.0'\n\n"
                "Unless required by applicable law or agreed to in writing, software \n"
                "distributed under the License is distributed on an \"AS IS\" BASIS, \n"
                "WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  \n"
                "See the License for the specific language governing permissions and \n"
                "limitations under the License."
                "\n\nIncludes:"
                "\n   Python(r) (c) 2001-2013 Python Software Foundation"
                "\n   Bottle (c) 2011-2013 Marcel Hellkamp"
                "{1}"
                ).format(Version.version))
    elif len(leftoverArgs) != 0:
        parser.error("incorrect arguments, please try\n  python CntlrCmdLine.py --help")
    elif options.webserver:
        # cntlr.startLogging(logFileName='logToBuffer')
        host, sep, portServer = options.webserver.partition(":")
        port, sep, server = portServer.partition(":")
        if server:
            run(host=host, port=port or 80, server=server)
        else:
            run(host=host, port=port or 80)

@route(u'/favicon.ico')
def arelleIcon():
    """Request for icon for URL display (get */favicon.ico*).
    
    :returns: ico -- Icon file for browsers
    """
    return static_file("arelle.ico", root=imagesDir)

@route(u'/')
def image():
    """Request for an cli index file(get */lib/cli/cli_index.html).
    
    :returns: file -- Requested file from cli directory of application for browsers
    """
    return static_file(u'index.html', root=libDir)

@route(u'/lib/cli/<cliFile:path>')
@route(u'/cli/<cliFile:path>')
def ckiPath(cliFile):
    """Request for an cli file(get */lib/cli/<cliPath>*).
    
    :returns: file -- Requested file from cli directory of application for browsers
    """
    return static_file(cliFile, root=cliDir)

@route(u'/lib/UI/<uiFilePath:path>')
@route(u'/UI/<uiFilePath:path>')
def uiFile(uiFilePath):
    """Request for an UI File file for URL display (get */images/<imgFile>*).
    
    :returns: UI file -- Requested image file from images directory of application for browsers
    """
    return static_file(uiFilePath, root=uiDir)

from XbrlSemanticDB import testConnection
@route(u'/testDBconnection')
def testDBconnection():
    return jsonResults(testConnection)

from ViewFilings import viewFilings
@route(u'/grid/filings')
def gridFilings():
    return jsonResults(viewFilings)

from ViewDocuments import viewDocuments
@route(u'/grid/documents')
def gridDocuments():
    return jsonResults(viewDocuments)

from ViewDTS import viewDTS
@route(u'/grid/DTS')
def _viewDTS():
    return jsonResults(viewDTS)

from ViewDataPoints import viewDataPoints, selectDataPoints
@route(u'/grid/datapoints')
def _viewDataPoints():
    return jsonResults(viewDataPoints)
@route(u'/select/datapoints')
def _selectDataPoints():
    return jsonResults(selectDataPoints)

from ViewAspects import viewAspects, selectAspects
@route(u'/grid/aspects')
def _viewAspects():
    return jsonResults(viewAspects)
@route(u'/select/aspects')
def _selectAspects():
    return jsonResults(selectAspects)

from ViewMessages import viewMessages
@route(u'/grid/messages')
def _viewMessages():
    return jsonResults(viewMessages)

from ViewProperties import viewProperties
@route(u'/grid/properties')
def _viewProperties():
    return jsonResults(viewProperties)

from ViewRelationships import viewRelationships, selectRelationships
@route(u'/grid/relationships')
def _viewRelationships():
    return jsonResults(viewRelationships)
@route(u'/select/relationships')
def _selectRelationships():
    return jsonResults(selectRelationships)

from ViewMultivariate import viewMultivariateRules, selectMultivariateRules
@route(u'/grid/multivariateRules')
def _viewMultivariateRules():
    return jsonResults(viewMultivariateRules)
@route(u'/select/multivariateRules')
def _selectMultivariateRules():
    return jsonResults(selectMultivariateRules)

from ViewMultivariate import viewMultivariateFilings, selectMultivariateFilings
@route(u'/grid/multivariateFilings')
def _viewMultivariateFilings():
    return jsonResults(viewMultivariateFilings)
@route(u'/select/multivariateFilings')
def _selectMultivariateFilings():
    return jsonResults(selectMultivariateFilings)

from ViewMultivariate import viewMultivariateProperties
@route(u'/view/multivariateProperties')
def _viewMultivariateProperties():
    return jsonResults(viewMultivariateProperties)



from ViewMultivariate import viewMultivariateGrid, selectMultivariateGrid
@route(u'/grid/multivariateGrid')
def _viewMultivariateGrid():
    return jsonResults(viewMultivariateGrid)
@route(u'/select/multivariateGrid')
def _selectMultivariateGrid():
    return jsonResults(selectMultivariateGrid)

@route('/rest/stopWebServer')
def stopWebServer():
    """Stop the web server by *get* requests to */rest/stopWebServer*.
    
    """
    def stopSoon(delaySeconds):
        time.sleep(delaySeconds)
        import signal
        os.kill(_os_pid, signal.SIGTERM)
    thread = threading.Thread(target=lambda: stopSoon(2.5))
    thread.daemon = True
    thread.start()
    response.content_type = 'text/html; charset=UTF-8'
    return htmlBody(tableRows((time.strftime("Received at %Y-%m-%d %H:%M:%S"),
                               "Good bye...",), 
                              header=_("Stop Request")))

@route('/localhost.crt')
def localhostCertificate():
    """Interface to QuickBooks server responding to  *get* requests for a host certificate */quickbooks/localhost.crt* or */localhost.crt*.
    
    (Supports QuickBooks protocol.)
    
    :returns: self-signed certificate
    """
    return '''
-----BEGIN CERTIFICATE-----
MIIDljCCAn4CAQAwDQYJKoZIhvcNAQEEBQAwgZAxCzAJBgNVBAYTAlVTMRMwEQYD
VQQIEwpDYWxpZm9ybmlhMQ8wDQYDVQQHEwZFbmNpbm8xEzARBgNVBAoTCmFyZWxs
ZS5vcmcxDzANBgNVBAsTBmFyZWxsZTESMBAGA1UEAxMJbG9jYWxob3N0MSEwHwYJ
KoZIhvcNAQkBFhJzdXBwb3J0QGFyZWxsZS5vcmcwHhcNMTIwMTIwMDg0NjM1WhcN
MTQxMDE1MDg0NjM1WjCBkDELMAkGA1UEBhMCVVMxEzARBgNVBAgTCkNhbGlmb3Ju
aWExDzANBgNVBAcTBkVuY2lubzETMBEGA1UEChMKYXJlbGxlLm9yZzEPMA0GA1UE
CxMGYXJlbGxlMRIwEAYDVQQDEwlsb2NhbGhvc3QxITAfBgkqhkiG9w0BCQEWEnN1
cHBvcnRAYXJlbGxlLm9yZzCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEB
AMJEq9zT4cdA2BII4TG4OJSlUP22xXqNAJdZZeB5rTIX4ePwIZ8KfFh/XWQ1/q5I
c/rkZ5TyC+SbEmQa/unvv1CypMAWWMfuguU6adOsxt+zFFMJndlE1lr3A2SBjHbD
vBGzGJJTivBzDPBIQ0SGcf32usOeotmE2PA11c5en8/IsRXm9+TA/W1xL60mfphW
9PIaJ+WF9rRROjKXVdQZTRFsNRs/Ag8o3jWEyWYCwR97+XkorYsAJs2TE/4zV+8f
8wKuhOrsy9KYFZz2piVWaEC0hbtDwX1CqN+1oDHq2bYqLygUSD/LbgK1lxM3ciVy
ewracPVHBErPlcJFxiOxAw0CAwEAATANBgkqhkiG9w0BAQQFAAOCAQEAM2np3UVY
6g14oeV0Z32Gn04+r6FV2D2bobxCVLIQDsWGEv1OkjVBJTu0bLsZQuNVZHEn5a+2
I0+MGME3HK1rx1c8MrAsr5u7ZLMNj7cjjtFWAUp9GugJyOmGK136o4/j1umtBojB
iVPvHsAvwZuommfME+AaBE/aJjPy5I3bSu8x65o1fuJPycrSeLAnLd/shCiZ31xF
QnJ9IaIU1HOusplC13A0tKhmRMGNz9v+Vqdj7J/kpdTH7FNMulrJTv/0ezTPjaOB
QhpLdqly7hWJ23blbQQv4ILT2CiPDotJslcKDT7GzvPoDu6rIs2MpsB/4RDYejYU
+3cu//C8LvhjkQ==
-----END CERTIFICATE-----
'''
    
@route('/about')
def about():
    """About web page for *get* requests to */about*.
    
    :returns: html - About web page
    """
    return htmlBody(u'''<table width="700p">
<tr><th colspan="2">About arelle</th></tr>
<tr><td rowspan="12" style="vertical-align:top;"><img src="/lib/cli/images/arelle32.gif"/></td><td>arelle&reg; version: %s %s. An open source XBRL platform</td></tr>
<tr><td>&copy; 2010-2013 Mark V Systems Limited.  All rights reserved.</td></tr>
<tr><td>Web site: <a href="http://www.arelle.org">http://www.arelle.org</a>.  
E-mail support: <a href="mailto:support@arelle.org">support@arelle.org</a>.</td></tr>
<tr><td>Licensed under the Apache License, Version 2.0 (the \"License\"); you may not use this file 
except in compliance with the License.  You may obtain a copy of the License at
<a href="http://www.apache.org/licenses/LICENSE-2.0">http://www.apache.org/licenses/LICENSE-2.0</a>.
Unless required by applicable law or agreed to in writing, software distributed under the License 
is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  
See the License for the specific language governing permissions and limitations under the License.</td></tr>
<tr><td>Includes:</td><tr>
<tr><td style="text-indent: 2.0em;">Python&reg; &copy; 2001-2010 Python Software Foundation</td></tr>
<tr><td style="text-indent: 2.0em;">PyParsing &copy; 2003-2010 Paul T. McGuire</td></tr>
<tr><td style="text-indent: 2.0em;">lxml &copy; 2004 Infrae, ElementTree &copy; 1999-2004 by Fredrik Lundh</td></tr>
<tr><td style="text-indent: 2.0em;">xlrd &copy; 2005-2009 Stephen J. Machin, Lingfo Pty Ltd, &copy; 2001 D. Giffin, &copy; 2000 A. Khan</td></tr>
<tr><td style="text-indent: 2.0em;">xlwt &copy; 2007 Stephen J. Machin, Lingfo Pty Ltd, &copy; 2005 R. V. Kiseliov</td></tr>
<tr><td style="text-indent: 2.0em;">Bottle &copy; 2011 Marcel Hellkamp</td></tr>
</table>''' % (__version__, Version.version) )


def htmlBody(body, script=""):
    """Wraps body html string in a css-styled html web page
    
    :param body: Contents for the *<body>* element
    :type body: html str
    :param script: Script to insert in generated html web page (such as a timed reload script)
    :type script: javascript str
    :returns: html - Web page of choices to navigate to */help* or */about*.
    """
    return u'''
<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml">
%s    <head>
        <STYLE type="text/css">
            body, table, p {font-family:Arial,sans-serif;font-size:10pt;}
            table {vertical-align:top;white-space:normal;}
            th {{background:#eee;}}
            td {vertical-align:top;}
            .tableHdr{border-top:.5pt solid windowtext;border-right:none;border-bottom:none;border-left:.5pt solid windowtext;}
            .cell{border-top:1.0pt solid windowtext;border-right:.5pt solid windowtext;border-bottom:.5pt solid windowtext;border-left:.5pt solid windowtext;}
            .blockedCell{border-top:1.0pt solid windowtext;border-right:.5pt solid windowtext;border-bottom:.5pt solid windowtext;border-left:.5pt solid windowtext;background:#eee;}
        </STYLE>
    </head>
    <body>
    %s
    </body>
</html>
''' % (script, body)

def tableRows(lines, header=None):
    """Wraps lines of text into a one-column table (for display of text results of operations, such as processing messages and status, to web browser).
    Replaces any *&* with *&amp;* and *<* with *&lt;*.
    
    :param lines: Sequence (list or tuple) of line strings.
    :type lines: [str]
    :param header: Optional header text for top row of table.
    :type header: str
    :returns: html - <table> html string.
    """
    return '<table cellspacing="0" cellpadding="4">%s\n</table>' % (
            ("<tr><th>%s</th></tr>" % header if header else "") + 
            "\n".join("<tr><td>%s</td></tr>" % line.replace("&","&amp;").replace("<","&lt;") for line in lines))

def errorReport(errors, media="html"):
    """Wraps lines of error text into specified media type for return of result to a request.
    
    :param errors: Sequence (list or tuple) of error strings.
    :type errors: [str]
    :param media: Type of result requestd.
    :type media: str
    :returns: html - <table> html string.
    """
    if media == "text":
        response.content_type = u'text/plain; charset=UTF-8'
        return '\n'.join(errors)
    else:
        response.content_type = u'text/html; charset=UTF-8'
        return htmlBody(tableRows(errors, header="Messages"))

def jsonSerializer(obj):
    if isinstance(obj, datetime):
        serial = obj.isoformat()
        return serial
    
def jsonResults(jsonCompositionFunction):
    try:
        jsonResults = jsonCompositionFunction(request)
        response.content_type = u'application/json; charset=UTF-8'
        return json.dumps( jsonResults, default=jsonSerializer )
    except Exception as ex:
        return errorReport([str(ex)])
    
if __name__ == "__main__":
    main()
