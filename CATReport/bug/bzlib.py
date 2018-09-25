
"""
Portions of this code taken from the testopia bugzilla interface (see
license below). Other portions of this code taken from reviewboard
- jon@vmware.com

The contents of this file are subject to the Mozilla Public
License Version 1.1 (the "License"); you may not use this file
except in compliance with the License. You may obtain a copy of
the License at http://www.mozilla.org/MPL/

Software distributed under the License is distributed on an "AS
IS" basis, WITHOUT WARRANTY OF ANY KIND, either express or
implied. See the License for the specific language governing
rights and limitations under the License.

The Original Code is the Bugzilla Testopia Python API Driver.

The Initial Developer of the Original Code is Airald Hapairai.
Portions created by Airald Hapairai are Copyright (C) 2008
Novell. All Rights Reserved.
Portions created by David Malcolm are Copyright (C) 2008 Red Hat.
All Rights Reserved.
Portions created by Will Woods are Copyright (C) 2008 Red Hat.
All Rights Reserved.
Portions created by Bill Peck are Copyright (C) 2008 Red Hat.
All Rights Reserved.

Contributor(s): Airald Hapairai
  David Malcolm <dmalcolm@redhat.com>
  Will Woods <wwoods@redhat.com>
  Bill Peck <bpeck@redhat.com>

The CookieTransport class is by Will Woods, based on code in
Python's xmlrpclib.Transport, which has this copyright notice:

# The XML-RPC client interface is
#
# Copyright (c) 1999-2002 by Secret Labs AB
# Copyright (c) 1999-2002 by Fredrik Lundh
#
# By obtaining, using, and/or copying this software and/or its
# associated documentation, you agree that you have read, understood,
# and will comply with the following terms and conditions:
#
# Permission to use, copy, modify, and distribute this software and
# its associated documentation for any purpose and without fee is
# hereby granted, provided that the above copyright notice appears in
# all copies, and that both that copyright notice and this permission
# notice appear in supporting documentation, and that the name of
# Secret Labs AB or the author not be used in advertising or publicity
# pertaining to distribution of the software without specific, written
# prior permission.
#
# SECRET LABS AB AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH REGARD
# TO THIS SOFTWARE, INCLUDING ALL IMPLIED WARRANTIES OF MERCHANT-
# ABILITY AND FITNESS.  IN NO EVENT SHALL SECRET LABS AB OR THE AUTHOR
# BE LIABLE FOR ANY SPECIAL, INDIRECT OR CONSEQUENTIAL DAMAGES OR ANY
# DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS,
# WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS
# ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE
# OF THIS SOFTWARE.
"""
import sys

#
# check for recent python; older versions don't have the right cookielib and
# xmlrpclib
#

version = sys.version_info
if not ( version[0] >= 2 and version [1] >= 5 ):
    print "bz.py requires python >= 2.5. Please use the python from the bldmnt systems or upgrade your current installation."
    sys.exit(1);


import xmlrpclib, urllib2, cookielib, os, getpass, sys
import pprint
from types import *
from datetime import datetime, time
from urlparse import urljoin, urlparse
from cookielib import CookieJar
from optparse import OptionParser
from operator import itemgetter
import csv

#csvf = open('./need_info.csv', 'w')
#wf = csv.writer(csvf)

BUGZILLA_URL = 'https://bugzilla.eng.vmware.com/xmlrpc.cgi'
DEBUG = False
VERSION = "0.1"
#options = {'comment': None,
#               'bugzilla_url': 'https://bugzilla.eng.vmware.com/xmlrpc.cgi',
#               'nocolumns': None,
#               'withcolumns': 'bug_id,product,category,component,creation_ts,bug_status,bug_severity,priority,assigned_to,reporter,short_desc,resolution',
#               'comments': None,
#               'debug': False,
#               'query': None,
#               'listcolumns': False,
#               'saved': None,
#               'empty': False}
options = None

PYVERSION = None

if sys.version_info > (2, 8):
    raise AssertionError("python 3 is not supported")

if sys.version_info < (2, 7):
    PYVERSION = "py26"
else:
    PYVERSION = "py27"
    import httplib


