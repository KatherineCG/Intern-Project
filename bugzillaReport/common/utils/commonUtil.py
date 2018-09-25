'''Common functions
Created on Aug 28, 2016

@author: kaiyuanli
'''

import csv
from datetime import datetime, timedelta
import getpass
import json, os, re, sys, subprocess

DATE_FORMAT_DEFAULT = '%Y-%m-%d-%H-%M-%S'
DATE_FORMAT_CAT = '%Y-%m-%dT%H:%M:%S'
DATE_FORMAT_YEAR_MONTH_DAY = '%Y-%m-%d'
DATE_FORMAT_YEARMONTHDAY = '%Y%m%d'

ALIGN_INDEX = 19

SCRIPT_PATH = os.path.join(os.getcwd(), sys.argv[0])
SCRIPT_NAME = os.path.splitext(os.path.basename(SCRIPT_PATH))[0]
ROOT_DIR = os.path.join(os.path.dirname(__file__), '..', '..')

CONFIG_ROOT_DIR = os.path.join(ROOT_DIR, 'config')
LOG_DIR = os.path.join(ROOT_DIR, 'log')
#THD_PARTH = os.path.join(ROOT_DIR, '3rdparty')

try:
   SCRIPT_USER = getpass.getuser()
except:
   SCRIPT_USER = 'kaiyuanli'
'''
try:
   # Add third party modules into python path
   for fileName in os.listdir(THD_PARTH):
      module = os.path.join(THD_PARTH, fileName)
      sys.path.append(module)
except Exception as e:
   raise Exception("Failed to add file %s into python path, please manually "
                   " add it first")
'''

#---------------------------
# Common operation libraries
#---------------------------
def runCommand(cmd):
   p = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE)
   o, e = p.communicate()
   return p.returncode, o , e

#-----------------------
# math related libraries
#-----------------------
def getPercentage(num, total):
   try:
      ratio = float(num) / float(total)
      return '%0.02f%%' % (ratio * 100)
   except:
      return 'N/A'


#----------------------------
# list/dict related libraries
#----------------------------
def insertIndex2List(infoList):
   """
   Insert index to each info in infoList, e.g.
   Input infoList: [['a', 'b', 'c'], ['d', 'e', 'f']]
   Manipulate this infoList to [['1', 'a', 'b', 'c'], ['2', 'd', 'e', 'f']]
   
   @infoList: a 2d list
   """
   assert(isinstance(infoList, list))
   for i in range(len(infoList)):
      info = infoList[i]
      assert(isinstance(info, list))
      info.insert(0, str(i + 1))

def getValueFromInfoDict(infoDict, k, default=None, required=True):
   """Return k's value in infoDict

   If required is True, raise exception if k not exist in infoDict
   If required is False, return value of @default if k not exist
   """
   def __formatValue(value):
      if (not isinstance(value, str)) and (not isinstance(value, unicode)):
         return value

      value = value.strip().encode()
      if value.lower() == 'true':
         value = True
      elif value.lower() == 'false':
         value = False

      return value

   try:
      value = infoDict[k]
   except KeyError:
      if not required:
         return default
      else:
         raise

   # If value is valid, format it first then return
   if isinstance(value, str) or isinstance(value, unicode):
      value = __formatValue(value)
   elif isinstance(value, list):
      value = [__formatValue(v) for v in value]

   return value

def getUniqueInstancesList(inputInstances, funcCb):
   uniqueInstances = set()

   for inputInstance in inputInstances:
      uniqueInstances.add(getattr(inputInstance, funcCb)())

   return list(uniqueInstances)

def convertTupleList2DictList(tupleList):
   """Convert a list of tuple to a list of dict

   @tupleList: a list of tuple and will treat tupleList[0] as the dict's key.
                e.g.[('a', 'b', 'c'), (1, 2, 3), (4, 5, 6)]
   @return: a list of dict. e.g.
            [{'a': 1, 'b': 2, 'c': 3}, {'a': 4, 'b': 5, 'c': 6}]
   """
   keys = tupleList[0]
   return [dict(zip(keys, tupleList[i])) for i in range(1, len(tupleList))]

