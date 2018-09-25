''' Library to define testrun output
Created on Sep 7, 2016

@author: kaiyuanli
'''
from Common.utils.htmlUtil import colorMsg, italicMsg
from Common.cat.object.testrun import KW_TRIAGE_ALERT

from Common.utils.constants import RESULT_PASS

from operator import itemgetter

BIOS = 'BIOS'
BOOTLOADER = 'Bootloader'
BOOT_OPTION = 'Boot Option(s)'
WORKLOAD_NAME_SHORT = 'Test Group'
BUILD_INFO = 'Build Info'
CLN = 'CLN'
END_TIME = 'End Time'
EXECUTION_TIME = 'Execution Time(s)'
FEATURE_SWITCH = 'Feature Switch(es)'
GROUP = 'Group(s)'
HOST_IP = 'Host IP'
ISSUES = 'Issues'
JOBS = 'Jobs'
MACHINE = 'Machine'
RESULT = 'Result'
RUN_TIME = 'Run Time'
RUN_TIME_IN_MINUTES = 'Run Time (minutes)'
START_TIME = 'Start Time'
TESTRUN_ID = 'Testrun Id'
TESTRUN_HTML_ID = 'Testrun'
TESTRUN_LINK = 'Testrun Link'
TEST_NAME = 'Test Name'
TESTESX_PREPARE = 'Testesx Prepare'
TRIAGE_INFO = 'Triage Info'
VMKBOOT = 'vmkBoot'
VMKINIT = 'Vmkernel Init'
VMKLOAD = 'VMKernel Load'
WORKLOAD_NAME = 'Workload Name'
WORKUNIT_ID = 'Workunit Id'
BUG_ID = 'Bug Id'
BUG_INFO = 'Bug Info'

class _TestrunFormatter(object):
   """Base class for testrun formatter
   """
   def __init__(self, testrun):
      self._testrun = testrun
      self._outputDict = {}
      wuData = testrun.getWorkunitData()
      wlData = testrun.getWorkloadData()

      self._outputDict[BOOT_OPTION] = wlData.getBootOptions()
      self._outputDict[BUILD_INFO] = wuData.getBuildInfo()
      self._outputDict[BUG_ID] = testrun.getBugID()[0]
      self._outputDict[BUG_INFO] = testrun.getBugID()[1]
      self._outputDict[CLN] = testrun.getCLN()
      self._outputDict[END_TIME] = testrun.getBugDatas()
      self._outputDict[FEATURE_SWITCH] = wlData.getFeatureSwitches()
      self._outputDict[GROUP] = wlData.getGroups()
      self._outputDict[MACHINE] = testrun.getHostNames()
      self._outputDict[RESULT] = testrun.getResult()
      self._outputDict[RUN_TIME] = testrun.getRunTime()
      self._outputDict[RUN_TIME_IN_MINUTES] = testrun.getRunTimeInMinutes()
      self._outputDict[START_TIME] = testrun.getStartTime()
      self._outputDict[TESTRUN_HTML_ID] = testrun.getHtmlId()
      self._outputDict[TESTRUN_ID] = testrun.getId()
      self._outputDict[TESTRUN_LINK] = testrun.getHyperLink()
      self._outputDict[TRIAGE_INFO] = self._getTriagePlainInfo()
      self._outputDict[WORKLOAD_NAME] = wuData.getWorkloadName()
      self._outputDict[WORKLOAD_NAME_SHORT] = wuData.getWorkloadData().getShortenVersionWorkloadName()
      self._outputDict[WORKUNIT_ID] = wuData.getId()
      self._outputDict[ISSUES] = self._getIssues()

   def getInfo(self, key):
      try:
         return self._outputDict[key]
      except:
         return ''

   def _getTriagePlainInfo(self):
      triageInfo = self._testrun.getTriageInfo()
      if isinstance(triageInfo, list):
         output_info = []
         for info in triageInfo:
            output_info.append(info.getName())
         return ', '.join(output_info)
      elif not triageInfo:
         return ''
      else:
         return triageInfo

   def _getTriageHtmlInfo(self):
      triageInfo = self._testrun.getTriageInfo()
      if triageInfo == KW_TRIAGE_ALERT:
         return colorMsg(triageInfo)
      elif isinstance(triageInfo, list):
         # Convert bug / ticket info to HTML veresion message
         html_info = []
         for info in triageInfo:
            html_info.append(info.getHtmlId())
         return ' | '.join(html_info)
      elif triageInfo is None:
         return ''
      else:
         return triageInfo

   def _getIssues(self, ignoreIfPass=True, flag=False, plain=True):
      """@flag: True, will print out issues high light by 'Issues' 
      """
      errorInfos = self._testrun.getErrorLogReadableInfo()
      if not errorInfos:
         return ''

      if ignoreIfPass and self.getInfo(RESULT) == RESULT_PASS:
         return ''

      if flag:
         issues = '%s(s)' % ISSUES
         if not plain:
            issues = italicMsg(issues)

         return '\n%s:\n%s\n' % (issues, errorInfos)
      else:
         return errorInfos

   def getOutput(self):
      output = []
      for key in self.getTitle():
         output.append(self.getInfo(key))
      return output

   @classmethod
   def getTitle(cls):
      raise NotImplementedError("Please override function getTitle()")

   @classmethod
   def sorted(cls, output_list):
      raise NotImplementedError("Please override function sorted()")


