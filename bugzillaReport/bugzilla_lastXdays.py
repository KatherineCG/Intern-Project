import sys
import os
basicpath = os.getcwd()

import matplotlib
matplotlib.use('Agg')

from datetime import datetime, timedelta
from optparse import OptionParser
from common.utils.emailUtil import sendEmail
from common.utils.logger import getLogger
from common.utils.htmlUtil import getHtmlTitle, colorMsg, boldMsg, genHyperLink
import collector.weeklybugreport as wr
import collector.weekly_bugdata as w_bd
options = None

logger = getLogger()

DEFAULT_USER = ''
DEFAULT_QUERY = ''
DEFAULT_TDELTA = 30
DEFAULT_TOLIST = []
DEFAULT_CCLIST = []

def allbugdata(args, tdelta):
    args = ['-q'] + args
    bugfilename = basicpath + '/csvdata/weeklybug.csv'
    w_bd.main(args, bugfilename, tdelta)
    return bugfilename

def buglink(bugidlist):
    bugidlist = map(str, bugidlist)
    bugid = ','.join(bugidlist)
    content = 'All bugs link'
    link = 'https://bugzilla.eng.vmware.com/buglist.cgi?query_format=advanced&bug_status=unreviewed&bug_status=new&bug_status=assigned' \
           '&bug_status=reopened&bug_status=resolved&bug_status=closed&chfieldto=Now&bugidtype=include&bug_id=' \
            + bugid + \
           '&cmdtype=doit&backButton=false'
    return genHyperLink(content, link)

def parse_options(args):
    parser = OptionParser(usage="%prog [-b] [user query] [--td] [time delta] [-m] [member list] [--pl] [product list] "
                                "[--to] [email to list] [--cc] [email cc list] [-a|o|f|c|r|x|p|ce|cv|s|rr|rc|d|t]")
    parser.add_option("-b", "--bugquery",
                      action="store", dest="bugquery",
                      type="string",help="comma-separated user and query of bug")
    parser.add_option("--td", "--tdelta",
                      action="store", dest="tdelta", default=30,
                      type="int", help="time delta from start to end")
    parser.add_option("-m", "--members",
                      action="store", dest="members",
                      type="string", help="comma-separated team member")
    parser.add_option("--pl", "--products",
                      action="store", dest="products", default=wr.DEFAULT_PRODUCT,
                      type="string", help="shown product list")
    parser.add_option("--to", "--emailToList",
                      action="store", dest="emailToList", default=DEFAULT_TOLIST,
                      help="comma-separated list of toUser email address",
                      type="string")
    parser.add_option("--cc", "--ccUserList",
                      action="store", dest="ccUserList", default=DEFAULT_CCLIST,
                      help="comma-separated list of CCUser email address",
                      type="string")
    parser.add_option("-a", "--allbugslink",
                      action="store_true", dest="allbugslink", default=False,
                      help="all bugs link")
    parser.add_option("-o", "--openedduration",
                      action="store_true", dest="openedduration", default=False,
                      help="duration of opened bugs")
    parser.add_option("-f", "--fixbugstime",
                      action="store_true", dest="fixbugstime", default=False,
                      help="time expense of fix bugs")
    parser.add_option("-c", "--closebugstime",
                      action="store_true", dest="closebugtime", default=False,
                      help="time expense of close bugs")
    parser.add_option("-r", "--reporter",
                      action="store_true", dest="reporter", default=False,
                      help="every reporter's bug amount")
    parser.add_option("-x", "--category",
                      action="store_true", dest="category", default=False,
                      help="automation/TDS/product bug amount")
    parser.add_option("-p", "--product",
                      action="store_true", dest="product", default=False,
                      help="every product's bug amount")
    parser.add_option("--ce", "--component(ESX)",
                      action="store_true", dest="component(ESX)", default=False,
                      help="ESX every component's bug amount")
    parser.add_option("--cv", "--component(VPX)",
                      action="store_true", dest="component(VPX)", default=False,
                      help="VPX every component's bug amount")
    parser.add_option("-s", "--status",
                      action="store_true", dest="status", default=False,
                      help="every status's bug amount")
    parser.add_option("--rr", "--resolution(resolved)",
                      action="store_true", dest="resolution(resolved)", default=False,
                      help="resolved every resolution's bug amount")
    parser.add_option("--rc", "--resolution(closed)",
                      action="store_true", dest="resolution(closed)", default=False,
                      help="closed every resolution's bug amount")
    parser.add_option("-d", "--datedelta",
                      action="store_true", dest="datedelta", default=False,
                      help="every date delta's bug amount")
    parser.add_option("-t", "--teammembers",
                      action="store_true", dest="teammembers", default=False,
                      help="every team member's bug amount")
    (globals()["options"], args) = parser.parse_args(args)

