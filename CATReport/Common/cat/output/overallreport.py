''' Library to define overall report output.

Overall report is only used for email,
hence this libary only handles HTML formatter

Created on Sep 7, 2016

@author: kaiyuanli
'''
from Common.cat.object.workunit import Workunit
from Common.cat.testruncollector import TestrunsCollector
from Common.testesx.constants import LEVEL_PRIORITY
from Common.utils.commonUtil import insertIndex2List, removeEmptyColumn
from Common.utils.htmlUtil import colorMsg, tableMsg, boldMsg


EXPLIAN_UNTRIAGE_RATE = '* Un-Triaged Rate = (#Un-Triaged Testrun / #Non-PASS Testrun) * 100%'
EXPLAIN_AVERAGE_EXEC = '* Average Run Time: The average run time of PASS testruns'


class _ReportHtmlFormatter(object):
   """Base class for report html formatter
   """
   TITLE = None     # override
   EXPLAINS = None   # override

   def __init__(self, report_dict):
      assert(self.TITLE)
      self._report_dict = report_dict
      self._total_info = None

   def getHtmlReport(self):
      """Return HTML report"""
      # Generate basic report info
      report = []
      for key, details in self._report_dict.items():
         output = self._getReportEntry(key, details)
         report.append(output)

      report = self._sorted(report)
      insertIndex2List(report)
      report.insert(0, self.TITLE)

      self._setTotalInfo()
      if self._getTotalInfo():
         report.insert(1, self._getTotalInfo())

      # Remove empty table and transfer to HTML format
      report = removeEmptyColumn(report)
      report = tableMsg(report)
      if self.EXPLAINS:
         for explain in self.EXPLAINS:
            report += '\n%s' % explain
      return report

   def getSummary(self):
      # Return report summary, which will be used for email subject
      raise NotImplementedError("Please override function getSummary()")

   def _setTotalInfo(self):
      # Optional function for child class to
      # set total information in overall report at last
      pass

   def _getTotalInfo(self):
      return self._total_info

   def _getReportEntry(self, key, collector):
      # Get one line entry for report
      raise NotImplementedError("Please override function _getReportEntry()")

   def _sorted(self, report_info):
      # Sorted the report_info
      raise NotImplementedError("Please override function _sorted()")

   def _convertZero2Empty(self, info):
      """Covert zero value to None,
      this will help removeEmptyColumn function to remove Column filled up with 0
      """
      if info == 0:
         return ''
      else:
         return info


class ReporByWuHtmlFormatter(_ReportHtmlFormatter):
   """Class to define html output for testruns grouped by workunit
   """
   TITLE = ["#", 'Workunit<br>ID', 'Workload<br>Name Prefix',
            'Build Info', 'Average<br>Run Time*', 'Testrun Level<br>Pass Rate',
            'Testscript Level<br>Pass Rate', 'Un-Triaged<br>Rate*',
            'Triage Info', 'Non-Triaged<br>Testruns']

   EXPLAINS = [EXPLAIN_AVERAGE_EXEC, EXPLIAN_UNTRIAGE_RATE]

   def __str__(self):
      return 'overall report group by workunit'

   def _getReportEntry(self, wuData, collector):
      # report_dict -- {wuData: collector}
      workloadName = wuData.getWorkloadData().getShortenVersionWorkloadName()
      if collector.getPassRate() < 0.5:
         workloadName = colorMsg(workloadName)

      buildInfo = wuData.getBuildInfo()
      triaged_data, need_triage_testruns = collector.getTriageInfo()

      return [wuData.getHtmlId(), workloadName, buildInfo,
              collector.getAveragePassTime(),
              collector.getPassRateFriendlyInfo(),
              collector.getTestLevelPassRateFridentlyInfo(),
              collector.getUnTriagedRateFriendlyInfo(),
              '<br>'.join(triaged_data),
              '<br>'.join(need_triage_testruns)]

   def _sorted(self, output_list):
      def by_pass_rate(info):
         # pass_rate first, then branch, then workload
         pass_rate_perc = info[4]
         pass_rate = pass_rate_perc[pass_rate_perc.index('(') + 1:
                                    pass_rate_perc.index('%')]
         return (float(pass_rate), info[3], info[1])

      return sorted(output_list, key=by_pass_rate)

   def _setTotalInfo(self):
      self._total_info = ['', boldMsg('Overall'), '', '', '',
            boldMsg(TestrunsCollector.getTotalPassRateFriendlyInfo()),
            boldMsg(TestrunsCollector.getTotalTestLevelPassRateFriendlyInfo()),
            boldMsg(TestrunsCollector.getTotalUnTriagedRateFriendlyInfo()),
            '', '']

   def getSummary(self):
      pass_rate = 0
      need_triage = 0
      wu_num = len(self._report_dict.keys())
      for collector in self._report_dict.values():
         pass_rate += collector.getPassRate()
         testruns = collector.getTestruns()
         for testrun in testruns:
            if testrun.isNeedTriage():
               need_triage += 1

      pass_rate = float(pass_rate) / float(wu_num)
      percentage = '%0.1f%%' % float(pass_rate * 100)
      if percentage.endswith('.0%'):
         percentage = percentage[0: percentage.index('.0%')] + '%'

      summary = '[%s Stable]' % percentage
      if need_triage:
         summary += '[%d Testruns Non-Triaged]' % need_triage

      common_info = Workunit.getWorkunitCommonInfo(self._report_dict.keys())
      return '%s CAT Testrun Report for %s' % (summary, common_info)


