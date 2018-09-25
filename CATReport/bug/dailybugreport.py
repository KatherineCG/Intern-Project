import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import pandas as pd
from Common.utils.htmlUtil import tableMsg

DEFAULT_COLUMN = ['Bug ID', 'Creation Date', 'Priority', 'Status', 'Assigned To','Reporter','Category', 'Component', 'Bug Type', 'Found In',
                 'Fix By', 'ETA','Summary']
def csvread(csvname):
    pd.set_option('max_colwidth', -1)
    csvdata = pd.read_csv(csvname)
    # handle the NaN fields
    csvdata = csvdata.where(csvdata.notnull(), '')
    return csvdata

def filterproductbug(csvname, column):
    csvdata = csvread(csvname)
    csvdata = csvdata.loc[~(csvdata['Product'] == 'Internal')]
    csvdata = csvdata.reset_index(drop=True)
    bugnumber = len(csvdata)
    if bugnumber == 0:
        htmldata = ''
    else:
        htmldata = generatehtml(csvdata, columnname=column)
    return [bugnumber, htmldata]

def filterautomationbug(csvname, column):
    csvdata = csvread(csvname)
    csvdata = csvdata.loc[(csvdata['Product'] == 'Internal') & (csvdata['Category'] == 'Tests') &
                          (csvdata['Component'] == 'ST Automation - SW Defined Network')]
    csvdata = csvdata.reset_index(drop=True)
    bugnumber = len(csvdata)
    if bugnumber == 0:
        htmldata = ''
    else:
        htmldata = generatehtml(csvdata, columnname=column)
    return [bugnumber, htmldata]

def filtertdsbug(csvname,column):
    csvdata = csvread(csvname)
    csvdata = csvdata.loc[(csvdata['Product'] == 'Internal') & (csvdata['Category'] == 'TDS')]
    csvdata = csvdata.reset_index(drop=True)
    bugnumber = len(csvdata)
    if bugnumber == 0:
        htmldata = ''
    else:
        htmldata = generatehtml(csvdata, columnname=column)
    return [bugnumber, htmldata]

def filterstatus(csvname,column):
    csvdata = csvread(csvname)
    csvdata = csvdata.loc[(csvdata['Status'] == 'resolved') & ~(csvdata['Status'] == 'closed')]
    csvdata = csvdata.reset_index(drop=True)
    bugnumber = len(csvdata)
    if bugnumber == 0:
        htmldata = ''
    else:
        redcsvdata = csvdata.loc[csvdata['Time expense (resolved)'] > 3]
        redcsvdata = redcsvdata['Bug ID']
        redlinedata = redcsvdata.values.tolist()
        if redlinedata != []:
            rednote = 'Bug resolved over 3 days.'
        else:
            rednote = None
        htmldata = generatehtml(csvdata, redlinedata, rednote=rednote, columnname=column)
    return [bugnumber, htmldata]

def duplicatedbug(csvname, column):
    csvdata = csvread(csvname)
    csvdata = csvdata.loc[~(csvdata['Duplicate'] == '')]
    bugnumber = len(csvdata)
    if bugnumber == 0:
        htmldata = ''
    else:
        redlinedata = csvdata.loc[csvdata['dup_product'] == '']
        redlinedata = redlinedata['Bug ID']
        redlinedata = redlinedata.values.tolist()
        orangelinedata = csvdata.loc[~(csvdata['Status'] == 'resolved') & ~(csvdata['Status'] == 'closed')]
        orangelinedata = orangelinedata['Bug ID']
        orangelinedata = orangelinedata.values.tolist()
        if redlinedata != []:
            rednote = 'Original bug and dup bug are not in the same product.'
        else:
            rednote = None
        if orangelinedata != []:
            orangenote = 'Dup bug is not fixed.'
        else:
            orangenote = None
        htmldata = generatehtml(csvdata, redlinedata, orangelinedata, rednote, orangenote, column)
    return [bugnumber, htmldata]

def generatehtml(csvdata, redlindata = [], orangelinedata = [], rednote=None, orangenote=None,columnname = DEFAULT_COLUMN):
    result = [columnname]
    csvdata = csvdata[columnname]
    csvdata = csvdata.values.tolist()
    result += csvdata
    htmldata = tableMsg(result, redlineInfo = redlindata, orangelineInfo = orangelinedata, rednote = rednote, orangenote = orangenote)
    return htmldata

if __name__ == '__main__':
    #csvdata = csvread('test.csv')
    print filterstatus('dailybug.csv')
