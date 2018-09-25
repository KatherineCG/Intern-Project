import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import bz
import csv
import bugdata as bd
import datetime
import time
from common.utils.htmlUtil import genHyperLink

TODAY = datetime.datetime.now()
DEFAULT_BUGCOLUMN = 'bug_id,priority,bug_status,assigned_to,reporter,category,' \
                    'component,found_in,fix_by,cf_type,cf_eta,short_desc,creation_ts,product,keywords,resolution'
DEFAULT_NAMES = {'ColumnA':'Bug ID', 'ColumnB':'Creation Date', 'ColumnC':'Priority', 'ColumnD':'Status', 'ColumnE':'Assigned To',
                 'ColumnF':'Reporter','ColumnG':'Category', 'ColumnH':'Component', 'ColumnJ':'Bug Type', 'ColumnK':'Found In',
                 'ColumnI':'Fix By', 'ColumnL':'ETA','ColumnM':'Summary','ColumnN':'Resolved Date','ColumnO':'Closed Date',
                 'ColumnP':'Time expense (opened)','ColumnQ':'Time expense (opened -> resolved)',
                 'ColumnR':'Time expense (resolved -> closed)', 'ColumnS':'Product','ColumnT': 'buglink','ColumnU':'Keywords',
                 'ColumnV':'Resolution'}

class Weekly_Bug:
    def bug_data(self, bugidlist, tdelta, bugcolumn = DEFAULT_BUGCOLUMN):
        bugsdata = []
        for id in bugidlist:
            argv_openbug = ['-w', bugcolumn, str(id)]
            args = bz.parse_options(argv_openbug)
            bugzilla_url = bz.options.bugzilla_url

            bd_bug = bd.Bug()
            cookie_file = bd_bug.cookie_file()
            server = bz.BugzillaServer(bugzilla_url, cookie_file, bz.options)
            server.login()

            bug_id = args[0]
            regular_bugdata = {}
            bugdata = server.show_bug(bug_id, regular_bugdata)
            link = 'https://bugzilla.eng.vmware.com/show_bug.cgi?id=' + str(bugdata['Bug ID'])
            bugdata['buglink'] = genHyperLink(str(bugdata['Bug ID']), link)
            time_format = '%Y-%m-%d %H:%M:%S'
            create_time = time.strptime(bugdata['Creation Date'], '%Y.%m.%d %H:%M:%S')
            create_time = time.strftime(time_format, create_time)
            create_time = datetime.datetime.strptime(create_time, time_format)
            bugdata['Creation Date'] = create_time

            report_time = datetime.datetime.now()
            if (report_time - create_time).days > tdelta:
                break
            if bugdata['Status'] != 'resolved' and bugdata['Status'] != 'closed':
                openeddelta = TODAY - create_time
                bugdata['Time expense (opened)'] = openeddelta.days

            #resolved date and closed date
            ori_bugata = server.original_bugdata(bug_id)
            if ori_bugata.has_key('comments'):
                for comment in ori_bugata['comments']:
                    for comment_ in comment['activity']:
                        if comment_['what'] == 'Status':
                            if comment_['added'] == 'resolved':
                                bugdata['Resolved Date'] = comment_['time']
                                resolved_time = datetime.datetime.strptime(bugdata['Resolved Date'], time_format)
                                tdelta_ = resolved_time - create_time
                                time_expense = tdelta_.days
                                bugdata['Time expense (opened -> resolved)'] = time_expense
                            if comment_['added'] == 'closed':
                                bugdata['Closed Date'] = comment_['time']
                                closed_time = datetime.datetime.strptime(bugdata['Closed Date'], time_format)
                                tdelta_ = closed_time - resolved_time
                                time_expense = tdelta_.days
                                bugdata['Time expense (resolved -> closed)'] = time_expense
            bugsdata.append(bugdata)
        return bugsdata

    def write_csv(self, bugsdata, bugfilename, names = DEFAULT_NAMES):
        fileobj = open(bugfilename, 'wb')
        writer = csv.writer(fileobj)

        bd_bug = bd.Bug()
        SortedValues = bd_bug.getSortedValues(names)
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
            SortedValues = bd_bug.getSortedValues(bugdata_new)
            writer.writerow(SortedValues)
        return

bug = Weekly_Bug()

def main(args, bugfilename, tdelta):
    bd_bug = bd.Bug()
    buglist = bd_bug.buglist(args)[::-1]
    bugsdata = bug.bug_data(buglist, tdelta)
    bug.write_csv(bugsdata, bugfilename)

if __name__ == '__main__':
    args = ['-q', '', '']
    bugfilename = 'test_week.csv'
    main(args, bugfilename, 30)