class ReportByFailedReasonHtmlFormatter(_ReportHtmlFormatter):
   """Class to define html output for testruns grouped by failed reason
   """
   TITLE = ['#', 'Failed-Level', 'Failed-Reason', '#Testrun', 'Triage Info']

   def __str__(self):
      return 'overall report group by failed reason'

   def _getReportEntry(self, failedReason, collector):
      # report_dict -- {failedReason: collector}
      failed_level, failed_info = failedReason
      triaged_data, _ = collector.getTriageInfo()
      return [failed_level.strip(), failed_info.strip(), collector.getTotal(),
              '<br>'.join(triaged_data)]

   def _sorted(self, output_list):
      def by_failed_level(info):
         # sorted by failed level, then testrun number
         failed_level = info[0].upper()
         testrun_number = info[2]
         try:
            level_index = LEVEL_PRIORITY.index(failed_level)
         except:
            level_index = -1

         return (level_index, testrun_number)

      return sorted(output_list, key=by_failed_level, reverse=True)

   def getSummary(self):
      failed_reason_number = len(self._report_dict.keys())
      need_triage = 0
      for collector in self._report_dict.values():
         testruns = collector.getTestruns()
         for testrun in testruns:
            if testrun.isNeedTriage():
               need_triage += 1

      summary = '[%d Failed Reason%s]' % (failed_reason_number,
                                          '' if failed_reason_number == 1 else 's')
      if need_triage:
         summary += '[%d Testruns Non-Triaged]' % need_triage

      workunits = set()
      for collector in self._report_dict.values():
         testruns = collector.getTestruns()
         for testrun in testruns:
            workunits.add(testrun.getWorkunitData())

      common_info = Workunit.getWorkunitCommonInfo(list(workunits))
      return '%s CAT Testrun Failed Reasons Report for %s' % (summary, common_info)


class ReportByBuildInfoHtmlFormatter(_ReportHtmlFormatter):
   """Class to define html output for testruns grouped by build info
   """
   TITLE = ['#', 'Build Info', 'Testrun Level PASS Rate',
            'Testscript Level Pass Rate', 'Un-Triaged Rate*',
            'Un-Triaged<br>Rate*']
   EXPLAINS = [EXPLIAN_UNTRIAGE_RATE]

   def __str__(self):
      return 'overall report group by build info'

   def _getReportEntry(self, build_info, collector):
      return [build_info, collector.getPassRateFriendlyInfo(),
              collector.getTestLevelPassRateFridentlyInfo(),
              collector.getUnTriagedRateFriendlyInfo()]

   def _sorted(self, output_list):
      def by_pass_rate(info):
         # pass_rate first, then branch
         pass_rate_perc = info[1]
         pass_rate = pass_rate_perc[pass_rate_perc.index('(') + 1:
                                    pass_rate_perc.index('%')]
         return (float(pass_rate), info[0])

      return sorted(output_list, key=by_pass_rate)

   def getSummary(self):
      build_infos = self._report_dict.keys()
      branch_infos = set()
      for build_info in build_infos:
         # Sample build_info -- vmcore-main:obj
         branch, _, _ = build_info.partition(':')
         branch_infos.add(branch)

      branch_infos = sorted(list(branch_infos), reverse=True)
      test_level_pass_info = TestrunsCollector.getTotalTestLevelPassRateFriendlyInfo()
      return '%s Test Scripts are PASSED for Branch %s' \
              % (test_level_pass_info, ', '.join(branch_infos))

class ReportByMachineInfoHtmlFormatter(_ReportHtmlFormatter):
   """Class to define html output for testruns grouped by build info
   """
   TITLE = ['#', 'MachineName', 'PASS<br>Rate', '#Total', '#PASS',
            '#PSOD', '#FAIL', '#TIMEOUT', '#INVALID', '#Non-PASS']

   def __str__(self):
      return 'overall report group by machine info'

   def _getReportEntry(self, machine_info, collector):
      if collector.getPassRate() < 0.5:
         machine_info = colorMsg(machine_info)

      return [machine_info, collector.getPassRatePercentage(),
              collector.getTotal(), collector.getPassTimes(),
              self._convertZero2Empty(collector.getPsodTimes()),
              self._convertZero2Empty(collector.getFailedTimes()),
              self._convertZero2Empty(collector.getTimeoutTimes()),
              self._convertZero2Empty(collector.getInvalidTimes()),
              collector.getNonPassTimes()]

   def _sorted(self, output_list):
      def by_pass_rate(info):
         # pass rate first,  machine name later
         pass_rate_percentage = info[1]
         pass_rate = pass_rate_percentage[0:pass_rate_percentage.index('%')]
         return (float(pass_rate), info[0])

      return sorted(output_list, key=by_pass_rate, reverse=False)

   def getSummary(self):
      pass_rate = 0
      machine_infos = self._report_dict.keys()
      machine_infos = sorted(list(machine_infos), reverse=True)
      machine_num = len(machine_infos)

      for collector in self._report_dict.values():
         pass_rate += collector.getPassRate()

      pass_rate = float(pass_rate) / float(machine_num)
      percentage = '%0.1f%%' % float(pass_rate * 100)
      if percentage.endswith('.0%'):
         percentage = percentage[0: percentage.index('.0%')] + '%'

      summary = '[%s Stable]' % percentage

      return ('%s CAT Machine Stability Report for %s machines including %s, etc.'
              % (summary, machine_num, machine_infos[0]))