class CookieTransport(xmlrpclib.Transport):
    '''A subclass of xmlrpclib.Transport that supports cookies.'''
    cookiejar = None
    scheme = 'https'

    def cookiefile(self):
        if 'USERPROFILE' in os.environ:
            homepath = os.path.join(os.environ["USERPROFILE"], "Local Settings",
            "Application Data")
        elif 'HOME' in os.environ:
            homepath = os.environ["HOME"]
        else:
            homepath = ''

        cookiefile = os.path.join(homepath, ".bugzilla-cookies.txt")
        return cookiefile

    # Cribbed from xmlrpclib.Transport.send_user_agent
    def send_cookies(self, connection, cookie_request):
        if self.cookiejar is None:
            self.cookiejar = cookielib.MozillaCookieJar(self.cookiefile())

            if os.path.exists(self.cookiefile()):
                self.cookiejar.load(self.cookiefile())
            else:
                self.cookiejar.save(self.cookiefile())

        # Let the cookiejar figure out what cookies are appropriate
        self.cookiejar.add_cookie_header(cookie_request)

        # Pull the cookie headers out of the request object...
        cookielist=list()
        for h,v in cookie_request.header_items():
            if h.startswith('Cookie'):
                cookielist.append([h,v])

        # ...and put them over the connection
        for h,v in cookielist:
            connection.putheader(h,v)

    def make_connection_py26(self, host):
        """xmlrpclib make_connection Python 2.6"""
        return self.make_connection(host)

    def make_connection_py27(self, host):
        """xmlrpclib make_connection Python 2.7"""
        # create a HTTPS connection object from a host descriptor
        # host may be a string, or a (host, x509-dict) tuple
        host, self._extra_headers, x509 = self.get_host_info(host)
        try:
            HTTPS = httplib.HTTPS
        except AttributeError:
            raise NotImplementedError(
                "your version of httplib doesn't support HTTPS"
                )
        else:
            return HTTPS(host, None, **(x509 or {}))

    def _parse_response_py26(self, responsefile, sock=None):
        return self._parse_response(responsefile, sock)

    def _parse_response_py27(self, responsefile, sock=None):
        """Code copied from pythong 2.6 lib."""
        # read response from input file/socket, and parse it
        p, u = self.getparser()

        while 1:
            if sock:
                response = sock.recv(1024)
            else:
                response = responsefile.read(1024)
            if not response:
                break
            if self.verbose:
                print "body:", repr(response)
            p.feed(response)

        responsefile.close()
        p.close()

        return u.close()

    # This is the same request() method from xmlrpclib.Transport,
    # with a couple additions noted below
    def request(self, host, handler, request_body, verbose=0):

        h = getattr(self, "make_connection_" + PYVERSION)(host)

        if verbose:
            h.set_debuglevel(1)

        # ADDED: construct the URL and Request object for proper cookie handling
        request_url = "%s://%s/" % (self.scheme,host)
        cookie_request  = urllib2.Request(request_url)

        self.send_request(h,handler,request_body)
        self.send_host(h,host)
        self.send_cookies(h,cookie_request) # ADDED. creates cookiejar if None.
        self.send_user_agent(h)
        self.send_content(h,request_body)

        errcode, errmsg, headers = h.getreply()

        # ADDED: parse headers and get cookies here
        # fake a response object that we can fill with the headers above
        class CookieResponse:
            def __init__(self,headers): self.headers = headers
            def info(self): return self.headers
        cookie_response = CookieResponse(headers)
        # Okay, extract the cookies from the headers
        self.cookiejar.extract_cookies(cookie_response,cookie_request)
        # And write back any changes
        if hasattr(self.cookiejar,'save'):
            self.cookiejar.save(self.cookiejar.filename)

        if errcode != 200:
            raise xmlrpclib.ProtocolError(
                host + handler,
                errcode, errmsg,
                headers
                )

        self.verbose = verbose

        try:
            sock = h._conn.sock
        except AttributeError:
            sock = None

        return getattr(self, "_parse_response_" + PYVERSION)(h.getfile(), sock)


class SafeCookieTransport(xmlrpclib.SafeTransport,CookieTransport):
    '''SafeTransport subclass that supports cookies.'''
    scheme = 'https'
    request = CookieTransport.request

VERBOSE=0

