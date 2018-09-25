#!/build/toolchain/lin64/python-2.7.6/bin/python -u
'''library to read and parser <cat-testrun-result-dir>/testesx/testesx.log
Created on Aug 29, 2016

@author: kaiyuanli
'''

from datetime import datetime
import os, re, sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from Common.testesx.constants import *
from Common.testesx.parser.commonparser import getUnifiedLogInfo, trunctStr
from Common.utils.restAPI import urlOpen


class _LineLevelLog(object):
   """Parser and record esx host log per line
   """
   KEY_ANOTHER_EXCEPTION = 'During handling of the above exception, another exception occurred:'
   KEY_GENERIC_EXCEPTION_DEPRECATED = 'WARNING: the GenericException() class is deprecated and will be removed shortly. Please use DebugInfoMixIn instead.'
   KEY_BOOT_TIMEOUT = 'ESX boot timed out'
   KEY_CONNECTION_LOST = 'connection lost'
   KEY_DASH = ' - '
   KEY_DISABLED = ' is disabled'
   KEY_EXECUTION = ' - Took'
   KEY_INFRA_ISSUE = 'Infrastructure issue'
   KEY_IPMI_TRANS_ISSUE = 'IPMI transport error'
   KEY_NIMBUS_COMMNAND_ERROR = 'Nimbus command error'
   KEY_PXE_COMMAND_ERROR = 'PXEconfig command error'
   KEY_GENERIC_TELNET_ISSUE = 'Unknown telnet error'
   KEY_TESTESXD_START_ISSUE = 'Failed to start testesxd'
   KEY_TRACEBACK = 'Traceback (most recent call last):'
   KEY_UWCOREDUMP = 'UW coredump'
   KEY_VMSUPPORT_RC = 'vm-support command executed, but returned an error'
   KEY_VMSUPPORT_FAIL = 'Failed to collect vm-support'

   def __init__(self, hostname, logLevel, logInfo):
      self._hostname = hostname
      self._result = logLevel
      # replace wrap line for testesx exception analysis
      self._raw_log_info = logInfo.replace('\n  ', self.KEY_DASH)
      self._execution = NOT_AVAILABLE
      self._info = None
      self._parseLogMessage()

   def _parseLogMessage(self):
      """Parse log message and initialize self._info and self._execution
      """
      try:
         if self.KEY_EXECUTION in self._raw_log_info:
            self._handleExecutionLog()
         elif self._result == LEVEL_WARNING:
            self._handleWarnningLog()
         elif self._result == LEVEL_ERROR:
            self._handleErrorLog()
         elif self._result == LEVEL_PSOD:
            self._handlePsodLog()
      except:
         self._info = self._raw_log_info

   def _handleExecutionLog(self):
      if self.KEY_CONNECTION_LOST in self._raw_log_info:
         self._result = LEVEL_CONNECTIONLOST

      pattern = '(.*?)%s\s(.*?)s' % self.KEY_EXECUTION
      self._info, self._execution = re.findall(pattern, self._raw_log_info)[0]

   def _handleWarnningLog(self):
      if self.KEY_DISABLED in self._raw_log_info:
         self._result = LEVEL_DISABLED
         self._info = trunctStr(self._raw_log_info, self.KEY_DISABLED)
      elif self.KEY_UWCOREDUMP in self._raw_log_info:
         self._result = LEVEL_UWCOREDUMP
         pattern = '%s\s\(app:.*?\, file:\s(.*?)\)' % self.KEY_UWCOREDUMP
         self._info = re.findall(pattern, self._raw_log_info)[0]
      else:
         self._info = self._raw_log_info

   def __handleInfraErrorLog(self):
      """Return a boolean to indicate whether or not
      matched proper infrastructure keyword, upper caller is _handleErrorLog
      """
      if self.KEY_TESTESXD_START_ISSUE in self._raw_log_info:
         # Handle testesxd exception
         self._result = LEVEL_INFRA_TESTESX
         self._info = trunctStr(self._raw_log_info, self.KEY_TRACEBACK)

      elif self.KEY_BOOT_TIMEOUT in self._raw_log_info:
         # Handle boot timeout
         self._result = LEVEL_INFRA_BOOT_TIMEOUT
         pattern = 'error:\s(.*?)\,\s(.*?)\s\(or is it hung\?\)'
         # ('ESX has started', 'but was too slow to initialize')
         start, slow = re.findall(pattern, self._raw_log_info)[0]
         self._info = '%s %s' % (start, slow)

      else:
         pattern = None
         if self.KEY_NIMBUS_COMMNAND_ERROR in self._raw_log_info:
            # Handle Nimbus Command Error
            self._result = LEVEL_INFRA_NIMBUS
            pattern = 'error:\s+(.*?)\s\-\svm name'

         elif self.KEY_IPMI_TRANS_ISSUE in self._raw_log_info:
            # Handle IPMI Transport issue
            self._result = LEVEL_INFRA_IPMI
            pattern = 'error:\s+(.*?)\s\-\sipmitool'

         elif self.KEY_PXE_COMMAND_ERROR in self._raw_log_info:
            # Handle PXEConfig error
            self._result = LEVEL_INFRA_PXE
            pattern = 'error:\s+(.*?)\s\-\scommand'

         elif self.KEY_GENERIC_TELNET_ISSUE in self._raw_log_info:
            # Handle generic telnet issue
            self._result = LEVEL_INFRA_TELNET
            pattern = 'error:\s+(.*)'

         elif self.KEY_INFRA_ISSUE in self._raw_log_info:
            # Handle generic infrastructure issue
            self._result = LEVEL_INFRA
            pattern = 'error:\s+(.*?)\s\-\shostname'


         if pattern:
            self._info = re.findall(pattern, self._raw_log_info)[0]

      return True if self._info else False

   def __handleMiscErrorLog(self):
      """Return a boolean to indicate whether or not
      matched proper misc error keyword, upper caller is _handleErrorLog
      """
      pattern = None

      if self.KEY_VMSUPPORT_RC in self._raw_log_info:
         # Handle exception during collect vmsupport
         self._result = LEVEL_FAIL_COLLECT_VMSUPPORT
         self._info = self.KEY_VMSUPPORT_RC

      elif self.KEY_VMSUPPORT_FAIL in self._raw_log_info:
         # Handle failed to call collect vmsupport
         self._result = LEVEL_FAIL_COLLECT_VMSUPPORT
         pattern = 'error:\s+(.*)'

      if pattern:
         self._info = re.findall(pattern, self._raw_log_info)[0]

      return True if self._info else False

   def _handleErrorLog(self):
      """Only return the first line of error message,
      and ignore the whole exception traceback
      """
      for isMatched in [self.__handleInfraErrorLog(),
                        self.__handleMiscErrorLog()]:
         if isMatched:
            return

      # Remove redundant info away first 
      self._raw_log_info = trunctStr(self._raw_log_info,
                                     self.KEY_GENERIC_EXCEPTION_DEPRECATED,
                                     trunct_from_start=True)

      if self.KEY_TRACEBACK not in self._raw_log_info:
         # If no traceback in raw info, record all
         self._info = self._raw_log_info

      else:
         # only record important error info, ignore the whole traceback
         info_list = self._raw_log_info.split('\n')
         strip_info_list = [value for value in info_list if value != '']

         if self.KEY_ANOTHER_EXCEPTION in strip_info_list:
            index = strip_info_list.index(self.KEY_ANOTHER_EXCEPTION) - 1
         else:
            index = len(strip_info_list) - 1
   
         self._info = strip_info_list[index]

   def _handlePsodLog(self):
      """Remove vmkernel timestamp away from psod log
      """
      for format_re in [VMKERNEL_LOG_FORMAT_RE, VMKBOOT_LOG_FORMAT_RE]:
         try:
            psod_log_re = '%s(.*?)$' % (format_re)
            self._info = re.findall(psod_log_re, self._raw_log_info,
                                    re.DOTALL | re.MULTILINE)[0]
         except:
            continue
         else:
            return

      if not self._info:
         self._info = self._raw_log_info

   def getResult(self):
      return self._result

   def getResultInfo(self):
      return self._info

   def getExecution(self):
      return self._execution

   def getHostName(self):
      return self._hostname

   def __str__(self):
      info = self.getDetailedInfo()
      return ' - '.join(info)

   def getDetailedInfo(self):
      """Return [hostname, result, result_info, execution]
      """
      return [self.getHostName(), self.getResult().lower(),
              self.getResultInfo(), self.getExecution()]


