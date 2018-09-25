import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from Common.utils.logger import getLogger
from Common.utils.htmlUtil import colorMsg, boldMsg
import dailybugreport as dr

logger = getLogger()
DEFAULT_COLUMN = {'Bug ID': 'bug_id', 'Creation Date': 'creation_date', 'Priority': 'priority', 'Status': 'status',
                  'Assigned To': 'assignee','Reporter': 'reporter','Category': 'catetory', 'Component': 'component',
                  'Bug Type':'bug_type', 'Found In':'found_in','Fix By':'fix_by', 'ETA':'ETA','Summary':'summary'}
options = None

def list_columns():
    columns = DEFAULT_COLUMN
    print "_" * 45
    print "| %s | %s|" % ('Name'.ljust(20), 'Description'.ljust(20))
    print "|" + "-" * 43 + "|"
    for column in columns:
        print "| %s| %s|" % (columns[column].ljust(20), column.ljust(20))
    print "|" + "-" * 43+ "|"

def main():
    column = dr.DEFAULT_COLUMN
    bugfilename = 'bug.csv'
    sub_report = []
    productbug = dr.filterproductbug(bugfilename, column)
    sub_report.append(colorMsg(boldMsg('Opened bug ---Product (Bug Number:' + str(productbug[0]) + ')', 4.5), 'blue'))
    sub_report.append(productbug[1])
    automationbug = dr.filterautomationbug(bugfilename, column)
    sub_report.append(colorMsg(boldMsg('Opened bug ---Automation (Bug Number:' + str(automationbug[0]) + ')', 4.5), 'blue'))
    sub_report.append(automationbug[1])
    tdsbug = dr.filtertdsbug(bugfilename, column)
    sub_report.append(colorMsg(boldMsg('Opened bug ---TDS (Bug Number:' + str(tdsbug[0]) + ')', 4.5), 'blue'))
    sub_report.append(tdsbug[1])
    statusbug = dr.filterstatus(bugfilename, column)
    sub_report.append(colorMsg(boldMsg('Resolved but not closed bug (Bug Number:' + str(statusbug[0]) + ')', 4.5), 'blue'))
    sub_report.append(statusbug[1])
    dupcolumn = column + ['Duplicate']
    dupbug = dr.duplicatedbug(bugfilename, dupcolumn)
    sub_report.append(colorMsg(boldMsg('Duplicated bug (Bug Number:' + str(dupbug[0]) + ')', 4.5), 'blue'))
    sub_report.append(dupbug[1])
    overall_output = "<br><br>".join(sub_report)
    return overall_output

if __name__ == '__main__':
    main()