class BugzillaServer(object):

    def __init__(self, url, cookie_file, options):
        self.url = url
        self.cookie_file = cookie_file
        self.options = options
        self.cookie_jar = cookielib.MozillaCookieJar(self.cookie_file)
        self.server = xmlrpclib.ServerProxy(url, SafeCookieTransport())
        self.columns = None

    def login(self, username=None, password=None):

        if self.has_valid_cookie():
            return

        print "==> Bugzilla Login Required"
        print "Enter username and password for Bugzilla at %s" % self.url

        if not (username and password):
            username = raw_input('Username: ')
            password = getpass.getpass('Password: ')

        debug('Logging in with username "%s"' % username)
        try:
            self.server.User.login({"login" : username, "password" :
            password})
        except xmlrpclib.Fault, err:
            print "A fault occurred:"
            print "Fault code: %d" % err.faultCode
            print "Fault string: %s" % err.faultString
        debug("logged in")
        self.cookie_jar.save;

    def get_columns(self, filter):
        if self.columns is None:
            try:
                self.columns = self.server.Bug.get_columns(filter)
            except xmlrpclib.Fault, err:
                print "A fault occurred:"
                print "Fault code: %d" % err.faultCode
                print "Fault string: %s" % err.faultString
                sys.exit(1)
        return self.columns

    def saved_queries(self, user):
        try:
            self.queries = self.server.Search.get_all_saved_queries(user)
        except xmlrpclib.Fault, err:
                print "A fault occurred:"
                print "Fault code: %s" % err.faultCode
                print "Fault string: %s" % err.faultString
                sys.exit(1)
        for query in self.queries:
            print query
        sys.exit(0)

    def query(self, query):
        self.parse_columns('buglist')
        try:
            self.query = self.server.Search.run_saved_query(query[0],
            query[1], self.withcolumns)
        except xmlrpclib.Fault, err:
                print "A fault occurred:"
                print "Fault code: %s" % err.faultCode
                print "Fault string: %s" % err.faultString
                sys.exit(1)

        if self.withcolumns:
            # If columns were supplied we print out a pretty table
            header = "|"
            # Sort CLI-fed columns by fielddefs.sortkey
            sorted_columns = sorted(self.withcolumns.iteritems(),
                                    key=itemgetter(1))
            for column in map(itemgetter(0), sorted_columns):
                header = header + " %s |" % \
                self.query['columns'][column]['title'].ljust(self.query['maxsize'][column] + 1)

            print "_" * len(header)
            print header
            print "|" + "_" * (len(header) - 2) + "|"
            for bug in self.query['bugs']:
                row = '|'
                for column in map(itemgetter(0), sorted_columns):
                    value = ''
                    if bug.has_key(column):
                        if isinstance( bug[column], basestring):
                            if (len(bug[column]) > 60):
                                # deal with truncated values
                                bug[column] = bug[column][0:56] + "..."

                        value = " %.60s" % bug[column]
                    row = row + value.ljust(self.query['maxsize'][column] + 2) + " |"
                print row
            print "|" + "-" * (len(header) - 2) + "|"
        else:
            # no columns, just a list of bug ids
            for id in self.query['bugidlist']:
                print id

    def list_columns(self):
        columns = self.get_columns('buglist')
        print "_" * 52
        print "| %s| %s |" % ('Name'.ljust(20), 'Description'.ljust(26))
        print "|" + "-" * 50 + "|"
        for column in columns:
            print "| %s| %s |" % (column['name'].ljust(20), column['description'].ljust(26))
        print "|" + "-" * 50 + "|"

    def add_comment(self, bug_id, comment):
        try:
            self.server.Bug.add_comment(bug_id, comment)
        except xmlrpclib.Fault, err:
            print "A fault occurred:"
            print "Fault code: %d" % err.faultCode
            print "Fault string: %s" % err.faultString
            sys.exit(1)

        print "Comment added to bug %s" % bug_id

    def parse_columns(self, filter):
        self.withcolumns = {}
        self.nocolumns = {}

        if self.options.withcolumns is not None:
            for column in self.options.withcolumns.split(','):
                for all_col in self.get_columns(filter):
                    if column == all_col['name']:
                        self.withcolumns[column] = all_col['sortkey']

        if self.options.nocolumns is not None:
            for column in self.options.nocolumns.split(','):
                self.nocolumns[column] = 1

    def show_bug(self, bug_id):
        try:
            bug = self.server.Bug.show_bug(bug_id)
        except xmlrpclib.Fault, err:
            print "A fault occurred:"
            print "Fault code: %d" % err.faultCode
            print "Fault string: %s" % err.faultString
            sys.exit(1)

        columns = self.get_columns('bug')
        # list of fields where zero is a valid (non-empty) result
        zerofields = ('cf_attempted', 'cf_failed')
        # list of fields to convert time format
        timefields = ('delta_ts', 'creation_ts')
        for timefield in timefields:
            converted = datetime.strptime(bug[timefield].value,
            "%Y%m%dT%H:%M:%S")
            bug[timefield] = converted.strftime("%Y.%m.%d %H:%M:%S")

        self.parse_columns('bug')

        qelist = ['fhou', 'vluo', 'phu', 'shuc', 'stephenw', 'weichen',
        'zhangt', 'sxiao', 'yubiny', 'lhong', 'wsiqi', 'kaiyuanli', 'hsu',
        'lih', 'shengnanz', 'louh', 'sreagan', 'vadithya', 'vsimha', 'zhuojil',
        'jdong', 'ldong', 'jtruong']
        infos = dict()
        for column in columns:
            if self.options.nocolumns:
                if column['name'] in self.nocolumns:
                    continue

            if self.options.withcolumns:
                if column['name'] not in self.withcolumns:
                    continue

            if column['name'] == "comments":
                continue
                if (bug.has_key('comments') and
                    (self.options.comments or
                     (self.options.withcolumns and
                      "comments" not in self.withcolumns))):
                    for comment in bug['comments']:
                        for act in comment['activity']:
                            if (act.has_key('what') and 
                                act['what'] == 'Need Info'):
                                for qe in qelist:
                                    if qe in act['added'] or qe in act['removed']:
                                        wf.writerow((bug_id, act['email'],
                                        act['added'], act['removed'],
                                        act['time'], comment['body'] if comment.has_key('body') else ''))
                                        print "%s#%s#%s#%s#%s#"% (bug_id,
                                            act['email'], act['added'], act['removed'],
                                            act['time'])
                                        #if (qe in act['added'] and
                                        #    comment.has_key('body')):
                                        #    print comment['body']
                                        break;
                                #print "\nOn %s %s wrote:\n%s\n%s"% (comment['time'],
                                #                        comment['email'],
                                #                        comment['name'],
                                #                        comment['activity'])
                                                        #comment['body'])
                                if comment.has_key('body'):
                                    pass
                                    #print "BBBBody \n%s\n" % comment['body']
            elif column['name'] == "description":
                pass
                #print "Initial Description:\n%s\n" % bug['description']
            else:
                if ((bug[column['name']] and (bug[column['name']] != "---")) or
                ( column['name'] in zerofields and bug[column['name']] == 0)
                or self.options.empty):
                    #pass
                    print "%s: %s" % (column['description'], bug[column['name']])
                    infos[column['description']] = bug[column['name']]
         
        return infos

    def has_valid_cookie(self):
        try:
            parsed_url = urlparse(self.url)
            host = parsed_url[1]
            path = parsed_url[2] or '/'

            # Cookie files don't store port numbers, unfortunately, so
            # get rid of the port number if it's present.
            host = host.split(":")[0]

            debug( "Looking for '%s' cookie in %s" % \
                  (host, self.cookie_file))
            self.cookie_jar.load(self.cookie_file, ignore_expires=True)

            try:
                cookie = self.cookie_jar._cookies[host]['/']['Bugzilla_logincookie']

                if not cookie.is_expired():
                    debug("Loaded valid cookie -- no login required")
                    return True

                debug("Cookie file loaded, but cookie has expired")
            except KeyError:
                debug("Cookie file loaded, but no cookie for this server")
        except IOError, error:
            debug("Couldn't load cookie file: %s" % error)

        return False