def convertDict2List(dictInfo, fieldnames):
   """Convert dict to list in required order. e.g.
   dictInfo = {1: 2, 3: 4, 5: 6, 7: 8}
   filednames = [7, 5, 3, 1]

   return value: [8, 6, 4, 2]

   @dictInfo: the input data in dict format
   @fieldnames: a sequence whose elements are associated with
                the fields of the input data in order

   @return: the value of @dictInfo in @fieldnames order
   @rtype: list
   """
   infoList = []

   for k in fieldnames:
      try:
         value = dictInfo[k]
      except:
         value = ''
      infoList.append(value)

   return infoList

def convertDictList2List(dictList, fieldnames):
   """Convert dict list to a 2d list in required order. e.g.
   dictList = [{1: 2, 3: 4, 5: 6, 7: 8}, {1: 'a', 3: 'b', 5: 'c', 7: 'd'}] 
   filednames = [7, 5, 3, 1]

   return value: [[8, 6, 4, 2], {'d', 'c', 'b', 'a'}]

   @dictInfo: the input data in dict format
   @fieldnames: a sequence whose elements are associated with
                the fields of the input data in order

   @return: the value of @dictInfo in @fieldnames order
   @rtype: list
   """
   return [convertDict2List(dictInfo, fieldnames) for dictInfo in dictList]


#---------------------------
# Datetime related libraries
#---------------------------
def getCurrentDate(dateformat=DATE_FORMAT_DEFAULT):
   """Get Current Date with properly date format

   @rtype: str
   """
   return datetime.now().strftime(dateformat)

def getBaseDate(days, dateformat=DATE_FORMAT_DEFAULT):
   """Get Base Date, calculated by (current time - days of time delta)

   @rtype: str
   """
   return (datetime.now() - timedelta(days=days)).strftime(dateformat)

def getDateFromTimestamp(date, dateformat=DATE_FORMAT_DEFAULT):
   """Get Date with properly date format from raw timestamp
   """
   return datetime.fromtimestamp(date).strftime(dateformat)

def getExecutionTime(start, end, dateformat=DATE_FORMAT_DEFAULT):
   """Get the execution time from @start to @end

   @rtype: datetime.timedelta
   """
   start = datetime.strptime(start, dateformat)
   end = datetime.strptime(end, dateformat)
   return end - start

def getTimeDeltaInSeconds(execTime):
   """Return total seconds of @timeDelta

   @rtype: str
   """
   if isinstance(execTime, timedelta):
      return str(int(execTime.total_seconds()))
   else:
      return ''

def getTimeDeltaInMinutes(execTime):
   """Return total minutes of @timeDelta

   @rtype: str
   """
   if isinstance(execTime, timedelta):
      #return str(int(execTime.total_seconds() / 60))
      return str(int(execTime.seconds / 60))
   else:
      return ''

def getWeekRange(dateformat=DATE_FORMAT_YEARMONTHDAY):
   """Return the first / last day of the week for the current day.
   Assuming weeks start on Monday and end on Sunday

   @return: start_date-end_date
   @rtype:  str
   """
   curTime = datetime.now()
   start = curTime - timedelta(days=curTime.weekday())
   end = start + timedelta(days=6)

   return '%s-%s' % (start.strftime(dateformat), end.strftime(dateformat))

#--------------------------------
# File related common libraries
#--------------------------------
def genFilePath(dirName, namePrefix, isFullName=False, ext='.txt'):
   """If isFullName, return dirName/namePrefix_ext
      Or, return dirName/namePrefix-userName-currentData_ext
   """
   if not os.path.isdir(dirName):
      os.makedirs(dirName)

   if not ext.startswith('.'):
      ext = '.%s' % ext

   if isFullName:
      fileName = namePrefix
   else:
      execTime = getCurrentDate()
      fileName = '%s-%s-%s' % (namePrefix, SCRIPT_USER, execTime)

   return os.path.join(dirName, '%s%s' % (fileName, ext))

