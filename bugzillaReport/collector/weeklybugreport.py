import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
basicpath = os.getcwd()
import pandas as pd
from common.utils.htmlUtil import tableMsg
import datetime
import time
from matplotlib import pyplot as plt
from PIL import Image

DEFAULT_MEMBER = ['tjun', 'clarkw', 'mengjunz', 'shelleyz', 'tfaisal', 'wamy']
DEFAULT_PRODUCT = ['ESX', 'VPX', 'NSX Transfor']
DEFAULT_COLOR = '#0080FF'

def readcsv(csvname):
    pd.set_option('max_colwidth', -1)
    csvdata = pd.read_csv(csvname)
    # handle the NaN fields
    csvdata = csvdata.where(csvdata.notnull(), '')
    return csvdata

def bugid(csvdata):
    bug_id = csvdata['Bug ID']
    bug_id = bug_id.values.tolist()
    bugnumber = len(bug_id)
    return [bugnumber, bug_id]

def filterbyteammember(csvdata, picname, members = DEFAULT_MEMBER):
    csvdata_reporter = csvdata["Reporter"]
    reporter_list = csvdata_reporter.values.tolist()
    reporter_list = list(set(reporter_list))
    bugamount = []
    if sorted(reporter_list) == sorted(members):
        htmldata = ''
    else:
        for member in members:
            bugamount.append(len(csvdata.loc[csvdata["Reporter"] == member]))
        plt.xlabel('Team Member')
        plt.ylabel('Bug Amount')
        plt.ylim(0, max(bugamount) + 0.5)
        pictm = plt.bar(left=members, height=bugamount, color=DEFAULT_COLOR, width=0.5)
        for x, y in zip(members, bugamount):
            plt.text(x, y + 0.03, '%.0f' % y, ha='center', va='bottom', fontsize=10)
        plt.savefig(basicpath + picname)
        plt.close()
        img = Image.open(basicpath + picname)
        htmldata = '<img src=cid:image' + picname + ' width=' + str(img.width * 0.8) + '>'
        htmldata = '%s\n' %htmldata
    return htmldata

def filterbyreporter(csvdata, picname):
    csvdata_reporter = csvdata["Reporter"]
    reporter_list = csvdata_reporter.values.tolist()
    reporter_list = list(set(reporter_list))
    bugamount = []
    for reporter in reporter_list:
        bugamount.append(len(csvdata.loc[csvdata["Reporter"] == reporter]))
    plt.xlabel('Reporter')
    plt.ylabel('Bug Amount')
    plt.ylim(0, max(bugamount) + 0.5)
    picr = plt.bar(left=reporter_list, height=bugamount, color=DEFAULT_COLOR, width=0.3)
    for x, y in zip(reporter_list, bugamount):
        plt.text(x, y + 0.03, str(y), ha='center', fontsize=10)
    plt.savefig(basicpath + picname)
    plt.close()
    img = Image.open(basicpath + picname)
    htmldata = '<img src=cid:image' + picname + ' width=' + str(img.width * 0.8) + '>'
    return '%s\n' %htmldata

def filterbytime(csvdata, picname, column):
    csvdata_time = csvdata.loc[~(csvdata[column] == '')]
    csvdata_time = csvdata_time[column]
    time_list = csvdata_time.values.tolist()
    time_list = list(set(time_list))
    bugamount = []
    for time in time_list:
        bugamount.append(len(csvdata.loc[csvdata[column] == time]))
    plt.xlabel('Time Expense(days)')
    plt.ylabel('Bug Amount')
    plt.ylim(0, max(bugamount) + 0.5)
    picr = plt.bar(left=map(str, time_list), height=bugamount, color=DEFAULT_COLOR, width=0.3)
    for x, y in zip(map(str, time_list), bugamount):
        plt.text(x, y + 0.03, str(y), ha='center', fontsize=10)
    plt.savefig(basicpath + picname)
    plt.close()
    img = Image.open(basicpath + picname)
    htmldata = '<img src=cid:image' + picname + ' width=' + str(img.width * 0.8) + '>'
    return '%s\n' %htmldata