def parse_options(args):
    parser = OptionParser(usage="%prog [-l|q] [-bcde] [-w|n] [column names] \
    [-a] [comment] [bug_id]",
                          version="%prog " + VERSION)
    parser.add_option("-a", "--addcomment",
                      action="store", dest="comment", default=None,
                      help="add a comment to the given bug",
                      type="string")
    parser.add_option("-b", "--bugzillaurl",
                      action="store", dest="bugzilla_url",
                      default=BUGZILLA_URL,
                      help="full url to xmlrpc.cgi on bugzilla server",
                      type="string")
    parser.add_option("-c", "--comments",
                      action="store_true", dest="comments", default=None,
                      help="show comments")
    parser.add_option("-d", "--debug",
                      action="store_true", dest="debug", default=DEBUG,
                      help="display debug output")
    parser.add_option("-e", "--empty",
                      action="store_true", dest="empty", default=False,
                      help="show fields with empty values")
    parser.add_option("-q", "--query",
                      dest="query", type="string",
                      help="see a user's saved query", nargs=2)
    parser.add_option("-s", "--savedqueries",
                      dest="saved", type="string",
                      help="view all of a user's saved queries", nargs=1)
    parser.add_option("-l", "--listcolumns",
                      action="store_true", dest="listcolumns", default=False,
                      help="list available bug columns")
    parser.add_option("-n", "--nocolumns",
                      action="store", dest="nocolumns", default=None,
                      help="comma-separated list of columns not to display",
                      type="string")
    parser.add_option("-w", "--withcolumns",
                      action="store", dest="withcolumns", default=None,
                      help="comma-separated list of columns to display",
                      type="string")

    (globals()["options"], args) = parser.parse_args(args)
    return args

def debug(s):
    """
    Prints debugging information if run with --debug
    """
    pass
    #global  options
    #if DEBUG or options and options.debug:
    #    print ">>> %s" % s

def loginBugzillaServer(username=None, password=None):
    if 'USERPROFILE' in os.environ:
        homepath = os.path.join(os.environ["USERPROFILE"], "Local Settings",
                                "Application Data")
    elif 'HOME' in os.environ:
        homepath = os.environ["HOME"]
    else:
        homepath = ''

    cookie_file = os.path.join(homepath, ".bugzilla-cookies.txt")

    bugzilla_url = BUGZILLA_URL
    args = ['-w', 'bug_id,product,category,component,creation_ts,bug_status,bug_severity,priority,assigned_to,reporter,short_desc,resolution,dup_id']
    args = parse_options(args)

    server = BugzillaServer(bugzilla_url, cookie_file, options)
    server.login(username, password)
    return server


def getBugSummary(bugid, username=None, password=None):
    server = loginBugzillaServer(username, password)
    b = server.show_bug(bugid)
    while b.has_key('Dup_id'):
       print("Bug %s is in duplicate with bug %s" % (bugid, b['Dup_id']))
       print("Get the summary of bug %s" % b['Dup_id'])
       b = server.show_bug(b['Dup_id'])
    return b