def getAllFilesInDir(rootDir):
   """Return all files full path under rootDir
   """
   filePaths = []
   for root, _, files in os.walk(rootDir, topdown=True):
      for fileName in files:
         if fileName.startswith('.') or fileName.endswith('~'):
            continue
         else:
            filePaths.append(os.path.join(root, fileName))

   return filePaths

def filterFilesByExt(filterFilePaths, acceptExtList):
   """Return a list of file path whose ext is in @acceptExtList
   """
   filePaths = []
   for filePath in filterFilePaths:
      _, fileExt = os.path.splitext(filePath)
      if any(fileExt in acceptExt for acceptExt in acceptExtList):
         filePaths.append(filePath)

   return filePaths


#--------------------------------
# File write related libraries
#--------------------------------
def dump2JsonFile(obj, namePrefix, outputDir=LOG_DIR, indent=2,
                  isFullName=False):
   """Dump object into JSON file

   @param obj: the object dumping to JSON file
   @param namePrefix: the name prefix of the output file
   @param outputDir: the output file's directory
   @param indent: (Default 2) objects will be pretty-print with this indent level
   @param isFullName: If false, will use namePrefix (Default False)
                      Or, return outputDir/namePrefix-userName-currentData_ext
   """
   jsFilePath = genFilePath(outputDir, namePrefix, isFullName, '.json')
   with open(jsFilePath, 'w') as f:
      json.dump(obj, f, indent=indent, sort_keys=True)

def write2File(writeInfos, namePrefix, outputDir=LOG_DIR, ext='.txt',
               isFullName=False):
   """Write infos into file
      @writeInfos: a list of infos, each element will be a line in file
      @namePrefix: the name prefix of file
      @outputDir: the output directory
      @ext: the ext of new created file, default: .txt
      @isFullName: If false, will use namePrefix (Default False)
                   Or, return outputDir/namePrefix-userName-currentData_ext

      @return: the path of new created file
   """
   filePath = genFilePath(outputDir, namePrefix, isFullName, ext)
   with open(filePath, 'wb') as f:
      for writeInfo in writeInfos:
         f.write(writeInfo)

   return filePath

def write2Csv(writeInfos, namePrefix, outputDir=LOG_DIR, isFullName=False):
   """Write writeInfos (as a list) into a csv file
   """
   filePath = genFilePath(outputDir, namePrefix, isFullName, '.csv')
   with open(filePath, 'wb') as f:
      csvFileWriter = csv.writer(f, quoting=csv.QUOTE_ALL)
      for info in writeInfos:
         csvFileWriter.writerow(info)

   return filePath

def writeDict2Csv(writeInfos, title, namePrefix, outputDir=LOG_DIR,
                  isFullName=False):
   """Write writeInfos (as a list of dict) and title (as a list) into a csv file
   """
   filePath = genFilePath(outputDir, namePrefix, isFullName, '.csv')
   with open(filePath, 'wb') as f:
      csvDictWriter = csv.DictWriter(f, title)
      csvDictWriter.writeheader()
      for writeInfo in writeInfos:
         csvDictWriter.writerow(writeInfo)
      f.close()

   return filePath

def write2Xls(sheetInfoList, namePrefix, outputDir=LOG_DIR, isFullName=False):
   filePath = genFilePath(outputDir, namePrefix, isFullName, '.xls')

   import xlwt

   bk = xlwt.Workbook()
   for sheetName, writeInfos in sheetInfoList:
      sheet = bk.add_sheet(sheetName)
      columnWidthMap = {}
      for rowIndex in range(len(writeInfos)):
         rowInfos = writeInfos[rowIndex]
         for columnIndex in range(len(rowInfos)):
            cell = rowInfos[columnIndex]
            try:
               sheet.write(rowIndex, columnIndex, cell)
            except:
               sheet.write(rowIndex, columnIndex, str(cell))

            if columnIndex not in columnWidthMap:
               columnWidthMap[columnIndex] = 0

            if len(str(cell)) > columnWidthMap[columnIndex]:
               columnWidthMap[columnIndex] = len(str(cell))

      for columnIndex, width in columnWidthMap.items():
         if width > 60:
            width = 60
         sheet.col(columnIndex).width = int((1 + width) * 256)

   bk.save(filePath)
   return filePath


