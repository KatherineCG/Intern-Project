#!/build/toolchain/lin64/python-2.7.6/bin/python -u
'''
Created on Apr 13, 2016

@author: kaiyuanli
'''
import os, sys, re
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from Common.utils.commonUtil import formatList2Str
from Common.utils.logger import getLogger
from Common.utils.restAPI import urlOpen
from Common.testesx.constants import NOT_AVAILABLE, TESTESX_DIR,\
                                     VMKERNEL_LOG_WITH_MATCH_TS_FORMAT_RE


logger = getLogger()


class ExecutionInfo(object):
   """Test Execution Info Class
   """

   def __init__(self, vmkernel_log_path, script_name):
      self._log_path = os.path.basename(vmkernel_log_path)
      self._host_name = self._setHostName()
      self._script_name = script_name
      self._start_time = NOT_AVAILABLE
      self._finish_time = NOT_AVAILABLE

   def updateStartTime(self, ts):
      """Update script start time
      """
      self._start_time = ts

   def updateFinishTime(self, ts):
      """Update script finish time
      """
      self._finish_time = ts

   def _setHostName(self):
      try:
         hostName = self._log_path[0: self._log_path.index('.log')]
         return hostName[0:hostName.index('-ilo')]
      except:
         return hostName

   def __str__(self):
      """Unique name composite by <hostname>-<script_name>
      """
      return '%s-%s' % (self._host_name, self._script_name)

   def __repr__(self):
      return str(self)

   def getHostName(self):
      return self._host_name

   def getValue(self):
      """Return tuple (script_name, start_time, end_time)
      """
      return [self._host_name, self._script_name,
              self._start_time, self._finish_time]


class TestesxVmkernelLog(object):
   """class to read / parser log info from testesx.log
   """
   TESTESX_START = 'TESTESX started'
   TESTESX_FINISH = 'TESTESX finished'

   def __init__(self, rootDir):
      self._rootDir = os.path.join(rootDir, TESTESX_DIR)
      self._vmkernel_logs = []

      # Dict to record script-name: execution-info instance
      self._script_executioninfo_dict = {}

      # List to record detailed script info
      self._script_info_list = []

      # Dict to record host-name: detailed script info
      self._host_scripts_dict = {}

   def __getVmkernelLogs(self):
      """Get all vmkernel logs in rootDir
      """
      dirInfo = urlOpen(self._rootDir)
      vmkernelRe = r'<a href=.*>(.*?vmkernel.log)</a>'
      vmkernel_names = re.findall(vmkernelRe, dirInfo, re.MULTILINE)
      for vmkernel_name in vmkernel_names:
         self._vmkernel_logs.append('%s%s' % (self._rootDir, vmkernel_name))

   def parserVmkernelLog(self):
      """Parser vmkernel log, restore useful log
      """
      logger.info("Parsering vmkernel log from %s" % self._rootDir)
      self.__getVmkernelLogs()
      if not self._vmkernel_logs:
         raise Exception("Cannot find *-vmkernel.log in %s" % self._rootDir)

      for vmkernel_log_path in self._vmkernel_logs:
         vmkernel_log = urlOpen(vmkernel_log_path)
         scriptStartedRe = '%s%s\s(.*?)$' % (VMKERNEL_LOG_WITH_MATCH_TS_FORMAT_RE,
                                             self.TESTESX_START)
         scriptStartedLogs = re.findall(scriptStartedRe, vmkernel_log,
                                        re.DOTALL | re.MULTILINE)

         scriptFinishedRe = '%s%s\s(.*?)$' % (VMKERNEL_LOG_WITH_MATCH_TS_FORMAT_RE,
                                              self.TESTESX_FINISH)
         scriptFinishedLogs = re.findall(scriptFinishedRe, vmkernel_log,
                                         re.DOTALL | re.MULTILINE)

         for ts, scriptName in scriptStartedLogs:
            info = ExecutionInfo(vmkernel_log_path, scriptName)
            info.updateStartTime(ts)
            self._script_executioninfo_dict[scriptName] = info

         for ts, scriptName in scriptFinishedLogs:
            try:
               info = self._script_executioninfo_dict[scriptName]
               info.updateFinishTime(ts)
            except:
               info = ExecutionInfo(vmkernel_log_path, scriptName)
               info.updateStartTime('N/A')
               info.updateFinishTime(ts)
               self._script_executioninfo_dict[scriptName] = info

      self._script_info_list = self._script_executioninfo_dict.values()
      self._script_info_list = sorted(self._script_info_list,
                                      key=lambda ExecutionInfo: ExecutionInfo._start_time)

      for script_info in self._script_info_list:
         hostName = script_info.getHostName()
         if hostName not in self._host_scripts_dict:
            self._host_scripts_dict[hostName] = []

         self._host_scripts_dict[hostName].append(script_info.getValue())

   def getScriptExecutionList(self):
      """Get script execution list, sort by start time
      """
      return self._script_info_list

   def getScriptExecutionReadableInfo(self):
      """Get script execution info as string
      """
      script_infos = []
      for script_info in self._script_info_list:
         script_infos.append(script_info.getValue())

      return script_infos

   def getHostScriptsDict(self):
      """Get host - script info list
      """
      return self._host_scripts_dict


"""Below code is for test purpose
"""
if __name__ == '__main__':
   from argparse import ArgumentParser

   from Common.cat.object.testrun import Testrun

   parser = ArgumentParser(description='Show test script running info by parser vmkernel log')

   parser.add_argument('-t', type=str, dest='testrunIds', action='append',
                       help="Testrun IDs")
   args = parser.parse_args()

   trIds = args.testrunIds

   trDatas = [Testrun(trId) for trId in trIds]
   for trId in trIds:
      tr = Testrun(trId)
      tr.initCatRawInfo()
      resultDir = tr.getResultDirUrl()
      vmkernelLog = TestesxVmkernelLog(resultDir)
      vmkernelLog.parserVmkernelLog()
      scriptInfos = vmkernelLog.getScriptExecutionReadableInfo()

      print("\n==============")
      print("Show N/A tests")
      print("==============")
      for hostName, scriptName, startTime, endTime in scriptInfos:
         if startTime == 'N/A' or endTime == 'N/A':
            print('%s %s %s %s %s' % (trId, hostName, scriptName,
                                      startTime, endTime))

      print("\n============================")
      print("Show all script running info")
      print("============================")
      scriptInfos.insert(0, ['Host Name', 'Script', 'Start Time', 'End Time'])
      print(formatList2Str(scriptInfos, title=True))

      print("\n============================")
      print("Show all script running info per host")
      print("============================\n")
      hostScriptsDict = vmkernelLog.getHostScriptsDict()
      for host, scriptInfos in vmkernelLog.getHostScriptsDict().items():
         print("\n Test script running info from host %s" % host)
         scriptInfos.insert(0, ['Host Name', 'Script', 'Start Time', 'End Time'])
         print(formatList2Str(scriptInfos, title=True))