def getBugInfo(cat_list, username=None, password=None):
    server = loginBugzillaServer()

    def addData(arr, b, cat):
        for a in arr:
           if cat[0] == a[1]:
              a[0] += cat[2]
              break
        else:
           arr.append([cat[2], cat[0], b['Creation Date'].split()[0],
              b['Severity'], b['Priority'], b['Status'], b['Assigned To'],
              b['Reporter'], b['Category'], b['Component'], b['Summary']])


    return_list = dict()
    com_list = ['infra_bugs', 'Core_p_bugs', 'Core_t_bugs',
                'UW_p_bugs', 'UW_t_bugs', 'RM_p_bugs',
                'RM_t_bugs', 'Oth_p_bugs', 'Oth_t_bugs']
    for com in com_list:
        return_list[com] = {'Total': 0, 'Fixed': 0,
                                 'bugs': []}
    for line in cat_list:
        if (line[0].startswith('Ignored') or line[0].startswith('NeedTriage')):
            continue
        bugid = line[0].split('>')[1].split('<')[0].split('R')[1]
        b = server.show_bug(bugid)
        while b.has_key('Dup_id'):
           b = server.show_bug(b['Dup_id'])
           line[0] = "<a href=https://bugzilla.eng.vmware.com/show_bug.cgi?id=%s>PR%s</a> " % (b['Bug ID'], b['Bug ID'])

        if ((b['Category'] == 'CAT' and b['Component'] == 'defects') or
             (b['Category'].startswith('Infrastructure')) or
             (b['Category'] == 'Nimbus') or
             (b['Category'].startswith('Test Infrastruc')) or
             (b['Category'] == 'Test' and b['Component'] == 'Operation') or 
             (b['Category'] == 'Test' and b['Component'] == 'VMkernelQA Auto')):
             addData(return_list['infra_bugs']['bugs'], b, line)
        elif (b['Category'] == 'ESX Server' and 
                   ((b['Component'] == 'iofilters') or
                    (b['Component'] == 'jumpstart') or
                    (b['Component'] == 'loadESX') or
                    (b['Component'] == 'logging') or
                    (b['Component'].startswith('RDMA')) or
                    (b['Component'].startswith('vmkapi')) or
                    (b['Component'].startswith('vmkcore')) or
                    (b['Component'] == 'vmkdriver-iscsi'))):
             addData(return_list['Core_p_bugs']['bugs'], b, line)
        elif (b['Category'] == 'ESX Server' and 
                   ((b['Component'] == 'esxcli') or
                    (b['Component'] == 'userworld'))):
             addData(return_list['UW_p_bugs']['bugs'], b, line)
        elif (b['Category'] == 'ESX Server' and 
                   ((b['Component'].startswith('resource mgmt')))):
             addData(return_list['RM_p_bugs']['bugs'], b, line)
        elif (b['Category'] == 'Tests' and 
                   ((b['Component'] == 'RDMA') or
                    (b['Component'] == 'VMcrypt') or
                    (b['Component'] == 'vmkapi') or
                    (b['Component'].startswith('vmkcore')) or
                    (b['Component'] == 'vmkernel - debu'))):
             addData(return_list['Core_t_bugs']['bugs'], b, line)
        elif (b['Category'] == 'Tests' and 
                   ((b['Component'].startswith('userworld')) or
                    (b['Component'] == 'userworld - too') or
                    (b['Component'] == 'esxcli - API') or
                    (b['Component'] == 'vmkcore - vmkct'))):
             addData(return_list['UW_t_bugs']['bugs'], b, line)
        elif (b['Category'] == 'Tests' and 
                   ((b['Component'].startswith('resource mgmt')))):
             addData(return_list['RM_t_bugs']['bugs'], b, line)
        elif (b['Category'] == 'Tests'):
             addData(return_list['Oth_t_bugs']['bugs'], b, line)
        else:
             addData(return_list['Oth_p_bugs']['bugs'], b, line)
             

    for com in com_list:
        total_pr = 0
        fixed_pr = 0
        for c in return_list[com]['bugs']:
           if (c[5] == 'resolved' or c[5] == 'closed'):
               fixed_pr += 1
           total_pr += 1
        return_list[com]['Total'] = total_pr
        return_list[com]['Fixed'] = fixed_pr
    print(return_list)
    return return_list

