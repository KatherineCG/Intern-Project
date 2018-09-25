'''Library to collect status from a list of testruns
Created on Sep 2, 2016

@author: kaiyuanli
'''
from Common.utils.commonUtil import formatList2Str
from Common.utils.constants import NOT_AVALIABLE, RESULT_PASS, RESULT_PSOD,\
   RESULT_FAIL, RESULT_TIMEOUT, RESULT_INVALID

from datetime import timedelta

def getPercentage(rate):
   percentage = '%0.1f%%' % float(rate * 100)
   if percentage.endswith('.0%'):
      percentage = percentage[0: percentage.index('.0%')] + '%'
   return percentage


class TestrunsCollector():
   """Collect data from a list of testruns
   """
   TOTAL_RESULT_DICT = {}
   TOTAL_UNTRIAGED_TESTRUNS = 0
   TOTAL_TESTRUNS = 0
   TOTAL_TESTS = 0
   TOTAL_PASSED_TESTS = 0

   def __init__(self, testruns):
      self._testruns = testruns
      self._total = len(self._testruns)
      TestrunsCollector.TOTAL_TESTRUNS += self._total
      self._total_tests = 0
      self._passed_tests = 0
      self._untriaged_testruns = 0
      self._first_start_time = None
      self._last_start_time = None
      self._start_cln = None
      self._end_cln = None
      self._result_testruns_dict = {}
      self._total_pass_seconds = 0
      self._calculateData()

   def _calculateData(self):
      def __update(minInfo, maxInfo, updateInfo):
         if minInfo is None or updateInfo < minInfo:
            minInfo = updateInfo
         if maxInfo is None or updateInfo > maxInfo:
            maxInfo = updateInfo
         return minInfo, maxInfo

      for testrun in self._testruns:
         try:
            cln = int(testrun.getCLN())
            self._start_cln, self._end_cln = __update(self._start_cln,
                                                      self._end_cln, cln)
         except:
            # If product source code is managed by git not perforce
            # the CLN is a string rather than int.
            # Then there is no need to record and show start / end cln
            pass

         self._first_start_time, self._last_start_time = __update(self._first_start_time,
                                                                  self._last_start_time,
                                                                  testrun.getStartTime())

         result = testrun.getResult()
         if result not in self._result_testruns_dict:
            self._result_testruns_dict[result] = []
         self._result_testruns_dict[result].append(testrun)

         if result not in TestrunsCollector.TOTAL_RESULT_DICT:
            TestrunsCollector.TOTAL_RESULT_DICT[result] = []
         TestrunsCollector.TOTAL_RESULT_DICT[result].append(testrun)

         if result == RESULT_PASS:
            self._total_pass_seconds += testrun.getRunTime().seconds

         if testrun.isNeedTriage():
            self._untriaged_testruns += 1
            TestrunsCollector.TOTAL_UNTRIAGED_TESTRUNS += 1

         self._total_tests += testrun.getTotalTestNum()
         TestrunsCollector.TOTAL_TESTS += testrun.getTotalTestNum()
         self._passed_tests += testrun.getPassedTestNum()
         TestrunsCollector.TOTAL_PASSED_TESTS += testrun.getPassedTestNum()

   def getTotal(self):
      return self._total

   def getTotalTestNum(self):
      return self._total_tests

   def getPassedTestNum(self):
      return self._passed_tests

   def getResultTestrunsDict(self):
      return self._result_testruns_dict

   def _getResultTimes(self, result):
      if result not in self._result_testruns_dict:
         return 0
      else:
         return len(self._result_testruns_dict[result])

   def getTestruns(self):
      return self._testruns

   def getClnRange(self):
      if self._start_cln and self._end_cln:
         return '[%d, %d]' % (self._start_cln, self._end_cln)
      else:
         return None

   def getFirstStartTime(self):
      return self._first_start_time

   def getEndStartTime(self):
      return self._end_start_time

   def getAveragePassTime(self):
      if self._total_pass_seconds == 0:
         return NOT_AVALIABLE
      else:
         avg_pass_seconds = self._total_pass_seconds / self.getPassTimes()
         return str(timedelta(seconds=avg_pass_seconds))

   def getPassRate(self):
      if self._total == 0:
         return 0
      else:
         rate = float(self.getPassTimes()) / float(self._total)
         return rate

   def getPassRatePercentage(self):
      return getPercentage(self.getPassRate())

   def getPassRateFriendlyInfo(self):
      pass_in_total = "%s / %s" % (self.getPassTimes(), self._total)
      pass_percentage = self.getPassRatePercentage()

      return '%s (%s)' % (pass_in_total, pass_percentage)
 
   def getCollectorConsoleOutput(self):
      """Get collector console output
      """
      report_list = [['First Start Time', self._first_start_time],
                     ['Last Start Time', self._last_start_time]]
      if self.getClnRange():
         report_list.append(['Changeset Range', self.getClnRange()])

      for result, testruns in self._result_testruns_dict.items():
         result_info = '%s / %s' % (len(testruns), self._total)
         report_list.append(['%s Testruns' % result, result_info])

      report_list.append(['PASS Rate', self.getPassRatePercentage()])
      return '\n%s\n' % formatList2Str(report_list, ' : ',
                                       appendIndex=False, title=False)

   def getPassTimes(self):
      return self._getResultTimes(RESULT_PASS)

   def getNonPassTimes(self):
      return self.getTotal() - self.getPassTimes()

   def getPsodTimes(self):
      return self._getResultTimes(RESULT_PSOD)

   def getFailedTimes(self):
      return self._getResultTimes(RESULT_FAIL)

   def getTimeoutTimes(self):
      return self._getResultTimes(RESULT_TIMEOUT)

   def getInvalidTimes(self):
      return self._getResultTimes(RESULT_INVALID)

   def getUnTriagedTimes(self):
      return self._untriaged_testruns

   def getUnTriagedRatePercentage(self):
      non_passed_times = self.getTotal() - self.getPassTimes()
      if non_passed_times == 0:
         # All PASSed, no need to triage then
         return getPercentage(0)
      else:
         rate = float(self.getUnTriagedTimes()) / float(non_passed_times)
         return getPercentage(rate)

   def getUnTriagedRateFriendlyInfo(self):
      non_passed_times = self.getTotal() - self.getPassTimes()
      untriaged_in_total = '%s / %s' % (self.getUnTriagedTimes(),
                                        non_passed_times)

      if non_passed_times == 0:
         untriaged_percentage = getPercentage(0)
      else:
         untriaged_rate = float(self.getUnTriagedTimes()) / float(non_passed_times)
         untriaged_percentage = getPercentage(untriaged_rate)
      return '%s (%s)' % (untriaged_in_total, untriaged_percentage)

   def getTestLevelPassRateFridentlyInfo(self):
      """Return test level pass rate
      """
      if self._total_tests == 0:
         # No test info found
         return NOT_AVALIABLE
      else:
         pass_in_total = "%s / %s" % (str(self._passed_tests),
                                      str(self._total_tests))

         pass_rate = float(self._passed_tests) / float(self._total_tests)
         pass_percentage = getPercentage(pass_rate)
         return '%s (%s)' % (pass_in_total, pass_percentage)

   def getTestLevelPassRatePercentage(self):
      """Return test level pass rate percentage
      """
      if self._total_tests == 0:
         # No test info found
         return NOT_AVALIABLE
      else:
         rate = float(self._passed_tests) / float(self._total_tests)
         return getPercentage(rate)

   @staticmethod
   def _getTotalResultTimes(result):
      if result not in TestrunsCollector.TOTAL_RESULT_DICT:
         return 0
      else:
         return len(TestrunsCollector.TOTAL_RESULT_DICT[result])

   @staticmethod
   def getTotalTimes():
      return TestrunsCollector.TOTAL_TESTRUNS

   @staticmethod
   def getTotalPassTimes():
      return TestrunsCollector._getTotalResultTimes(RESULT_PASS)

   @staticmethod
   def getTotalNonPassTimes():
      return (TestrunsCollector.getTotalTimes() -
              TestrunsCollector.getTotalPassTimes())

   @staticmethod
   def getTotalPsodTimes():
      return TestrunsCollector._getTotalResultTimes(RESULT_PSOD)

   @staticmethod
   def getTotalFailedTimes():
      return TestrunsCollector._getTotalResultTimes(RESULT_FAIL)

   @staticmethod
   def getTotalTimeoutTimes():
      return TestrunsCollector._getTotalResultTimes(RESULT_TIMEOUT)

   @staticmethod
   def getTotalInvalidTimes():
      return TestrunsCollector._getTotalResultTimes(RESULT_INVALID)

   @staticmethod
   def getTotalPassRateFriendlyInfo():
      pass_in_total = '%s / %s' % (TestrunsCollector.getTotalPassTimes(),
                                   TestrunsCollector.getTotalTimes())

      total = TestrunsCollector.getTotalTimes()
      if not total:
         pass_rate = getPercentage(0)
      else:
         pass_perc = float(TestrunsCollector.getTotalPassTimes()) / float(total)
         pass_rate = getPercentage(pass_perc)

      return "%s (%s)" % (pass_in_total, pass_rate)

   @staticmethod
   def getTotalUnTriagedTimes():
      return TestrunsCollector.TOTAL_UNTRIAGED_TESTRUNS

   @staticmethod
   def getTotalUnTriagedRatePercentage():
      total_untriage_times = TestrunsCollector.getTotalUnTriagedTimes()
      total_nonpassed_times = TestrunsCollector.getTotalNonPassTimes()

      if total_nonpassed_times == 0:
         # All PASS, no need to triage then
         return getPercentage(0)

      rate = float(total_untriage_times) / float(total_nonpassed_times)
      return getPercentage(rate)

   @staticmethod
   def getTotalUnTriagedRateFriendlyInfo():
      total_untriage_times = TestrunsCollector.getTotalUnTriagedTimes()
      total_nonpassed_times = TestrunsCollector.getTotalNonPassTimes()

      untriaged_in_total = '%s / %s' % (total_untriage_times,
                                        total_nonpassed_times)

      if total_nonpassed_times == 0:
         # All PASS, no need to triage then
         perc = getPercentage(0)
      else:
         rate = float(total_untriage_times) / float(total_nonpassed_times)
         perc = getPercentage(rate)

      return '%s (%s)' % (untriaged_in_total, perc)

   @staticmethod
   def getTotalTestLevelPassRateFriendlyInfo():
      """Return total test level pass rate
      """
      if TestrunsCollector.TOTAL_TESTS == 0:
         # No test info found
         return NOT_AVALIABLE
      else:
         pass_in_total = "%s / %s" % (str(TestrunsCollector.TOTAL_PASSED_TESTS),
                                      str(TestrunsCollector.TOTAL_TESTS))

         pass_rate = float(TestrunsCollector.TOTAL_PASSED_TESTS) / \
                     float(TestrunsCollector.TOTAL_TESTS)
         pass_percentage = getPercentage(pass_rate)
         return '%s (%s)' % (pass_in_total, pass_percentage)

   def getTriageInfo(self):
      """Return (triaged_data_list, need_triage_testrun)
      """
      triaged_data = set()
      need_triage_testruns = []
      for testrun in self.getTestruns():
         triagedInfo = testrun.getTriageInfo()
         if testrun.isNeedTriage():
            need_triage_testruns.append(testrun.getHtmlId())
         elif isinstance(triagedInfo, list):
            for info in triagedInfo:
               triaged_data.add(info.getHtmlId())
         elif triagedInfo:
            triaged_data.add(triagedInfo)

      return (list(triaged_data), need_triage_testruns)

   @staticmethod
   def reset_global_value():
      TestrunsCollector.TOTAL_RESULT_DICT = {}
      TestrunsCollector.TOTAL_UNTRIAGED_TESTRUNS = 0
      TestrunsCollector.TOTAL_TESTRUNS = 0
      TestrunsCollector.TOTAL_TESTS = 0
      TestrunsCollector.TOTAL_PASSED_TESTS = 0