class _EsxHostLog(object):
   """class to parse host level log
   """
   KEY_BOOTLOARDER_START = 'Bootloader started'
   KEY_BOOTLOARDER_DONE = 'Bootloader done'
   KEY_ESX_HOST = 'ESX HOST: '
   KEY_HOST_IP = 'Got IP address: '
   KEY_RESET_MACHINE = 'Resetting machine'
   KEY_TESTESX_START = 'Starting testesx on'
   KEY_TESTESX_READY = 'ESX is ready for testing'
   KEY_VMKBOOT_START = 'vmkBoot started'
   KEY_VMKBOOT_DONE = 'vmkBoot done'
   KEY_VMKLOAD_START = 'VMKernel started'
   KEY_VMKLOAD_DONE = 'VMKernel loaded successfully'
   KEY_VMKENREL_INITIAZLIED = 'Boot Successful'

   def __init__(self, esx_flag):
      self._esx_flag = esx_flag
      self._line_level_logList = []
      self._host_result_list = set()
      self._esx_hostname = NOT_AVAILABLE
      self.host_ip = NOT_AVAILABLE
      self._reset_time = NOT_AVAILABLE
      self._bootloader_st = NOT_AVAILABLE
      self._bootloader_dt = NOT_AVAILABLE
      self._vmkboot_st = NOT_AVAILABLE
      self._vmkboot_dt = NOT_AVAILABLE
      self._vmkload_st = NOT_AVAILABLE
      self._vmkload_dt = NOT_AVAILABLE
      self._vmk_it = NOT_AVAILABLE
      self._testesx_rt = NOT_AVAILABLE

   def update(self, timestamp, logLevel, logInfo):
      """Update EsxHost per line
      """
      if logLevel == LEVEL_INFO:
         self.__handleInfoLog(timestamp, logInfo)
      else:
         line_level_log = _LineLevelLog(self._esx_hostname, logLevel, logInfo)
         self._line_level_logList.append(line_level_log)
         self._host_result_list.add(line_level_log.getResult())

   def __updateHostName(self, logInfo, keyword):
      """Handle Host Name
      """
      host_name_info = trunctStr(logInfo, keyword, trunct_from_start=True)
      if NIMBUS_KEY in host_name_info:
         self._esx_hostname = host_name_info.replace(':_:', '-')
         self._esx_hostname = host_name_info.replace('...', '')
      else:
         self._esx_hostname = trunctStr(host_name_info, '-ilo')

   def __handleInfoLog(self, timestamp, logInfo):
      """Handle log info which log level is INFO
      """
      def setTimeStamp(value, newValue):
         if value == NOT_AVAILABLE:
            value = newValue

         return value

      if self.KEY_ESX_HOST in logInfo:
         self.__updateHostName(logInfo, self.KEY_ESX_HOST)

      elif self.KEY_HOST_IP in logInfo:
         # Parser esx host ip after host boot
         self.host_ip = trunctStr(logInfo, self.KEY_HOST_IP,
                                  trunct_from_start=True)

      elif self.KEY_RESET_MACHINE in logInfo:
         self._reset_time = setTimeStamp(self._reset_time, timestamp)
         self.__updateHostName(logInfo, self.KEY_RESET_MACHINE)

      elif self.KEY_BOOTLOARDER_START in logInfo:
         self._bootloader_st = setTimeStamp(self._bootloader_st, timestamp)

      elif self.KEY_BOOTLOARDER_DONE in logInfo:
         self._bootloader_dt = setTimeStamp(self._bootloader_dt, timestamp)

      elif self.KEY_VMKBOOT_START in logInfo:
         self._vmkboot_st = setTimeStamp(self._vmkboot_st, timestamp)

      elif self.KEY_VMKBOOT_DONE in logInfo:
         self._vmkboot_dt = setTimeStamp(self._vmkboot_dt, timestamp)

      elif self.KEY_VMKLOAD_START in logInfo:
         self._vmkload_st = setTimeStamp(self._vmkload_st, timestamp)

      elif self.KEY_VMKLOAD_DONE in logInfo:
         self._vmkload_dt = setTimeStamp(self._vmkload_dt, timestamp)

      elif self.KEY_VMKENREL_INITIAZLIED in logInfo:
         self._vmk_it = setTimeStamp(self._vmk_it, timestamp)

      elif self.KEY_TESTESX_READY in logInfo:
         self._testesx_rt = setTimeStamp(self._testesx_rt, timestamp)

   def __getExecutionTime(self, start_time, end_time):
      if start_time == NOT_AVAILABLE or end_time == NOT_AVAILABLE:
         return NOT_AVAILABLE

      try:
         # get execution by TESTESX_TIMESTAMP first
         # Python 2 strptime function does not support
         # %Z format for timezones, hence slice start_time and end_time
         return str(datetime.strptime(end_time[:19], TESTESX_TIMESTAMP)
                    - datetime.strptime(start_time[:19], TESTESX_TIMESTAMP))
      except ValueError:
         # use legacy testesx timestamp to get execution time
         return str(datetime.strptime(end_time, TESTESX_TIMESTAMP_DEPRECATED)
                    - datetime.strptime(start_time, TESTESX_TIMESTAMP_DEPRECATED))

   def getHostName(self):
      return self._esx_hostname

   def getHostIp(self):
      return self.host_ip

   def getStatisticFriendlyHostName(self):
      """Customize nimbus-<ldap-name>-<testrun-id>-<esx-flag> to
         nimbus-esx, which will be easier to statistic machine level information
         Otherwise, each Nimbus testrun would return M host names
      """
      if NIMBUS_KEY in self._esx_hostname:
         return NIMBUS_ESX
      else:
         return self._esx_hostname

   def getBiosInitPhaseTime(self):
      return self.__getExecutionTime(self._reset_time,
                                     self._bootloader_st)

   def getBootLoaderPhaseTime(self):
      return self.__getExecutionTime(self._bootloader_st,
                                     self._bootloader_dt)

   def getVmkernelBootPhaseTime(self):
      return self.__getExecutionTime(self._vmkboot_st,
                                     self._vmkboot_dt)

   def getVmkernelLoadPhaseTime(self):
      return self.__getExecutionTime(self._vmkload_st,
                                     self._vmkload_dt)

   def getVmkernelInitializePhaseTime(self):
      return self.__getExecutionTime(self._vmkload_dt,
                                     self._vmk_it)

   def getTestesxPreparePhaseTime(self):
      return self.__getExecutionTime(self._vmk_it,
                                     self._testesx_rt)

   def getLineLevelLogs(self):
      return self._line_level_logList

   def getResultList(self):
      return self._host_result_list