#--------------------------------
# File read related libraries
#--------------------------------
def isFileExist(filePath, raiseErr=True):
   """
   @return True, if file exist
           False, if file not exist and raiseErr = False
           Raise Exception, if file not exist and raiseError = True
   """
   if os.path.exists(filePath):
      return True
   elif not raiseErr:
      return False
   else:
      raise Exception("File %s not exist" % filePath)

def loadFromJsonFile(jsFilePath):
   """Load object from JSON file

   @param jsFilePath: the JSON file's path

   @return: the object loading from JSON file
   """
   isFileExist(jsFilePath)
   with open(jsFilePath) as f:
      return json.load(f)

def readFromXls(filePath, sheetName):
   """Read info from spreed sheet
   """
   import xlrd

   isFileExist(filePath)

   book = xlrd.open_workbook(filePath)
   sheet = book.sheet_by_name(sheetName)
   spreed_sheet_info = []
   for rowIndex in range(0, sheet.nrows):
      row_info = []
      for colIndex in range(0, sheet.ncols):
         cell = sheet.row_values(rowIndex)[colIndex]
         row_info.append(cell)
      spreed_sheet_info.append(row_info)
   return spreed_sheet_info

def readFromCsv(filePath):
   """Read info from csv file

   @rtype: a list of str
   """
   isFileExist(filePath)

   infos = []

   csvInfo = open(filePath, 'rb')
   reader = csv.reader(csvInfo)
   for line in reader:
      infos.append(line)
   csvInfo.close()

   return infos

def readDictListFromCsv(filePath):
   """Read info from csv file and return a list of dict

   @rtype: a list of dict
   """
   isFileExist(filePath)

   with open(filePath, 'rb') as csvfile:
      reader = csv.DictReader(csvfile)
      infos = [row for row in reader]

   return infos

#--------------------------------------
# Str / Format output related libraries
#--------------------------------------
def filterOutXmlTag(info):
   htmlRe = '(\<.*?\>)\w+(\<.*?\>)'
   htmlGroup = re.findall(htmlRe, info)
   if htmlGroup:
      for preTag, postTag in htmlGroup:
         info = info.replace(preTag, '')
         info = info.replace(postTag, '')
      return info
   else:
      return info

def getListFormatIndex(infoList):
   """Get appropriate format index -- length of the longest value in the list
   """
   index = 0
   for info in infoList:
      length = len(filterOutXmlTag(str(info)))
      if length> index:
         index = length

   return index

def alignStr(info, width):
   htmlRe = r'<.*>(.*?)</.*?>'
   htmlGroup = re.findall(htmlRe, info)
   if htmlGroup:
      content = htmlGroup[0]
      width = len(info) - len(content) + width
      return info.ljust(width)
   else:
      return info.ljust(width)

def getIndexByColumn(listInfo, title=True):
   """title = True means the first line is title
   """
   group_info_by_column = {}
   # Covert list to map, group by column
   start = 1 if title else 0
   for row in range(start, len(listInfo)):
      row_info = listInfo[row]
      for column in range(len(row_info)):
         if column not in group_info_by_column:
            group_info_by_column[column] = []
         group_info_by_column[column].append(row_info[column])

   index_by_column = {}
   for column, column_info in group_info_by_column.items():
      index_by_column[column] = getListFormatIndex(column_info)

   # Adjust width again by considering the first line
   firstline = listInfo[0]
   column_length = min(len(firstline), len(index_by_column))
   for column in range(column_length):
      current_width = index_by_column[column]
      if title and current_width == 0:
         continue
      else:
         cell = str(firstline[column])
         index_by_column[column] = max(current_width, len(cell))

   return index_by_column