def filterbyproduct(csvdata, picname, products = DEFAULT_PRODUCT):
    bugamount = []
    otherbug = len(csvdata["Product"])
    for product in products:
        bugnum = len(csvdata.loc[csvdata["Product"] == product])
        bugamount.append(bugnum)
        otherbug -= bugnum
    products.append('Other Product')
    bugamount.append(otherbug)
    plt.xlabel('Products')
    plt.ylabel('Bug Amount')
    plt.ylim(0, max(bugamount) + 0.5)
    picr = plt.bar(left=products, height=bugamount, color=DEFAULT_COLOR, width=0.3)
    for x, y in zip(products, bugamount):
        plt.text(x, y + 0.03, str(y), ha='center', fontsize=10)
    plt.savefig(basicpath + picname)
    plt.close()
    img = Image.open(basicpath + picname)
    htmldata = '<img src=cid:image' + picname + ' width=' + str(img.width * 0.8) + '>'
    return '%s\n' %htmldata

def filterbycomponent(csvdata, picname, product):
    bugamount = []
    lable = []
    bugs = csvdata.loc[csvdata['Product'] == product]
    components = {}
    for component in bugs['Component']:
        if component not in components:
            components[component] = 1
        else:
            components[component] += 1
    for key in components:
        bugamount.append(components[key])
        lable.append(key + '(' + str(components[key]) + ')')
    plt.figure(figsize=(6.7, 4.8))
    colors = ['#24A8D3', '#AEC9D2', '#004F7B', '#A7D2E8', '#E6EAEA']
    plt.pie(bugamount,labels=lable,colors=colors,labeldistance=1.1,autopct='%3.2f%%',shadow=False,
                                    startangle=90,pctdistance=0.6)
    plt.axis('equal')
    plt.savefig(basicpath + picname)
    plt.close()
    img = Image.open(basicpath + picname)
    htmldata = '<img src=cid:image' + picname + ' width=' + str(img.width * 0.8) + '>'
    return '%s\n' %htmldata

def filterbyresult(csvdata, picname):
    results = ['Opened', 'Resolved', 'Closed']
    bugamount = []
    all_num = len(csvdata["Status"])
    res_num = len(csvdata.loc[csvdata["Status"] == 'resolved'])
    clo_num = len(csvdata.loc[csvdata["Status"] == 'closed'])
    bugamount.append(all_num - res_num - clo_num)
    bugamount.append(res_num)
    bugamount.append(clo_num)
    plt.xlabel('Resolution')
    plt.ylabel('Bug Amount')
    plt.ylim(0, max(bugamount) + 0.5)
    picr = plt.bar(left=results, height=bugamount, color=DEFAULT_COLOR, width=0.3)
    for x, y in zip(results, bugamount):
        plt.text(x, y + 0.03, str(y), ha='center', fontsize=10)
    plt.savefig(basicpath + picname)
    plt.close()
    img = Image.open(basicpath + picname)
    htmldata = '<img src=cid:image' + picname + ' width=' + str(img.width * 0.8) + '>'
    return '%s\n' %htmldata

def filterbyresolution(csvdata, picname, status):
    bugamount = []
    lable = []
    bugs = csvdata.loc[csvdata['Status'] == status]
    resolutions = {}
    for resolution in bugs['Resolution']:
        if resolution not in resolutions:
            resolutions[resolution] = 1
        else:
            resolutions[resolution] += 1
    for key in resolutions:
        bugamount.append(resolutions[key])
        lable.append(key + '(' + str(resolutions[key]) + ')')
    colors = ['#24A8D3', '#AEC9D2', '#004F7B', '#A7D2E8', '#E6EAEA']
    plt.pie(bugamount,labels=lable,colors=colors,labeldistance=1.1,autopct='%3.2f%%',shadow=False,
                                    startangle=90,pctdistance=0.6)
    plt.axis('equal')
    plt.savefig(basicpath + picname)
    plt.close()
    img = Image.open(basicpath + picname)
    htmldata = '<img src=cid:image' + picname + ' width=' + str(img.width * 0.8) + '>'
    return '%s\n' %htmldata

