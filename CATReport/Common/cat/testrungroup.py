'''Library to query, collect, parser, conclude various testruns
Created on Sep 2, 2016

@author: kaiyuanli
'''
from Common.cat.lib.catApi import getCatHyperLink
from Common.cat.object.testrun import Testrun
from Common.cat.output.overallreport import ReporByWuHtmlFormatter, \
   ReportByFailedReasonHtmlFormatter, ReportByBuildInfoHtmlFormatter,\
   ReportByMachineInfoHtmlFormatter
from Common.cat.output.testrunreport import DetailTestrunsFormatter,\
   DetailScriptsFormatter, DetailMachineInfoFormatter, \
   TrByWuPlainFormatter, TrByWuHtmlFormatter,\
   TrByFailedReasonPlainFormatter, TrByFailedReasonHtmlFormatter,\
   TrByBuildInfoPlainFormatter, TrByBuildInfoHtmlFormatter,\
   TrByMachineInfoPlainFormatter, TrByMachineInfoHtmlFormatter
from Common.utils.commonUtil import formatList2Str, write2File, write2Xls
from Common.utils.constants import RESULT_PASS
from Common.utils.htmlUtil import boldMsg, genHyperLink
from Common.utils.logger import getLogger
from testruncollector import TestrunsCollector
from bug.bugdata import main as bdmain
from bug.bugzilla_daily import main as dailymain

logger = getLogger()