class _TestrunPlainFormatter(_TestrunFormatter):
   """Class to define plain output for testrun formatter
   """

   def __init__(self, testrun):
      super(_TestrunPlainFormatter, self).__init__(testrun)
      self._outputDict[ISSUES] = self._getIssues(flag=True)


class _TestrunHtmlFormatter(_TestrunFormatter):
   """Class to define HTML output for testrun formatter
   """

   def __init__(self, testrun):
      super(_TestrunHtmlFormatter, self).__init__(testrun)
      self._outputDict[ISSUES] = self._getIssues(flag=True, plain=False)
      self._outputDict[TRIAGE_INFO] = self._getTriageHtmlInfo()


class TrByWuPlainFormatter(_TestrunPlainFormatter):
   """Class to define plain output for testrun group by workunit
   """

   def getOutput(self):
      output = super(TrByWuPlainFormatter, self).getOutput()
      output.append(self.getInfo(ISSUES))
      return output

   @classmethod
   def getTitle(cls):
      return [TESTRUN_LINK, CLN, RESULT, MACHINE, BUG_INFO]

   @classmethod
   def sorted(cls, output_list):
      # sorted by CLN
      return sorted(output_list, key=itemgetter(1, 0), reverse=True)


class TrByWuHtmlFormatter(_TestrunHtmlFormatter):
   """Class to define HTML output for testrun group by workunit
   """
   def getOutput(self):
      output = super(TrByWuHtmlFormatter, self).getOutput()
      output.append(self.getInfo(ISSUES))
      return output

   @classmethod
   def getTitle(cls):
      return [TESTRUN_HTML_ID, CLN, START_TIME, RUN_TIME,
              RESULT, MACHINE, TRIAGE_INFO, BUG_INFO, '']  ###

   @classmethod
   def sorted(cls, output_list):
      # sorted by CLN
      return sorted(output_list, key=itemgetter(1, 0), reverse=True)


class TrByFailedReasonPlainFormatter(_TestrunPlainFormatter):
   """Class to define plain output for testrun group by failed reasons
   """
   @classmethod
   def getTitle(cls):
      return [TESTRUN_LINK, CLN, WORKLOAD_NAME_SHORT, RESULT, MACHINE, BUG_INFO]

   @classmethod
   def sorted(cls, output_list):
      # sorted by CLN
      return sorted(output_list, key=itemgetter(1, 0), reverse=True)


class TrByFailedReasonHtmlFormatter(_TestrunFormatter):
   """Class to define HTML output for testrun group by failed reasons
   """
   @classmethod
   def getTitle(cls):
      return [TESTRUN_HTML_ID, CLN, WORKLOAD_NAME_SHORT,
              START_TIME, RUN_TIME, RESULT, MACHINE, TRIAGE_INFO, BUG_INFO]

   @classmethod
   def sorted(cls, output_list):
      # sorted by CLN
      return sorted(output_list, key=itemgetter(1, 0), reverse=True)


class TrByBuildInfoPlainFormatter(_TestrunPlainFormatter):
   """Class to define plain output for testrun group by build info
   """
   @classmethod
   def getTitle(cls):
      return [TESTRUN_LINK, CLN, WORKLOAD_NAME_SHORT, START_TIME,
              RUN_TIME, RESULT, TRIAGE_INFO, BUG_INFO]

   @classmethod
   def sorted(cls, output_list):
      # sorted by CLN
      return sorted(output_list, key=itemgetter(1, 0), reverse=True)


class TrByBuildInfoHtmlFormatter(_TestrunHtmlFormatter):
   """Class to define HTML output for testrun group by build info
   """
   @classmethod
   def getTitle(cls):
      return [TESTRUN_HTML_ID, CLN, WORKLOAD_NAME_SHORT,
              START_TIME, RUN_TIME, RESULT, TRIAGE_INFO, BUG_INFO]

   @classmethod
   def sorted(cls, output_list):
      # sorted by CLN
      return sorted(output_list, key=itemgetter(1, 0), reverse=True)