def main(args):
    global bugs_info
    if 'USERPROFILE' in os.environ:
        homepath = os.path.join(os.environ["USERPROFILE"], "Local Settings",
                                "Application Data")
    elif 'HOME' in os.environ:
        homepath = os.environ["HOME"]
    else:
        homepath = ''

    cookie_file = os.path.join(homepath, ".bugzilla-cookies.txt")

    args = parse_options(args)
    bugzilla_url = options.bugzilla_url

    server = BugzillaServer(bugzilla_url, cookie_file, options)
    server.login()

    if (options.saved):
        server.saved_queries(options.saved)
        sys.exit(0)

    if (options.query):
        server.query(options.query)
        sys.exit(0)

    if (options.listcolumns):
        server.list_columns()
        sys.exit(0)

    if len(args) < 1:
        print "You must specify a bug number"
        sys.exit(1)

    bug_id = args[0].split(',')

    if (options.comment):
        server.add_comment(bug_id, options.comment)
        sys.exit(0)

    if (options.withcolumns and options.nocolumns):
        print "--nocolumns and --withcolumns are mutually exclusive"
        sys.exit(1)

    for b in bug_id:
        bug = server.show_bug(b)
    #csvf.close()
    print bugs_info
    infra_bugs = []
    Core_p_bugs = []
    Core_t_bugs = []
    UW_p_bugs = []
    UW_t_bugs = []
    RM_p_bugs = []
    RM_t_bugs = []
    Oth_p_bugs = []
    Oth_t_bugs = []
    for b in bugs_info:
        if ((b['Category'] == 'CAT' and b['Component'] == 'defects') or
             (b['Category'].startswith('Infrastructure')) or
             (b['Category'] == 'Nimbus') or
             (b['Category'].startswith('Test Infrastruc')) or
             (b['Category'] == 'Test' and b['Component'] == 'Operation') or 
             (b['Category'] == 'Test' and b['Component'] == 'VMkernelQA Auto')):
            infra_bugs.append(b)
        elif (b['Category'] == 'ESX Server' and 
                   ((b['Component'] == 'iofilters') or
                    (b['Component'] == 'jumpstart') or
                    (b['Component'] == 'loadESX') or
                    (b['Component'] == 'logging') or
                    (b['Component'].startswith('RDMA')) or
                    (b['Component'].startswith('vmkapi')) or
                    (b['Component'].startswith('vmkcore')) or
                    (b['Component'] == 'vmkdriver-iscsi'))):
             Core_p_bugs.append(b)
        elif (b['Category'] == 'ESX Server' and 
                   ((b['Component'] == 'esxcli') or
                    (b['Component'] == 'userworld'))):
             UW_p_bugs.append(b)
        elif (b['Category'] == 'ESX Server' and 
                   ((b['Component'] == 'resource mgmt -'))):
             RM_p_bugs.append(b)
        elif (b['Category'] == 'Tests' and 
                   ((b['Component'] == 'RDMA') or
                    (b['Component'] == 'VMcrypt') or
                    (b['Component'] == 'vmkapi') or
                    (b['Component'].startswith('vmkcore')) or
                    (b['Component'] == 'vmkernel - debu'))):
             Core_t_bugs.append(b)
        elif (b['Category'] == 'Tests' and 
                   ((b['Component'].startswith('userworld')) or
                    (b['Component'] == 'userworld - too') or
                    (b['Component'] == 'esxcli - API') or
                    (b['Component'] == 'vmkcore - vmkct'))):
             UW_t_bugs.append(b)
        elif (b['Category'] == 'Tests' and 
                   ((b['Component'].startswith('resource mgmt')))):
             RM_t_bugs.append(b)
        elif (b['Category'] == 'Tests'):
             Oth_t_bugs.append(b)
        else:
             Oth_p_bugs.append(b)
             
    def show_line(bug):
        print("%s#%s#%s#%s#%s#%s#%s#%s#%s#%s" %(b['Bug ID'], b['Creation Date'].split()[0], b['Severity'], b['Priority'], b['Status'], b['Assigned To'], b['Reporter'], b['Category'], b['Component'], b['Summary']))

        
    total_pr = 0
    fixed_pr = 0
    for b in infra_bugs:
       if (b['Status'] == 'resolved' or b['Status'] == 'closed'):
           fixed_pr += 1
       total_pr += 1
    print("Infra test issue#Total PRs:%d#Fixed PRs:%d" %(total_pr, fixed_pr))
    for b in infra_bugs:
        show_line(b)

    total_pr = 0
    fixed_pr = 0
    for b in Core_p_bugs:
       if (b['Status'] == 'resolved' or b['Status'] == 'closed'):
           fixed_pr += 1
       total_pr += 1
    print("Core product issue#Total PRs:%d#Fixed PRs:%d" %(total_pr, fixed_pr))
    for b in Core_p_bugs:
        show_line(b)


    total_pr = 0
    fixed_pr = 0
    for b in Core_t_bugs:
       if (b['Status'] == 'resolved' or b['Status'] == 'closed'):
           fixed_pr += 1
       total_pr += 1
    print("Core test issue#Total PRs:%d#Fixed PRs:%d" %(total_pr, fixed_pr))
    for b in Core_t_bugs:
        show_line(b)

    total_pr = 0
    fixed_pr = 0
    for b in UW_p_bugs:
       if (b['Status'] == 'resolved' or b['Status'] == 'closed'):
           fixed_pr += 1
       total_pr += 1
    print("UW product issue#Total PRs:%d#Fixed PRs:%d" %(total_pr, fixed_pr))
    for b in UW_p_bugs:
        show_line(b)
    
    total_pr = 0
    fixed_pr = 0
    for b in UW_t_bugs:
       if (b['Status'] == 'resolved' or b['Status'] == 'closed'):
           fixed_pr += 1
       total_pr += 1
    print("UW test issue#Total PRs:%d#Fixed PRs:%d" %(total_pr, fixed_pr))
    for b in UW_t_bugs:
        show_line(b)
    
    total_pr = 0
    fixed_pr = 0
    for b in RM_p_bugs:
       if (b['Status'] == 'resolved' or b['Status'] == 'closed'):
           fixed_pr += 1
       total_pr += 1
    print("RM product issue#Total PRs:%d#Fixed PRs:%d" %(total_pr, fixed_pr))
    for b in RM_p_bugs:
        show_line(b)

    total_pr = 0
    fixed_pr = 0
    for b in RM_t_bugs:
       if (b['Status'] == 'resolved' or b['Status'] == 'closed'):
           fixed_pr += 1
       total_pr += 1
    print("RM test issue#Total PRs:%d#Fixed PRs:%d" %(total_pr, fixed_pr))
    for b in RM_t_bugs:
        show_line(b)
    
    total_pr = 0
    fixed_pr = 0
    for b in Oth_p_bugs:
       if (b['Status'] == 'resolved' or b['Status'] == 'closed'):
           fixed_pr += 1
       total_pr += 1
    print("Other product issue#Total PRs:%d#Fixed PRs:%d" %(total_pr, fixed_pr))
    for b in Oth_p_bugs:
        show_line(b)
    
    total_pr = 0
    fixed_pr = 0
    for b in Oth_t_bugs:
       if (b['Status'] == 'resolved' or b['Status'] == 'closed'):
           fixed_pr += 1
       total_pr += 1
    print("Other test issue#Total PRs:%d#Fixed PRs:%d" %(total_pr, fixed_pr))
    for b in Oth_t_bugs:
        show_line(b)