class TestesxLog(object):
   """Class to read / parse log info from testesx.log
   """
   KEY_SKIP_LIST = ['Decommissioning',
                    'All sessions have been lost, aborting testesx',
                    'testesx was interrupted',
                    'testesx main orchestrator loop terminated',
                    'testesx has failed to run all tests',
                    'Some or all testesx tests have failed',
                    'UW coredump detected during boot',
                    'ESX userworld coredump',
                    'ESX product error',
                    'vmkernel PSOD',
                    'cannot start the NMI profiler: Dynamic probe error']

   CONTENTS_OF_STDERR = 'contents of <stderr>'
   HOST_TYPE_NIMBUS = "HOST TYPE: nimbus"
   HOST_CONNECTION_LOST = 'connection lost (socket timeout)'

   def __init__(self, root_dir):
      """Init TestesxLog instance,
      exception will be raised out if testesx_url doesn't exist
      """
      self._testesx_url = os.path.join(root_dir, TESTESX_DIR, TESTESX_LOG)
      try:
         self._testesx_log = urlOpen(self._testesx_url, True)
      except:
         raise Exception("Failed to find testesx.log in %s" % self._testesx_url)

      self._esx_hostlog_dict = {}
      self._total_line_level_logs = []
      self._test_result_list = []
      self._nimbus = False
      self._total_tests = 0
      self._failed_tests = 0

   def getTestesxLogUrl(self):
      """Return testesx log url
      """
      return self._testesx_url

   def getResultList(self):
      """Return all kinds of result list
      """
      resultList = set()
      for esx_host in self._esx_hostlog_dict.values():
         resultList |= esx_host.getResultList()

      return resultList

   def parseTestesxLog(self):
      """Parse testesx log, restore each host related log ,
      then restore all script level log per group
      """
      esx_loglist = self._parseOverallLog()
      if not esx_loglist:
         # Try legacy testesx timestamp and parse log one more time
         esx_loglist = self._parseOverallLog(TESTESX_TIMESTAMP_DEPRECATED_RE)

      if not esx_loglist:
         # TODO: Add log parser then exception happened before init esx sub logger
         return
      else:
         # Parser esx log
         self._parseEsxDetailLog(esx_loglist)

   def _parseOverallLog(self, testesx_timestamp=TESTESX_TIMESTAMP_RE):
      """Parse overall log, define host type, and group log message by esx host
      """
      # 0. Define host type
      if TestesxLog.HOST_TYPE_NIMBUS in self._testesx_log:
         self._nimbus = True

      # 1. Split log per timestamp
      split_per_timestamp_re = '^(%s.*?)(?=\n%s|\n%s.*$)' % (testesx_timestamp,
                                                         testesx_timestamp,
                                                         testesx_timestamp)
      logs_group_by_timestamp = re.findall(split_per_timestamp_re,
                                           self._testesx_log,
                                           re.DOTALL | re.MULTILINE)
      if not logs_group_by_timestamp:
         return

      #2. Split log info to format (logLevel, esxFlag, log_info)
      esx_loglist = []
      for log_info in logs_group_by_timestamp:
         log_info = log_info.strip('\n')
         split_re = '^(%s)\s\[(.*?)\]\s\[(esx\d+)\]\s(.*?)$' % (testesx_timestamp)
         split_log_info = re.findall(split_re, log_info, re.DOTALL)
         if not split_log_info:
            continue
         esx_loglist.append(split_log_info[0])

      return esx_loglist

   def _parseEsxDetailLog(self, esx_loglist):
      """Parse esx detailed log
      """
      def _skipParserLog(log_info):
         if not log_info:
            return True

         elif log_info == TestesxLog.HOST_CONNECTION_LOST:
            # Skip log with cotains connection lost, which is caused by PSOD
            return True

         elif log_info.startswith(TestesxLog.CONTENTS_OF_STDERR):
            # If log only contains connection error, skip this debug log
            return True

         for skip_log in self.KEY_SKIP_LIST:
            if skip_log in log_info:
               return True

         return False

      for timestamp, log_level, esx_flag, log_info in esx_loglist:
         if _skipParserLog(log_info):
            continue

         if esx_flag not in self._esx_hostlog_dict:
            self._esx_hostlog_dict[esx_flag] = _EsxHostLog(esx_flag)

         self._esx_hostlog_dict[esx_flag].update(timestamp, log_level, log_info)

      for esxHost in self._esx_hostlog_dict.values():
         self._total_line_level_logs.extend(esxHost.getLineLevelLogs())

      self.setTestResultList()

   def setTestResultList(self):
      """Set test result list
      """
      """Return script level detailed info, each item in format
         (hostname, testresult, testname, execution time)
      """
      detailed_log_message_list = self.getDetailedLogMessages()
      valid_result = LEVEL_SCRIPT_LIST[:]
      if LEVEL_PSOD in self.getResultList():
         valid_result.remove(LEVEL_CONNECTIONLOST)

      for detailed_log in detailed_log_message_list:
         if detailed_log.getResult() in valid_result:
            self._test_result_list.append(detailed_log.getDetailedInfo())
            self._total_tests += 1
            if detailed_log.getResult() not in [LEVEL_DISABLED, LEVEL_SKIPPED,
                                                LEVEL_PASS]:
               self._failed_tests += 1

   def getHostNames(self):
      """Return read-able hostnames 
      """
      if self._nimbus:
         return ['%s Nimbus ESX' % len(self._esx_hostlog_dict)]
      else:
         return [esxHost.getHostName()
                 for esxHost in self._esx_hostlog_dict.values()]

   def getHostNameIpDict(self):
      """Return host name and ip mapping
      """
      return dict((esxHost.getHostName(), esxHost.getHostIp()) 
                  for esxHost in self._esx_hostlog_dict.values())

   def getDetailedLogMessages(self):
      """Return detailed _LineLevelLog instance list
      """
      return self._total_line_level_logs

   def getErrorLogMessages(self):
      """Return _LineLevelLog instance list which can be considered as error info,
      include FAIL, PSOD, CONNECTION LOST without PSOD, UW coredump, etc.
      """
      positive_result = LEVEL_POSITIVE_LIST[:]
      total_result_list = self.getResultList()

      if LEVEL_PSOD in total_result_list:
         # Some PSOD instances are treated as TIMEOUT in testesx
         positive_result.append(LEVEL_CONNECTIONLOST)
         positive_result.append(LEVEL_INFRA_BOOT_TIMEOUT)

      if any('INFRA_ISSUE_' in result for result in total_result_list):
         # If contain any specified INFRA_ISSUE_* sub key, ignore the overall
         # INFRA_ISSUE result
         positive_result.append(LEVEL_INFRA)

      log_list = set()
      detailed_log_message = self.getDetailedLogMessages()
      for detailed_log in detailed_log_message:
         if detailed_log.getResult() not in positive_result:
            log_list.add(detailed_log)

      def by_result_level(info):
         """sorted by result level
         """
         result = info.getResult()
         return LEVEL_PRIORITY.index(result)

      # sorted by result level, priority from top to down
      return sorted(list(log_list), key=by_result_level, reverse=True)

   def getErrorLogReadableInfo(self):
      """Return readable error message.
      """
      error_log_list = self.getErrorLogMessages()
      readable_info_list = set()

      for error_log in error_log_list:
         readable_info = "%s - %s" % (error_log.getResult().lower(),
                                      error_log.getResultInfo())

         readable_info_list.add(readable_info)

      # Don't sort readable_info_list since sorted in getErrorLogMessages()
      return '\n'.join(list(readable_info_list))

   def getUnifiedErrorMessages(self):
      """Return unified error message (replace dynamic str away) as a list

      Each element is in format (result_level, unified_info_str)
      """
      error_log_list = self.getErrorLogMessages()
      unified_info_list = set()

      for error_log in error_log_list:
         result = error_log.getResult()
         info = error_log.getResultInfo()
         unified_info_list.add((result.lower(),
                                getUnifiedLogInfo(result, info)))

      return list(unified_info_list)

   def getScriptLevelDetailedInfo(self):
      """Return script level detailed info, each item in format
         (hostname, testresult, testname, execution time)
      """
      return self._test_result_list

   def getMachineLevelDetailedInfo(self):
      """Return machine level detailed info
      """
      machine_log_info = []
      for esx_host in self._esx_hostlog_dict.values():
         machine_info = [esx_host.getHostName(),
                         esx_host.getHostIp(),
                         esx_host.getBiosInitPhaseTime(),
                         esx_host.getBootLoaderPhaseTime(),
                         esx_host.getVmkernelBootPhaseTime(),
                         esx_host.getVmkernelLoadPhaseTime(),
                         esx_host.getVmkernelInitializePhaseTime(),
                         esx_host.getTestesxPreparePhaseTime()]
         machine_log_info.append(machine_info)
      return machine_log_info

   def getTotalTestNum(self):
      return self._total_tests

   def getPassedTestNum(self):
      return (self._total_tests - self._failed_tests)