class TrByMachineInfoPlainFormatter(_TestrunPlainFormatter):
   """Class to define plain output for testrun group by machine info
   """

   def getOutput(self):
      output = super(TrByMachineInfoPlainFormatter, self).getOutput()
      output.append(self.getInfo(ISSUES))
      return output

   @classmethod
   def getTitle(cls):
      return [TESTRUN_LINK, CLN, WORKLOAD_NAME_SHORT, BUILD_INFO, START_TIME,
              RUN_TIME, RESULT, TRIAGE_INFO,  BUG_INFO, ''] ###

   @classmethod
   def sorted(cls, output_list):
      # sorted by START_TIME then CLN
      return sorted(output_list, key=itemgetter(4, 1), reverse=True)


class TrByMachineInfoHtmlFormatter(_TestrunHtmlFormatter):
   """Class to define HTML output for testrun group by machine info
   """
   def getOutput(self):
      output = super(TrByMachineInfoHtmlFormatter, self).getOutput()
      output.append(self.getInfo(ISSUES))
      return output

   @classmethod
   def getTitle(cls):
      return [TESTRUN_HTML_ID, CLN, WORKLOAD_NAME_SHORT, BUILD_INFO,
              START_TIME, RUN_TIME, RESULT, TRIAGE_INFO, BUG_INFO, ''] ###

   @classmethod
   def sorted(cls, output_list):
      # sorted by START_TIME then CLN
      return sorted(output_list, key=itemgetter(4, 1), reverse=True)


class DetailTestrunsFormatter(_TestrunFormatter):
   """Class to define plain output for detailed testrun info
   """
   def __init__(self, testrun):
      super(DetailTestrunsFormatter, self).__init__(testrun)
      issues = self._getIssues().replace('\n', ', ')
      self._outputDict[ISSUES] = issues

   @classmethod
   def getTitle(cls):
      return [TESTRUN_ID, WORKUNIT_ID, WORKLOAD_NAME, GROUP,
              BOOT_OPTION, FEATURE_SWITCH, BUILD_INFO, CLN,
              START_TIME, END_TIME, RUN_TIME, RUN_TIME_IN_MINUTES,
              RESULT, MACHINE, TRIAGE_INFO, BUG_INFO, ISSUES]

   @classmethod
   def sorted(cls, output_list):
      # sorted by 1) CLN  2) workload name
      return sorted(output_list, key=itemgetter(3, 1), reverse=True)


class DetailScriptsFormatter(_TestrunFormatter):
   """Class to define plain output for detailed script info
   """

   def getOutput(self):
      """Return a *list* of scripts info
      """
      scripts_detailed_info = self._testrun.getDetailedLogMessages()
      if not scripts_detailed_info:
         return None

      outputs = []
      for info in scripts_detailed_info:
         output = [self.getInfo(TESTRUN_ID), self.getInfo(WORKUNIT_ID),
                   self.getInfo(CLN), self.getInfo(START_TIME),
                   self.getInfo(BUILD_INFO), self.getInfo(BUG_INFO)]
         output.extend(info)
         outputs.append(output)
      return outputs

   @classmethod
   def getTitle(cls):
      return [TESTRUN_ID, WORKUNIT_ID, CLN, START_TIME,
              BUILD_INFO, MACHINE, RESULT, TEST_NAME,
              EXECUTION_TIME, BUG_INFO]

   @classmethod
   def sorted(cls, output_list):
      # sorted by 1) script name 2)  Result 3) machine
      return sorted(output_list, key=itemgetter(5, 4, 3), reverse=True)


class DetailMachineInfoFormatter(_TestrunFormatter):
   """Class to define plain output for detailed machine info
   """

   def __init__(self, testrun):
      super(DetailMachineInfoFormatter, self).__init__(testrun)

      issues = self._getIssues().replace('\n', ', ')
      self._outputDict[ISSUES] = issues

   def getOutput(self):
      """Return a *list* of machines info
      """
      machine_detailed_info = self._testrun.getDetailedMachineMessages()
      if not machine_detailed_info:
         return None

      outputs = []
      for info in machine_detailed_info:
         output = [self.getInfo(TESTRUN_ID), self.getInfo(RESULT),
                   self.getInfo(WORKUNIT_ID), self.getInfo(WORKLOAD_NAME),
                   self.getInfo(BUILD_INFO), self.getInfo(CLN),
                   self.getInfo(START_TIME), self.getInfo(END_TIME),
                   self.getInfo(BUG_INFO)]

         output.extend(info)
         output.append(self._outputDict[ISSUES])
         outputs.append(output)
      return outputs

   @classmethod
   def getTitle(cls):
      return [TESTRUN_ID, RESULT, WORKUNIT_ID, WORKLOAD_NAME,
              BUILD_INFO, CLN, START_TIME, END_TIME, MACHINE,
              HOST_IP, BIOS, BOOTLOADER, VMKBOOT, VMKLOAD,
              VMKINIT, TESTESX_PREPARE, ISSUES, BUG_INFO]


   @classmethod
   def sorted(cls, output_list):
      # sorted by testrun id
      return sorted(output_list, key=itemgetter(0), reverse=True)
