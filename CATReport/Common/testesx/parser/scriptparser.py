'''
Created on Apr 13, 2016

@author: kaiyuanli
'''
from Common.testesx.constants import IGNORE_LIST, NOT_AVALIABLE, TESTESX_DIR
from Common.utils.restAPI import urlOpen

import os, re

LOG_FILE_EMPTY = 'log file is empty'
LINE_LIMIT_FOR_TOTAL_LOG = 5
LINE_RANGE_FOR_TRACEBACK = 20

KW_TRACEBACK = 'Traceback'

class ScriptInfo():
   """Class to record script info after parser
   """
   def __init__(self, scriptName):
      self._name = scriptName
      self._result = ''
      self._bug_report = ''
      self._log_path = ''
      self._total_log = False
      self._log_info = ''

      # Replace some change-able info with token,
      # then use this field to check whether the failure is new or old
      self._replaced_log_info = ''

   def setResult(self, result):
      self._result = result

   def setBugReport(self, bugReport):
      self._bug_report = bugReport

   def setLogPath(self, logPath):
      self._log_path = logPath

   def setLogInfo(self, logInfo, totalLog=False):
      self._log_info = logInfo
      self._total_log = totalLog

   def _printDetailsInfo(self):
      for key, value in self.__dict__.items():
         print '%s : %s' % (key, value)

class TestScriptLog():
   """Class to read and parser test script log
   """
   def __init__(self, rootDir, scriptName):
      self._rootDir = rootDir
      self._scriptName = scriptName
      self._scriptDir = os.path.join(rootDir, TESTESX_DIR, self._scriptName.replace('/', '_'))
      self._scriptInfo = ScriptInfo(scriptName)

   def __initScriptLocation(self):
      try:
         script_dir_info = urlOpen(self._scriptDir)
      except:
         raise Exception("Script log dir %s not exist" % self._scriptDir)

      try:
         report = re.findall(r'<a href=.*>(.*?.tar.gz)</a>',
                             script_dir_info, re.MULTILINE)[0]
         self._bug_report = os.path.join(self._scriptDir, report)
      except:
         self._bug_report = NOT_AVALIABLE

      try:
         scriptlog = re.findall(r'<a href=.*>(.*?.log)</a>',
                                script_dir_info, re.MULTILINE)[0]
         self._script_log = os.path.join(self._scriptDir, scriptlog)
      except:
         self._script_log = NOT_AVALIABLE

      self._scriptInfo.setBugReport(self._bug_report)
      self._scriptInfo.setBugReport(self._script_log)

   def _parserTestLog(self):
      """Parser test log
      """
      self.__initScriptLocation()
      if self._script_log == NOT_AVALIABLE:
         # Skip parser test log if it's not available 
         return

      log_content = urlOpen(self._script_log)
      if not log_content:
         self._scriptInfo.setLogInfo(LOG_FILE_EMPTY)
         return

      log_content_splitted = log_content.split('\n')
      if len(log_content_splitted) <= LINE_LIMIT_FOR_TOTAL_LOG:
         self._scriptInfo.setLogInfo(log_content, totalLog=True)
         return

      self._parserMajorLog(log_content)

   def _parserMajorLog(self, log_content):
      """Parser major log which lead the result abnormal
      """
      raw_major_log_list = []
      log_content_splitted = log_content.split('\n')

      if KW_TRACEBACK in log_content:
         # Check traceback info first
         raw_major_log_list = self.__parserTracebackLog(log_content_splitted)
      else:
         # Didn't match any rule, record all the log_content instead
         raw_major_log_list = log_content_splitted

      major_log_list = self._filterMajorLog(raw_major_log_list)
      self._scriptInfo.setLogInfo(major_log_list)

   def __parserTracebackLog(self, log_content_splitted):
      """Paser major log by traceback
      """
      tracback_line = 0
      total_line = len(log_content_splitted)
      for line_number in range(total_line):
         if KW_TRACEBACK in log_content_splitted[line_number]:
            tracback_line = line_number
            break

      # Capture LINE_RANGE_FOR_TRACEBACK lines before and after KW_TRACEBACK
      start_line = max(tracback_line - LINE_RANGE_FOR_TRACEBACK, 0)
      end_line = min(tracback_line + LINE_RANGE_FOR_TRACEBACK, total_line - 1)
      return log_content_splitted[start_line:end_line]

   def _filterMajorLog(self, raw_major_log_list):
      """Filter out some lines which contain skip keyword
      """
      def __containIgnoreInfo(info):
         contain = False
         for key in IGNORE_LIST:
            if key in info:
               contain = True
               break
         return contain

      major_log_list = []
      for info in raw_major_log_list:
         if not __containIgnoreInfo(info):
            major_log_list.append(info)
      return '\n'.join(major_log_list)

"""Below code is for test purpose
"""
if __name__ == '__main__':
   resultDirs = ['https://cat.eng.vmware.com/PA/results/esx/3/6/4/3/0/7/1/3',]
   scriptNames = ['vmkapi_bc60/vmkapi-logging.sh', 'vmkapi_bc60/vmkapi-native-driver.sh']
   for resultDir in resultDirs:
      for scriptName in scriptNames:
         print resultDir
         testLog = TestScriptLog(resultDir, scriptName)
         testLog._parserTestLog()
         testLog._scriptInfo._printDetailsInfo()
         print '----------------------------------'
         print '\n\n'