class _TestrunsGroup(object):
   """Base class to group testruns
   """
   def __init__(self, testrun_plain_format_clazz, testrun_html_format_clazz,
                report_html_format_clazz, skip_pass=False, parser_log=True):
      # Output related argus
      self._tr_plain_format_clazz = testrun_plain_format_clazz
      self._tr_html_format_clazz = testrun_html_format_clazz
      self._skip_pass = skip_pass
      self._parser_log = parser_log

      # Testrun related argus
      self._testruns = []
      self._testrunsDict = {} # keyData - [testrunData] dictionary
      self._detailed_trs_result = []
      self._detailed_scripts_result = []
      self._detailed_machines_result = []

      #bug argus
      self._bugs = []

      # Report / collection related argus
      self._print_tr_group_conclude_info = True
      self._reportDict = {} # keyData - testrunsCollector dictionary
      self._report_html_formatter = report_html_format_clazz(self._reportDict)

   def retrieveTestrunsById(self, testrunIds):
      testruns = Testrun.queryTestrunsByIds(testrunIds,
                                            skipPass=self._skip_pass,
                                            parserLog=self._parser_log)

      if testruns:
         self._testruns.extend(testruns)

   def retrieveTestruns(self, limitDay, limitNumber, wuIds=[], wlNames=[],
                        testerIds=[], areaIds=[], areaNames=[], branchNames=[],
                        bldTypes=[]):
      """Retrieve testruns from CAT
      """
      testruns = Testrun.queryTestrunDatas(limitDay, limitNumber, wuIds,
                                           wlNames, areaIds, areaNames,
                                           branchNames, testerIds, bldTypes,
                                           skipPass=self._skip_pass,
                                           parserLog=self._parser_log)

      if testruns:
         self._testruns.extend(testruns)

   def setTestruns(self, testruns):
      """Set testruns to TestGroup
      """
      self._testruns = testruns

   def extendTestruns(self, testruns):
      """Extend testruns to TestrunGroup
      """
      if not testruns:
         return
      self._testruns.extend(testruns)

   def getTestruns(self):
      """Return all testruns retrieved by this testrun group
      """
      return self._testruns

   def validTestrunsGroup(self):
      """True (valid), if Testrungroup contains _testruns.
         Otherwise, False (invalid)
      """
      if not self._testruns:
         logger.warn("Cannot find testruns from CAT")
         return False
      else:
         return True

   def getTestrunsDict(self):
      return self._testrunsDict

   def _appendTestrun(self, key, testrun):
      if key not in self._testrunsDict:
         self._testrunsDict[key] = []
      self._testrunsDict[key].append(testrun)

   def groupTestrunToDict(self):
      if not self._testruns:
         logger.warn("Cannot find testruns from CAT")
         return

      for testrun in self._testruns:
         self._groupTestrun(testrun)

      for key, testruns in self._testrunsDict.items():
         collector = TestrunsCollector(testruns)
         self._reportDict[key] = collector
         # Only recored detailed testrun info which is record in testrunDict
         for testrun in testruns:
            self._updateDetailedTestrunInfo(testrun)
            #self._buglist

   def _updateDetailedTestrunInfo(self, testrun):
      # Testrun Level
      testrun_formatter = DetailTestrunsFormatter(testrun)
      testrun_output = testrun_formatter.getOutput()
      if testrun_output:
         self._detailed_trs_result.append(testrun_output)

      # Script Level
      script_formatter = DetailScriptsFormatter(testrun)
      script_output = script_formatter.getOutput()
      if script_output:
         for script in script_output:
            self._detailed_scripts_result.append(script)

      # Machine Level
      machine_formatter = DetailMachineInfoFormatter(testrun)
      machine_output = machine_formatter.getOutput()
      if machine_output:
         for machine in machine_output:
            self._detailed_machines_result.append(machine)

   def getTestrunsGroupOutput(self, plain=True):
      """Generate testruns output, group by key.
      @plain: True, return output with plain text format
              False, return output with HTML format
      """
      if plain:
         log_flag = 'with plain text format'
      else:
         log_flag = 'with HTML format'
      logger.info("Generating testruns report %s...", log_flag)

      testruns_format_dict = {}
      # Generate each testrun's output
      for key, testruns in self._testrunsDict.items():
         testrunsOutput = []
         testruns_format_dict[key] = testrunsOutput
         for testrun in testruns:
            if plain:
               formatter = self._tr_plain_format_clazz(testrun)
            else:
               formatter = self._tr_html_format_clazz(testrun)
            output = formatter.getOutput()
            testrunsOutput.append(output)

      # Sort and add title / collector info for each testrun list
      outputs_format_dict = {}
      for key, testrunsOutput in testruns_format_dict.items():
         if plain:
            testrunsOutput = self._tr_plain_format_clazz.sorted(testrunsOutput)
         else:
            testrunsOutput = self._tr_html_format_clazz.sorted(testrunsOutput)

         # Add title
         if plain:
            title = self._tr_plain_format_clazz.getTitle()
         else:
            title = self._tr_html_format_clazz.getTitle()

         testrunsOutput.insert(0, title)
         tr_format_output = formatList2Str(testrunsOutput)

         if plain and self._print_tr_group_conclude_info:
            collector = self._reportDict[key]
            tr_format_output += '\n%s' % collector.getCollectorConsoleOutput()

         keyOutput = self._formatKeyOutput(key, plain)
         outputs_format_dict[keyOutput] = tr_format_output

      # Combine all output together, group by key
      outputs = []
      for keyoutput, testrunsOuput in outputs_format_dict.items():
         outputs.append('\n')
         outputs.append(keyoutput)
         outputs.append(testrunsOuput)

      return '\n'.join(outputs)

   def getBugResult(self):
      """Generate bug output.
            @plain: True, return output with plain text format
                    False, return output with HTML format
            """
      bug_dict = {}
      bug = []
      bug_output = None
      # Generate each testrun's output
      for key, testruns in self._testrunsDict.items():
         bugOutput = []
         bug_dict[key] = bugOutput
         for testrun in testruns:
            formatter = self._tr_html_format_clazz(testrun)
            bug += formatter._outputDict['Bug Id']
      bug = list(set(bug))
      if bug:
         bugfilename = 'bug.csv'
         bdmain(bug, bugfilename)
         bug_output = dailymain()
      return bug_output

   def getOverallHtmlReport(self):
      """generate overall HTML report, the info is only used for email
      """
      logger.info("Generating %s...", str(self._report_html_formatter))
      return self._report_html_formatter.getHtmlReport()

   def getOverallSummary(self):
      """generate overall summary which would be used for email title
      """
      return self._report_html_formatter.getSummary()

   def getDetailedTestrunsResult(self):
      """Return the detailed testrun level raw data
      """
      if self._detailed_trs_result:
         DetailTestrunsFormatter.sorted(self._detailed_trs_result)
         self._detailed_trs_result.insert(0, DetailTestrunsFormatter.getTitle())
         return self._detailed_trs_result
      else:
         return None

   def getDetailedScriptsResult(self):
      """Return the detailed scripts level raw data
      """
      if self._detailed_scripts_result:
         DetailScriptsFormatter.sorted(self._detailed_scripts_result)
         self._detailed_scripts_result.insert(0,
                                              DetailScriptsFormatter.getTitle())
         return self._detailed_scripts_result
      else:
         return None

   def getDetailedMachinesResult(self):
      """Return the detailed machine level raw data
      """
      if self._detailed_machines_result:
         DetailMachineInfoFormatter.sorted(self._detailed_machines_result)
         self._detailed_machines_result.insert(
                      0, DetailMachineInfoFormatter.getTitle())
         return self._detailed_machines_result
      else:
         return None

   def _groupTestrun(self, testrun):
      raise NotImplementedError("Please override function _groupTestrun()")

   def _formatKeyOutput(self, keyData, plain=True):
      raise NotImplementedError("Please override function _formatKeyOutput()")

   @staticmethod
   def reset_calculator():
      TestrunsCollector.reset_global_value()


