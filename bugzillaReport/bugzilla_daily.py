import sys
import os
basicpath = os.getcwd()

from datetime import datetime
from optparse import OptionParser
from common.utils.emailUtil import sendEmail
from common.utils.logger import getLogger
from common.utils.htmlUtil import getHtmlTitle, colorMsg, boldMsg
import collector.dailybugreport as dr
import collector.bugdata as bd

logger = getLogger()
DEFAULT_USER = ''
DEFAULT_QUERY = ''
DEFAULT_BLOCKER_QUERY = ''
DEFAULT_COLUMN = {'Bug ID': 'bug_id', 'Creation Date': 'creation_date', 'Priority': 'priority', 'Status': 'status',
                  'Assigned To': 'assignee','Reporter': 'reporter','Category': 'catetory', 'Component': 'component',
                  'Bug Type':'bug_type', 'Found In':'found_in','Fix By':'fix_by', 'ETA':'ETA','Summary':'summary'}
DEFAULT_TOLIST = []
DEFAULT_CCLIST = []
options = None

def blockerbug(args, column):
    args = ['-q'] + args
    bugfilename = basicpath + r'\csvdata\blockerbug.csv'
    bd.main(args, bugfilename)
    csvdata = dr.csvread(bugfilename)
    bugnumber = len(csvdata)
    if bugnumber == 0:
        htmldata = ''
    else:
        csvdatalist = csvdata.values.tolist()
        redlinedata = []
        for data in csvdatalist:
            keywordslist = data[-2].split(',')
            if 'TestBlocker' in keywordslist:
                redlinedata.append(data[0])
        if redlinedata != []:
            rednote = "Bug's keywords contain 'Test-Blocker'"
        else:
            rednote = None
        htmldata = dr.generatehtml(csvdata, redlinedata, rednote=rednote, columnname=column)
    return [bugnumber, htmldata]

def list_columns():
    columns = DEFAULT_COLUMN
    print "_" * 45
    print "| %s | %s|" % ('Name'.ljust(20), 'Description'.ljust(20))
    print "|" + "-" * 43 + "|"
    for column in columns:
        print "| %s| %s|" % (columns[column].ljust(20), column.ljust(20))
    print "|" + "-" * 43+ "|"

def parse_options(args):
    parser = OptionParser(usage="%prog [-l] [-q|b] [user query] [-c] [column names] [--to] [email to list] [--cc] [email cc list]")
    parser.add_option("-q", "--query",
                      action="store", dest="query",
                      type="string",help="comma-separated user and query of bugs")
    parser.add_option("-b", "--blockerquery",
                      action="store", dest="blockerquery",
                      type="string", help="comma-separated user and query of blocker bug")
    parser.add_option("-l", "--listcolumns",
                      action="store_true", dest="listcolumns", default=False,
                      help="list available bug columns")
    parser.add_option("-c", "--columns",
                      action="store", dest="columns",
                      help="comma-separated list of bug columns to display",
                      type="string")
    parser.add_option("--to", "--emailToList",
                      action="store", dest="emailToList", default=DEFAULT_TOLIST,
                      help="comma-separated list of toUser email address",
                      type="string")
    parser.add_option("--cc", "--ccUserList",
                      action="store", dest="ccUserList", default=DEFAULT_CCLIST,
                      help="comma-separated list of CCUser email address",
                      type="string")

    (globals()["options"], args) = parser.parse_args(args)

def main(args):
    query = [DEFAULT_USER, DEFAULT_QUERY]
    blockerquery = [DEFAULT_USER, DEFAULT_BLOCKER_QUERY]
    column = dr.DEFAULT_COLUMN
    emailToList = DEFAULT_TOLIST
    ccUserList = DEFAULT_CCLIST

    args = parse_options(args)
    if options.listcolumns:
        list_columns()
        sys.exit(0)
    if options.query:
        query = options.query
        query = query.split(',')
    if options.blockerquery:
        blockerquery = options.blockerquery
        blockerquery = blockerquery.split(',')
    if options.columns:
        keys = options.columns
        coldict = {v: k for k, v in DEFAULT_COLUMN.items()}
        keys = keys.split(',')
        column = []
        for key in keys:
            column.append(coldict[key])
    if options.emailToList != emailToList:
        emailToList = options.emailToList
        emailToList = emailToList.split(',')
    if options.ccUserList != ccUserList:
        ccUserList = options.ccUserList
        ccUserList = ccUserList.splilt(',')

    args = ['-q'] + query
    bugfilename = basicpath + '\csvdata\dailybug.csv'
    bd.main(args, bugfilename)

    time_format = '%Y-%m-%d %H:%M:%S'
    report_time = datetime.now()

    sub_report = []
    sub_report.append(getHtmlTitle('Bugzilla Daily Report' + '  ' + report_time.strftime(time_format)))
    productbug = dr.filterproductbug(bugfilename, column)
    sub_report.append(colorMsg(boldMsg('Opened bug ---Product (Bug Number:' + str(productbug[0]) + ')', 4.5), 'blue'))
    sub_report.append(productbug[1])
    automationbug = dr.filterautomationbug(bugfilename, column)
    sub_report.append(colorMsg(boldMsg('Opened bug ---Automation (Bug Number:' + str(automationbug[0]) + ')', 4.5), 'blue'))
    sub_report.append(automationbug[1])
    tdsbug = dr.filtertdsbug(bugfilename, column)
    sub_report.append(colorMsg(boldMsg('Opened bug ---TDS (Bug Number:' + str(tdsbug[0]) + ')', 4.5), 'blue'))
    sub_report.append(tdsbug[1])
    bbug = blockerbug(blockerquery, column)
    sub_report.append(colorMsg(boldMsg('Blocker bug (Bug Number:' + str(bbug[0]) + ')', 4.5), 'blue'))
    sub_report.append(bbug[1])
    statusbug = dr.filterstatus(bugfilename, column)
    sub_report.append(colorMsg(boldMsg('Resolved but not closed bug (Bug Number:' + str(statusbug[0]) + ')', 4.5), 'blue'))
    sub_report.append(statusbug[1])
    dupcolumn = column + ['Duplicate']
    dupbug = dr.duplicatedbug(bugfilename, dupcolumn)
    sub_report.append(colorMsg(boldMsg('Duplicated bug (Bug Number:' + str(dupbug[0]) + ')', 4.5), 'blue'))
    sub_report.append(dupbug[1])

    overall_output = "<br><br>".join(sub_report)
    # Send out the report
    area_subject = "Bugzilla Daily Report"
    mail_subject = ("[%s][%s]" % (area_subject,
                                  report_time.strftime(time_format)))
    sendEmail(mail_subject, overall_output, None, None, emailToList, sender='bugzilla_reporter@vmware.com',ccUser=ccUserList)

if __name__ == '__main__':
    main(sys.argv[1:])