def filterbydate(csvdata, picname):
    results = ['Today', 'This week', 'This month']
    opendate = csvdata['Creation Date'].values.tolist()
    time_format = '%Y-%m-%d'
    today = datetime.date.today()
    tdelta = today.weekday()
    today = datetime.datetime.strptime(str(today), time_format)
    Mondaydate = today - datetime.timedelta(days=tdelta)
    Monthnum = today.month
    todaybug, weekbug, monthbug = 0, 0, 0
    for date in opendate:
        date = time.strptime(date, '%Y-%m-%d %H:%M:%S')
        date = time.strftime(time_format, date)
        date = datetime.datetime.strptime(date, time_format)
        if date == today:
            todaybug += 1
        if (date - Mondaydate).days >=0 and (date - Mondaydate).days < 7:
            weekbug += 1
        if date.month == Monthnum:
            monthbug += 1
    bugamount = [todaybug, weekbug, monthbug]

    plt.xlabel('Date Range')
    plt.ylabel('Bug Amount')
    plt.ylim(0, max(bugamount) + 0.5)
    picd = plt.bar(left=results, height=bugamount, color=DEFAULT_COLOR, width=0.3)
    for x, y in zip(results, bugamount):
        plt.text(x, y + 0.03, '%.0f' % y, ha='center', va='bottom', fontsize=10)
    plt.savefig(basicpath + picname)
    plt.close()
    img = Image.open(basicpath + picname)
    htmldata = '<img src=cid:image' + picname + ' width=' + str(img.width * 0.8) + '>'
    return '%s\n' %htmldata

def filterbycategory(csvdata, picname):
    xaxis = ['Product', 'TDS', 'Automation']
    allbug = len(csvdata['Product'])
    internalbug = len(csvdata.loc[csvdata['Product'] == 'Internal'])
    bugamount = []
    bugamount.append(allbug-internalbug)
    bugamount.append(len(csvdata.loc[(csvdata['Product'] == 'Internal') & (csvdata['Category'] == 'TDS')]))
    bugamount.append(len(csvdata.loc[(csvdata['Product'] == 'Internal') & (csvdata['Category'] == 'Tests')
                         & (csvdata['Component'] == 'ST Automation - SW Defined Network')]))
    plt.xlabel('Category')
    plt.ylabel('Bug Amount')
    plt.ylim(0, max(bugamount) + 0.5)
    picd = plt.bar(left=xaxis, height=bugamount, color=DEFAULT_COLOR, width=0.3)
    for x, y in zip(xaxis, bugamount):
        plt.text(x, y + 0.03, '%.0f' % y, ha='center', va='bottom', fontsize=10)
    plt.savefig(basicpath + picname)
    plt.close()
    img = Image.open(basicpath + picname)
    htmldata = '<img src=cid:image' + picname + ' width=' + str(img.width * 0.8) + '>'
    return '%s\n' %htmldata

def generatehtml(csvdata):
    csvdata = csvdata.values.tolist()
    htmldata = tableMsg(csvdata)
    with open('test.html','w') as html_file:
        html_file.write(htmldata)
    return htmldata

if __name__ == '__main__':
    csvdata = readcsv('test_week.csv')
    picname = 'test.png'
    members = DEFAULT_MEMBER
    filterbycomponent(csvdata, picname, 'ESX')
    htmldata = filterbydate(csvdata, picname)
    with open('test.html','w') as html_file:
        html_file.write(htmldata)