def removeEmptyColumn(listInfo, title=True):
   """If title is True, then ignore cell value of the first line,
   """
   index_by_column = getIndexByColumn(listInfo, title)
   listInfo_without_empty = []
   for row in range(len(listInfo)):
      row_info = []
      for column in range(len(listInfo[row])):
         try:
            cell_index = index_by_column[column]
         except:
            continue
         if cell_index == 0:
            continue
         row_info.append(str(listInfo[row][column]))
      if row_info:
         listInfo_without_empty.append(row_info)

   return listInfo_without_empty

def alignOutput(summary, info, centerIndex=ALIGN_INDEX, wrap=True, alignChar=':'):
   return "%s  %s  %s%s" % (summary.rjust(centerIndex), alignChar, str(info),
                            '\n' if wrap else '')

def formatDict2Str(dictInfo):
   keys = sorted(dictInfo.keys())
   keyIndex = getListFormatIndex(keys)

   infos = []
   for key in keys:
      infos.append(alignOutput(str(key), str(dictInfo[key]), keyIndex))

   return ''.join(infos)

def formatList2Str(listInfo, overallIndex=' | ',
                   appendIndex=True, title=True):
   """listInfo format: [[list-1], [list-2], [list-3]]
   """
   if appendIndex:
      start = 1 if title else 0
      index = 1
      for i in range(start, len(listInfo)):
         listInfo[i].insert(0, index)
         index += 1

      if title:
         listInfo[0].insert(0, ' ')

   index_by_column = getIndexByColumn(listInfo, title)

   formatted_info_list = []
   for row in range(len(listInfo)):
      formatted_row_info = []
      for column in range(len(listInfo[row])):
         cell = str(listInfo[row][column])
         try:
            cell_width = index_by_column[column]
         except:
            cell_width = 0

         if cell_width == 0:
            # all cell in the same column is empty, skip this column
            continue
         formatted_row_info.append(alignStr(cell, cell_width))

      if formatted_row_info:
         formatted_row_info = overallIndex.join(formatted_row_info).rstrip(' ')
         formatted_info_list.append(formatted_row_info)

   if title:
      second_line = formatted_info_list[1]
      if '\n' in second_line:
         second_line = second_line[0:second_line.index('\n')]

      second_line = filterOutXmlTag(second_line)

      length = len(second_line)
      break_line = '-' * length
      formatted_info_list.insert(1, break_line)

   return '\n'.join(formatted_info_list)


"""Below code is for test purpuse
"""
if __name__ == '__main__':

   print("Testing convertDict2List...")
   dictInfo1 = {1: 2, 3: 4, 5: 6, 7: 8}
   fieldnames = [7, 5, 3, 1, 9]
   convertInfo = convertDict2List(dictInfo1, fieldnames)
   assert(convertInfo == [8, 6, 4 , 2, ''])
   print(" convert list: %s" % convertInfo)

   print("Testing convertDictList2List...")
   dictInfo2 = {1: 'a', 3: 'b', 5: 'c', 7: 'd'}
   convertInfo = convertDictList2List([dictInfo1, dictInfo2], fieldnames)
   assert(convertInfo == [[8, 6, 4 , 2, ''], ['d', 'c', 'b', 'a', '']])
   print(" convert list: %s" % convertInfo)

   print("Testing convertTupleList2DictList...")
   tupleList = [('a', 'b', 'c'), (1, 2, 3), (4, 5, 6)]
   convertList = convertTupleList2DictList(tupleList)
   assert(convertList == [{'a': 1, 'b': 2, 'c': 3},
                          {'a': 4, 'b': 5, 'c': 6}])
   print(" convert list: %s" % convertList)

   print("Testing filterFilesByExt...")
   filePaths = filterFilesByExt(getAllFilesInDir('.'), ['.py'])
   print(" file list: %s" % filePaths)

   print("Testing time related functions...")
   curTime = getCurrentDate()
   startTime = getBaseDate(7)
   print(" current time: %s" % curTime)
   print(" base    time: %s" % startTime)
   print(" exec    time: %s" % getExecutionTime(startTime, curTime))
   print(" week   range: %s" % getWeekRange())