def main(args):
    tdelta = DEFAULT_TDELTA
    members = wr.DEFAULT_MEMBER
    bugquery = [DEFAULT_USER, DEFAULT_QUERY]
    products = wr.DEFAULT_PRODUCT
    emailToList = DEFAULT_TOLIST
    ccUserList = DEFAULT_CCLIST
    openimg = os.sep + 'pic' + os.sep + 'openimg.png'
    resolvedimg = os.sep + 'pic' + os.sep + 'resolvedimg.png'
    closedimg = os.sep + 'pic' + os.sep + 'closedimg.png'
    reporterimg = os.sep + 'pic' + os.sep + 'reporter.png'
    categoryimg = os.sep + 'pic' + os.sep + 'category.png'
    productimg = os.sep + 'pic' + os.sep + 'product.png'
    componentesximg = os.sep + 'pic' + os.sep + 'esx.png'
    componentvpximg = os.sep + 'pic' + os.sep + 'vpx.png'
    statusimg = os.sep + 'pic' + os.sep + 'status.png'
    resolutionrimg = os.sep + 'pic' + os.sep + 'resolved.png'
    resolutioncimg = os.sep + 'pic' + os.sep + 'closed.png'
    dateimg = os.sep + 'pic' + os.sep + 'date.png'
    teammemberimg = os.sep + 'pic' + os.sep + 'teamimg.png'
    options_attributes = ['allbugslink', 'openedduration', 'category', 'closebugtime', 'datedelta', 'fixbugstime',
                          'product', 'reporter', 'status', 'teammembers', 'component(ESX)', 'component(VPX)',
                          'resolution(resolved)', 'resolution(closed)']
    args = parse_options(args)
    if options.bugquery:
        bugquery = options.bugquery
        bugquery = bugquery.split(',')
    if options.tdelta:
        tdelta = options.tdelta
    if options.members:
        members = options.members
        members = members.split(',')
    if options.products != products:
        products = options.products
        products = products.split(',')
    if options.emailToList != emailToList:
        emailToList = options.emailToList
        emailToList = emailToList.split(',')
    if options.ccUserList != ccUserList:
        ccUserList = options.ccUserList
        ccUserList = ccUserList.splilt(',')
    store_true_optins = {}
    for attribute in options_attributes:
        store_true_optins[attribute] = getattr(options, attribute)
    if list(set(store_true_optins.values())) == [False]:
        keys = store_true_optins.keys()
        for key in keys:
            store_true_optins[key] = True
    time_format = '%Y.%m.%d'
    report_time = datetime.now()
    report_time = report_time.strftime(time_format)
    start_time = datetime.strptime(report_time, time_format) - timedelta(days=tdelta)

    bugfilename = allbugdata(bugquery, tdelta)
    csvdata = wr.readcsv(bugfilename)
    bugnumber = wr.bugid(csvdata)[0]
    buglist = wr.bugid(csvdata)[1]

    sub_report = []
    images = []
    sub_report.append(getHtmlTitle(
        'Bugzilla Report' + '  ' + start_time.strftime(time_format) + ' - ' + report_time))
    if store_true_optins['allbugslink']:
        sub_report.append(colorMsg(boldMsg('Link to all the bugs (Bug Number:' + str(bugnumber) + ')', 4.5), 'blue'))
        sub_report.append(buglink(buglist))
    if store_true_optins['openedduration']:
        openbug = wr.filterbytime(csvdata, openimg, 'Time expense (opened)')
        if openbug:
            sub_report.append(colorMsg(boldMsg('The duration of opened bugs', 4.5, True), 'blue'))
            sub_report.append(openbug)
            images.append(openimg)
    if store_true_optins['fixbugstime']:
        resolvedbug = wr.filterbytime(csvdata, resolvedimg, 'Time expense (opened -> resolved)')
        if resolvedbug:
            sub_report.append(colorMsg(boldMsg('Time expense of resolved bugs', 4.5, True), 'blue'))
            sub_report.append(resolvedbug)
            images.append(resolvedimg)
    if store_true_optins['closebugtime']:
        closebug = wr.filterbytime(csvdata, closedimg, 'Time expense (resolved -> closed)')
        if closebug:
            sub_report.append(colorMsg(boldMsg('Time expense of close bugs', 4.5, True), 'blue'))
            sub_report.append(closebug)
            images.append(closedimg)
    if store_true_optins['reporter']:
        sub_report.append(colorMsg(boldMsg('Bug distribution data', 4.5, True), 'blue'))
        sub_report.append(colorMsg(boldMsg('Reporter', 3, True), 'blue'))
        sub_report.append(wr.filterbyreporter(csvdata, reporterimg))
        images.append(reporterimg)
    if store_true_optins['category']:
        if colorMsg(boldMsg('Bug distribution data', 4.5, True), 'blue') not in sub_report:
            sub_report.append(colorMsg(boldMsg('Bug distribution data', 4.5, True), 'blue'))
        sub_report.append(colorMsg(boldMsg('Automation/TDS/Product', 3, True), 'blue'))
        sub_report.append(wr.filterbycategory(csvdata, categoryimg))
        images.append(categoryimg)
    if store_true_optins['product']:
        if colorMsg(boldMsg('Bug distribution data', 4.5, True), 'blue') not in sub_report:
            sub_report.append(colorMsg(boldMsg('Bug distribution data', 4.5, True), 'blue'))
        sub_report.append(colorMsg(boldMsg('Product', 3, True), 'blue'))
        sub_report.append(wr.filterbyproduct(csvdata, productimg, products))
        images.append(productimg)
        if 'ESX' in products:
            sub_report.append(colorMsg(boldMsg('Component(ESX)', 3, True), 'blue'))
            sub_report.append(wr.filterbycomponent(csvdata, componentesximg, 'ESX'))
            images.append(componentesximg)
        if 'VPX' in products:
            sub_report.append(colorMsg(boldMsg('Component(VPX)', 3, True), 'blue'))
            sub_report.append(wr.filterbycomponent(csvdata, componentvpximg, 'VPX'))
            images.append(componentvpximg)
    if store_true_optins['status']:
        if colorMsg(boldMsg('Bug distribution data', 4.5, True), 'blue') not in sub_report:
            sub_report.append(colorMsg(boldMsg('Bug distribution data', 4.5, True), 'blue'))
        sub_report.append(colorMsg(boldMsg('Status', 3, True), 'blue'))
        sub_report.append(wr.filterbyresult(csvdata, statusimg))
        images.append(statusimg)
    if store_true_optins['resolution(resolved)']:
        if colorMsg(boldMsg('Bug distribution data', 4.5, True), 'blue') not in sub_report:
            sub_report.append(colorMsg(boldMsg('Bug distribution data', 4.5, True), 'blue'))
        sub_report.append(colorMsg(boldMsg('Resolution(resolved)', 3, True), 'blue'))
        sub_report.append(wr.filterbyresolution(csvdata, resolutionrimg, 'resolved'))
        images.append(resolutionrimg)
    if store_true_optins['resolution(closed)']:
        if colorMsg(boldMsg('Bug distribution data', 4.5, True), 'blue') not in sub_report:
            sub_report.append(colorMsg(boldMsg('Bug distribution data', 4.5, True), 'blue'))
        sub_report.append(colorMsg(boldMsg('Resolution(closed)', 3, True), 'blue'))
        sub_report.append(wr.filterbyresolution(csvdata, resolutioncimg, 'closed'))
        images.append(resolutioncimg)
    if store_true_optins['datedelta']:
        if colorMsg(boldMsg('Bug distribution data', 4.5, True), 'blue') not in sub_report:
            sub_report.append(colorMsg(boldMsg('Bug distribution data', 4.5, True), 'blue'))
        sub_report.append(colorMsg(boldMsg('Date', 3, True), 'blue'))
        sub_report.append(wr.filterbydate(csvdata, dateimg))
        images.append(dateimg)
    if store_true_optins['teammembers']:
        teammemberbug = wr.filterbyteammember(csvdata, teammemberimg, members)
        if teammemberbug:
            sub_report.append(colorMsg(boldMsg('Bug Information', 4.5, True), 'blue'))
            sub_report.append(colorMsg(boldMsg('Team Member', 3, True), 'blue'))
            sub_report.append(teammemberbug)
            images.append(teammemberimg)
    # Send out the report
    overall_output = "<br><br>".join(sub_report)
    area_subject = "Bugzilla Report"
    mail_subject = ("[%s] from [%s] To [%s]" % (area_subject,start_time.strftime(time_format),report_time))
    sendEmail(mail_subject, overall_output, images, None, emailToList, sender='bugzilla_reporter@vmware.com', ccUser=ccUserList)

if __name__ == '__main__':
    main(sys.argv[1:])


