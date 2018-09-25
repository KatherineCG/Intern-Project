import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
basicpath = os.path.dirname(os.getcwd())

import bz
import csv
from Common.utils.htmlUtil import genHyperLink
import datetime

NOW_TIME = datetime.datetime.now()
DEFAULT_BUGCOLUMN = 'bug_id,priority,bug_status,assigned_to,reporter,category,' \
                    'component,found_in,fix_by,cf_type,cf_eta,short_desc,creation_ts,product,keywords,dup_id'

DEFAULT_CSVCOLUMN = {'ColumnA':'Bug ID', 'ColumnB':'Creation Date', 'ColumnC':'Priority', 'ColumnD':'Status', 'ColumnE':'Assigned To',
                 'ColumnF':'Reporter','ColumnG':'Category', 'ColumnH':'Component', 'ColumnJ':'Bug Type', 'ColumnK':'Found In',
                 'ColumnI':'Fix By', 'ColumnL':'ETA','ColumnM':'Summary','ColumnN':'Product','ColumnO':'Keywords',
                     'ColumnP':'Time expense (resolved)', 'ColumnQ':'Duplicate', 'ColumnR':'dup_product'}

class Bug:

    def cookie_file(self):
        if 'USERPROFILE' in os.environ:
            homepath = os.path.join(os.environ["USERPROFILE"], "Local Settings",
                                    "Application Data")
        elif 'HOME' in os.environ:
            homepath = os.environ["HOME"]
        else:
            homepath = ''

        cookie_file = os.path.join(homepath, ".bugzilla-cookies.txt")

        return cookie_file

    def buglist(self, arg):
        arg = bz.parse_options(arg)
        bugzilla_url = bz.options.bugzilla_url

        cookie_file = self.cookie_file()
        server = bz.BugzillaServer(bugzilla_url, cookie_file, bz.options)
        server.login()

        bugidlist = server.query(bz.options.query)

        return bugidlist

    def bug_data(self, bugidlist, bugcolumn = DEFAULT_BUGCOLUMN):
        bugsdata = []
        for id in bugidlist:
            argv_openbug = ['-w', bugcolumn, str(id)]
            args = bz.parse_options(argv_openbug)
            bugzilla_url = bz.options.bugzilla_url

            cookie_file = self.cookie_file()
            server = bz.BugzillaServer(bugzilla_url, cookie_file, bz.options)
            server.login()

            bug_id = args[0]
            regular_bugdata = {}
            bugdata = server.show_bug(bug_id, regular_bugdata)
            if (bugdata['Status'] == 'closed'):
                continue
            link = 'https://bugzilla.eng.vmware.com/show_bug.cgi?id=' + str(bugdata['Bug ID'])
            bugdata['Bug ID'] = genHyperLink(str(bugdata['Bug ID']), link)
            time_format = '%Y-%m-%d %H:%M:%S'
            ori_bugata = server.original_bugdata(bug_id)
            if ori_bugata.has_key('comments'):
                for comment in ori_bugata['comments']:
                    for comment_ in comment['activity']:
                        if comment_['what'] == 'Status':
                            if comment_['added'] == 'resolved':
                                bugdata['Resolved Date'] = comment_['time']
                                if bugdata['Status'] == 'resolved':
                                    resolved_time = datetime.datetime.strptime(bugdata['Resolved Date'], time_format)
                                    tdelta_ = NOW_TIME - resolved_time
                                    bugdata['Time expense (resolved)'] = tdelta_.days
            flag = False
            if bugdata.has_key('Dup_id'):
                dup_bugid = [bugdata['Dup_id']]
                # if the duplicated bug is also be duplicated
                if dup_bugid != ['']:
                    i = 0
                    duplicate = str(bug_id)
                    dup_product = bugdata['Product']
                    while i <= (len(dup_bugid) - 1):
                        dup_bug = server.original_bugdata(dup_bugid[i])
                        if dup_bug['bug_status'] != 'closed' and dup_bug['bug_status'] != 'resolved':
                            flag = True
                        elif dup_bug['bug_status'] == 'resolved':
                            dup_bug = self.bugstatusdate(dup_bug)
                            resolved_time = datetime.datetime.strptime(dup_bug['Resolved Date'], time_format)
                            tdelta = NOW_TIME - resolved_time
                            if tdelta.days <= 7:
                                flag = True
                        else:
                            dup_bug = self.bugstatusdate(dup_bug)
                            closed_time = datetime.datetime.strptime(dup_bug['Closed Date'], time_format)
                            tdelta = NOW_TIME - closed_time
                            if tdelta.days <= 7:
                                flag = True
                        if flag:
                            link = 'https://bugzilla.eng.vmware.com/show_bug.cgi?id=' + str(dup_bugid[i])
                            duplicate += '->' + genHyperLink(str(dup_bugid[i]), link) + '(' + dup_bug[
                                'bug_status'] + ')'
                            if dup_product != dup_bug['product']:
                                dup_product = ''
                            flag = False
                        if dup_bug['dup_id'] != '':
                            dup_bugid.append(dup_bug['dup_id'])
                        i += 1
                    # bugdata['Dup_id'] = dup_bugid
                    bugdata['dup_product'] = dup_product
                    if duplicate != str(bug_id):
                        bugdata['Duplicate'] = duplicate
            bugsdata.append(bugdata)
        return bugsdata

    def bugstatusdate(self, bugdata):
        if bugdata.has_key('comments'):
            for comment in bugdata['comments']:
                for comment_ in comment['activity']:
                    if comment_['what'] == 'Status':
                        if comment_['added'] == 'resolved':
                            bugdata['Resolved Date'] = comment_['time']
                        if comment_['added'] == 'closed':
                            bugdata['Closed Date'] = comment_['time']
        return bugdata

    def write_csv(self, bugsdata, bugfilename, names = DEFAULT_CSVCOLUMN):
        fileobj = open(bugfilename, 'wb')
        writer = csv.writer(fileobj)

        SortedValues = self.getSortedValues(names)
        writer.writerow(SortedValues)

        bugdata_new = {}
        for bugdata in bugsdata:
            for i in range(1,len(names)+1):
                ascii = chr(i + 64)
                key = 'Column' + "%s" %ascii
                if bugdata.has_key(names[key]):
                    bugdata_new[key] = bugdata[names[key]]
                else:
                    bugdata_new[key] = ''
            SortedValues = self.getSortedValues(bugdata_new)
            writer.writerow(SortedValues)
        return

    def getSortedValues(self, row):
        sortedValues = []
        keys = row.keys()
        keys.sort()
        for key in keys:
            sortedValues.append(row[key])
        return sortedValues

bug = Bug()
def main(buglist, bugfilename):
    bugsdata = bug.bug_data(buglist)
    bug.write_csv(bugsdata, bugfilename)