class TestrunGroupsByWorkunit(_TestrunsGroup):
   """Group testruns by workunit
   """
   def __init__(self):
      super(TestrunGroupsByWorkunit, self).__init__(TrByWuPlainFormatter,
                                                    TrByWuHtmlFormatter,
                                                    ReporByWuHtmlFormatter)

   def _groupTestrun(self, testrun):
      """Group testruns by workunit id
      """
      wuData = testrun.getWorkunitData()
      self._appendTestrun(wuData, testrun)

   def _formatKeyOutput(self, wuData, plain):
      if plain:
         return 'Workunit %s -- Workload %s, Build %s, Area %s, Tester %s\n' % \
                (wuData.getId(), wuData.getWorkloadName(), wuData.getBuildInfo(),
                 wuData.getAreaName(), wuData.getTesterId())
      else:
         tester_id = wuData.getTesterId()
         tester_email_id = genHyperLink(tester_id,
                                        getCatHyperLink('tester', tester_id))
         keyInfo = 'Workunit %s -- Workload %s, Build %s, Area %s, Tester %s\n' % \
                   (wuData.getHtmlId(), wuData.getWorkloadName(),
                    wuData.getBuildInfo(), wuData.getAreaName(),
                    tester_email_id)
         return boldMsg(keyInfo)


class TestrunGroupsByFailedReason(_TestrunsGroup):
   """Group testruns by failed reason

   This class will ignore testrun which result is PASS
   """
   def __init__(self):
      super(TestrunGroupsByFailedReason, self).__init__(
                                             TrByFailedReasonPlainFormatter,
                                             TrByFailedReasonHtmlFormatter,
                                             ReportByFailedReasonHtmlFormatter,
                                             True)

      self._print_tr_group_conclude_info = False

   def _groupTestrun(self, testrun):
      result = testrun.getResult()
      errorMessages = testrun.getUnifiedErrorMessages()
      if result == RESULT_PASS:
         return

      for errorMessage in errorMessages:
         self._appendTestrun(errorMessage, testrun)

   def _formatKeyOutput(self, failedReason, plain=True):
      """Format Failed Reason output
      """
      failed_level, failed_info = failedReason
      failed_msg = '%s - %s\n' % (failed_level, failed_info)

      if plain:
         return failed_msg
      else:
         return boldMsg(failed_msg)


class TestrunGroupsByBuildInfo(_TestrunsGroup):
   """Group testruns by build info -- <branch-name>:<build-type>
   """
   def __init__(self, parser_log=True):
      super(TestrunGroupsByBuildInfo, self).__init__(TrByBuildInfoPlainFormatter,
                                                     TrByBuildInfoHtmlFormatter,
                                                     ReportByBuildInfoHtmlFormatter,
                                                     parser_log=parser_log)

   def _groupTestrun(self, testrun):
      """Group testrun by build info
      """
      buildInfo = testrun.getWorkunitData().getBuildInfo()
      self._appendTestrun(buildInfo, testrun)

   def _formatKeyOutput(self, buildInfo, plain):
      if plain:
         return 'Build Info %s' % buildInfo
      else:
         return 'Build Info %s' % boldMsg(buildInfo)