"""Below code is for test purpose
"""
if __name__ == '__main__':
   from argparse import ArgumentParser

   from Common.cat.object.testrun import Testrun

   parser = ArgumentParser(description='Show test script running result by parser testesx log')

   parser.add_argument('-t', type=str, dest='testrunIds', action='append',
                       help="Testrun IDs")
   args = parser.parse_args()

   trIds = args.testrunIds

   trDatas = [Testrun(trId) for trId in trIds]
   for trId in trIds:
      tr = Testrun(trId)
      tr.initCatRawInfo()
      resultDir = tr.getResultDirUrl()
      testesxLog = TestesxLog(resultDir)
      testesxLog.parseTestesxLog()
      print("\n\nTestrun ID: %s, testesx log url: %s" % (trId,
                                 testesxLog.getTestesxLogUrl()))

      print("\nDetailed machine related info in format: (host | host ip | bios init | boot loader | "
            "vmkernel boot | vmkernel load | vmkernel init | testesx prepare")
      print("==============================")
      print("Host Names: %s" % testesxLog.getHostNames())
      print("Machine level detailed info:")
      for machineLog in testesxLog.getMachineLevelDetailedInfo():
         print(machineLog)

      detailed = testesxLog.getScriptLevelDetailedInfo()
      print("\nDetailed %d script(s) info:" % len(detailed))
      print("============================")
      for detail in detailed:
         print(' | '.join(detail))

      print("\nDetailed error message in format: (host | error-type | error-detail | execution-time):")
      print("=================================")
      errorList = testesxLog.getErrorLogMessages()
      for errorLog in errorList:
         print(' | '.join(errorLog.getDetailedInfo()))

      print("\nError unified message:")
      print(testesxLog.getUnifiedErrorMessages())

      print("\nError readable message:")
      print(testesxLog.getErrorLogReadableInfo())

      print("\nFailed Rate: %s / %s\n" % (testesxLog.getFailedTestNum(),
                                          testesxLog.getTotalTestNum()))