if __name__ == "__main__":
    #main(sys.argv[1:])
    info_list = [['<a href=https://bugzilla.eng.vmware.com/show_bug.cgi?id=1779835>PR1779835</a> ', ' vmcore-main:obj', 4, '<a href=https://cat.eng.vmware.com/testrun/41741766/?legacy=true>41741766</a>, <a href=https://cat.eng.vmware.com/testrun/41712873/?legacy=true>41712873</a>, <a href=https://cat.eng.vmware.com/testrun/41710470/?legacy=true>41710470</a>, <a href=https://cat.eng.vmware.com/testrun/41709927/?legacy=true>41709927</a>'], ['Ignored ', ' vmcore-main:obj', 8, '<a href=https://cat.eng.vmware.com/testrun/41739504/?legacy=true>41739504</a>, <a href=https://cat.eng.vmware.com/testrun/41739534/?legacy=true>41739534</a>, <a href=https://cat.eng.vmware.com/testrun/41709156/?legacy=true>41709156</a>, <a href=https://cat.eng.vmware.com/testrun/41727684/?legacy=true>41727684</a>, <a href=https://cat.eng.vmware.com/testrun/41722518/?legacy=true>41722518</a>, <a href=https://cat.eng.vmware.com/testrun/41714079/?legacy=true>41714079</a>, <a href=https://cat.eng.vmware.com/testrun/41739483/?legacy=true>41739483</a>, <a href=https://cat.eng.vmware.com/testrun/41739480/?legacy=true>41739480</a>'], ['<a href=https://bugzilla.eng.vmware.com/show_bug.cgi?id=1777223>PR1777223</a> ', ' vmcore-main:obj', 3, '<a href=https://cat.eng.vmware.com/testrun/41742354/?legacy=true>41742354</a>, <a href=https://cat.eng.vmware.com/testrun/41737179/?legacy=true>41737179</a>, <a href=https://cat.eng.vmware.com/testrun/41715603/?legacy=true>41715603</a>'], ['<a href=https://bugzilla.eng.vmware.com/show_bug.cgi?id=1787080>PR1787080</a> ', ' vmcore-main:obj', 14, '<a href=https://cat.eng.vmware.com/testrun/41725701/?legacy=true>41725701</a>, <a href=https://cat.eng.vmware.com/testrun/41723094/?legacy=true>41723094</a>, <a href=https://cat.eng.vmware.com/testrun/41718267/?legacy=true>41718267</a>, <a href=https://cat.eng.vmware.com/testrun/41717739/?legacy=true>41717739</a>, <a href=https://cat.eng.vmware.com/testrun/41715918/?legacy=true>41715918</a>, <a href=https://cat.eng.vmware.com/testrun/41714106/?legacy=true>41714106</a>, <a href=https://cat.eng.vmware.com/testrun/41712234/?legacy=true>41712234</a>, <a href=https://cat.eng.vmware.com/testrun/41709900/?legacy=true>41709900</a>, <a href=https://cat.eng.vmware.com/testrun/41707749/?legacy=true>41707749</a>, <a href=https://cat.eng.vmware.com/testrun/41725140/?legacy=true>41725140</a>, <a href=https://cat.eng.vmware.com/testrun/41722512/?legacy=true>41722512</a>, <a href=https://cat.eng.vmware.com/testrun/41714076/?legacy=true>41714076</a>, <a href=https://cat.eng.vmware.com/testrun/41711193/?legacy=true>41711193</a>, <a href=https://cat.eng.vmware.com/testrun/41707965/?legacy=true>41707965</a>'], ['<a href=https://bugzilla.eng.vmware.com/show_bug.cgi?id=1787206>PR1787206</a> ', ' vmcore-main:obj', 2, '<a href=https://cat.eng.vmware.com/testrun/41729958/?legacy=true>41729958</a>, <a href=https://cat.eng.vmware.com/testrun/41708307/?legacy=true>41708307</a>'], ['NeedTriage ', ' vmcore-main:obj', 17, '<a href=https://cat.eng.vmware.com/testrun/41738535/?legacy=true>41738535</a>, <a href=https://cat.eng.vmware.com/testrun/41712735/?legacy=true>41712735</a>, <a href=https://cat.eng.vmware.com/testrun/41710479/?legacy=true>41710479</a>, <a href=https://cat.eng.vmware.com/testrun/41742099/?legacy=true>41742099</a>, <a href=https://cat.eng.vmware.com/testrun/41712183/?legacy=true>41712183</a>, <a href=https://cat.eng.vmware.com/testrun/41728053/?legacy=true>41728053</a>, <a href=https://cat.eng.vmware.com/testrun/41742096/?legacy=true>41742096</a>, <a href=https://cat.eng.vmware.com/testrun/41724315/?legacy=true>41724315</a>, <a href=https://cat.eng.vmware.com/testrun/41727915/?legacy=true>41727915</a>, <a href=https://cat.eng.vmware.com/testrun/41734608/?legacy=true>41734608</a>, <a href=https://cat.eng.vmware.com/testrun/41748669/?legacy=true>41748669</a>, <a href=https://cat.eng.vmware.com/testrun/41747508/?legacy=true>41747508</a>, <a href=https://cat.eng.vmware.com/testrun/41742723/?legacy=true>41742723</a>, <a href=https://cat.eng.vmware.com/testrun/41710782/?legacy=true>41710782</a>, <a href=https://cat.eng.vmware.com/testrun/41749776/?legacy=true>41749776</a>, <a href=https://cat.eng.vmware.com/testrun/41748249/?legacy=true>41748249</a>, <a href=https://cat.eng.vmware.com/testrun/41739489/?legacy=true>41739489</a>'], ['<a href=https://bugzilla.eng.vmware.com/show_bug.cgi?id=1787143>PR1787143</a> ', ' vmcore-main:obj', 13, '<a href=https://cat.eng.vmware.com/testrun/41727342/?legacy=true>41727342</a>, <a href=https://cat.eng.vmware.com/testrun/41713296/?legacy=true>41713296</a>, <a href=https://cat.eng.vmware.com/testrun/41712225/?legacy=true>41712225</a>, <a href=https://cat.eng.vmware.com/testrun/41707743/?legacy=true>41707743</a>, <a href=https://cat.eng.vmware.com/testrun/41737617/?legacy=true>41737617</a>, <a href=https://cat.eng.vmware.com/testrun/41723112/?legacy=true>41723112</a>, <a href=https://cat.eng.vmware.com/testrun/41716512/?legacy=true>41716512</a>, <a href=https://cat.eng.vmware.com/testrun/41723100/?legacy=true>41723100</a>, <a href=https://cat.eng.vmware.com/testrun/41722398/?legacy=true>41722398</a>, <a href=https://cat.eng.vmware.com/testrun/41725167/?legacy=true>41725167</a>, <a href=https://cat.eng.vmware.com/testrun/41722524/?legacy=true>41722524</a>, <a href=https://cat.eng.vmware.com/testrun/41718243/?legacy=true>41718243</a>, <a href=https://cat.eng.vmware.com/testrun/41727885/?legacy=true>41727885</a>'], ['<a href=https://bugzilla.eng.vmware.com/show_bug.cgi?id=1787441>PR1787441</a> ', ' vmcore-main:obj', 1, '<a href=https://cat.eng.vmware.com/testrun/41738334/?legacy=true>41738334</a>'], ['<a href=https://bugzilla.eng.vmware.com/show_bug.cgi?id=1747515>PR1747515</a> ', ' vmcore-main:obj', 1, '<a href=https://cat.eng.vmware.com/testrun/41723727/?legacy=true>41723727</a>'], ['<a href=https://bugzilla.eng.vmware.com/show_bug.cgi?id=1787165>PR1787165</a> ', ' vmcore-main:obj', 1, '<a href=https://cat.eng.vmware.com/testrun/41707770/?legacy=true>41707770</a>']]
    print(getBugInfo(info_list))