"""Below code is for testing purpose
"""
if __name__ == '__main__':
   from Common.cat.object.testrun import Testrun
   trDatas1 = Testrun.queryTestrunDatas(1, 10, areaIds=[2], branchNames=['vmcore-main'],
                                        parserLog=False)
   trDatas2 = Testrun.queryTestrunDatas(1, 10, areaIds=[13], branchNames=['vmcore-main'],
                                       parserLog=False)
   collector1 = TestrunsCollector(trDatas1)
   collector2 = TestrunsCollector(trDatas2)

   for collector in [collector1, collector2]:
      print('\nConsole output:\n%s\n' % collector.getCollectorConsoleOutput())
      triage_data, need_triaged_testruns = collector.getTriageInfo()
      print('Triaged data:\n%s\n' % triage_data)
      print('Triaged testruns:\n%s\n' % need_triaged_testruns)

      print('Total: %s' % collector.getTotal())
      print('PASS : %s' % collector.getPassTimes())
      print('FAIL: %s' % collector.getFailedTimes())
      print('PSOD: %s' % collector.getPsodTimes())
      print('TIMEOUT: %s' % collector.getTimeoutTimes())
      print('un-triaged: %s' % collector.getUnTriagedTimes())
      print('\n')

      print('PASS rate: %s' % collector.getPassRatePercentage())
      print('un-triaged rate: %s' % collector.getUnTriagedRatePercentage())
      print('-------------------------------')
      print('-------------------------------')

   print ('\n\n')
   print("Overall total: %s" % TestrunsCollector.getTotalTimes())
   print("Overall PASS: %s" % TestrunsCollector.getTotalPassTimes())
   print("Overall FAIL: %s" % TestrunsCollector.getTotalFailedTimes())
   print("Overall PSOD: %s" % TestrunsCollector.getTotalPsodTimes())
   print("Overall TIMEOUT: %s" % TestrunsCollector.getTotalTimeoutTimes())
   print("Overall INVALID: %s" % TestrunsCollector.getTotalInvalidTimes())
   print("Overall unTriaged: %s" % TestrunsCollector.getTotalUnTriagedTimes())
   print('\n')

   print("Overall PASS Rate: %s" % TestrunsCollector.getTotalPassRatePercentage())
   print("Overall untriaged Rate: %s" % TestrunsCollector.getTotalUnTriagedRatePercentage())