class TestrunGroupsByMachineInfo(_TestrunsGroup):
   """Group testruns by machine info
   """
   def __init__(self, parser_log=True):
      super(TestrunGroupsByMachineInfo, self).__init__(TrByMachineInfoPlainFormatter,
                                                       TrByMachineInfoHtmlFormatter,
                                                       ReportByMachineInfoHtmlFormatter,
                                                       parser_log=parser_log)

   def _groupTestrun(self, testrun):
      """Group testrun by build info
      """
      machineInfo = testrun.getHostNames()
      if 'Nimbus ESX' in machineInfo:
         # Convert 'N Nimbus ESX' to 'Nimbus ESX'
         machineInfo = 'Nimbus ESX'

      machines = machineInfo.split(',')
      for machine in machines:
         machine = machine.strip()
         # Each testrun may contain M machines,
         # add each machine - testrun mapping
         self._appendTestrun(machine, testrun)

   def _formatKeyOutput(self, machineInfo, plain):
      if plain:
         return 'Machine %s' % machineInfo
      else:
         return 'Machine %s' % boldMsg(machineInfo)


def generateReport(group, limitDay, limitNumber, wuIds=[], wlNames=[],
                   testerIds=[], areaIds=[], areaNames=[], branchNames=[],
                   bldTypes=[], testrunIds=[]):
   """Generate report data based on group instance and parser info

   @return: [overall_output_in_html_format, detail_output_in_html_format,
            attach_files]
   """
   overall_output = None
   detail_output = None
   bug_output = None
   attach_files = []
   if testrunIds:
      group.retrieveTestrunsById(testrunIds)
   else:
      group.retrieveTestruns(limitDay, limitNumber, wuIds, wlNames, testerIds,
                             areaIds, areaNames, branchNames, bldTypes)

   group.groupTestrunToDict()

   if not group.validTestrunsGroup():
      logger.warn("Please try to expand testruns data by "
                  "define command options -d limitDay | -l limitNumber")
      logger.warn("Or, please check command options for "
                  "filter testruns are correct")
   else:
      plain_output = group.getTestrunsGroupOutput()
      logger.info(plain_output)

      detail_output = group.getTestrunsGroupOutput(plain=False)
      overall_output = group.getOverallHtmlReport()
      detailed_testrun = group.getDetailedTestrunsResult()
      detailed_script = group.getDetailedScriptsResult()
      detailed_machine = group.getDetailedMachinesResult()

      bug_output = group.getBugResult()

      attach_files = [write2File(plain_output, 'Testruns output in plain text')]
      #buglist = group.
      detailed_info_list = []
      if detailed_testrun:
         detailed_info_list.append(['Testrun Level', detailed_testrun])
      if detailed_script:
         detailed_info_list.append(['Script Level', detailed_script])
      if detailed_machine:
         detailed_info_list.append(['Machine Level', detailed_machine])

      if detailed_info_list:
         try:
            attach_files.append(write2Xls(detailed_info_list,
                                          'Testruns detailed raw data'))
         except Exception as e:
            logger.warn("Failed to generate detailed raw data in excel file."
                        " Reason: %s" % str(e))

   return [overall_output, detail_output, bug_output, attach_files]

def generateReportByParser(group, parser):
   """Generate report data based on group instance and parser info

   @return: [overall_output_in_html_format, detail_output_in_html_format,
            attach_files]
   """
   return generateReport(group, parser.limitDay, parser.limitNumber,
                         parser.wuIds, parser.wlNames, parser.testerIds,
                         parser.areaIds, parser.areaNames, parser.branchNames,
                         parser.bldTypes, parser.testrunIds)


"""Below code is for testing purpose
"""
if __name__ == '__main__':

   #group = TestrunGroupsByWorkunit()
   group = TestrunGroupsByFailedReason()
   group.retrieveTestruns(1, 30,
                          branchNames=['vmcore-main'],
                          areaIds=['2', '13', '61'],
                          bldTypes=['obj'])
   print group.getTestrunsGroupOutput(True)

   #overallOutput = group.getOverallHtmlReport()
   overallOutput = ''
   output = group.getTestrunsGroupOutput(False)

   #print group.genDetailedTestrunsResult()
   #print group.genDetailedScriptsResult()

   #from Common.utils.emailUtil import sendEmail
   #sendEmail('test', '%s\n\n%s' % (overallOutput, output))

