#!/build/toolchain/lin64/python-2.7.6/bin/python -u

''' Utility library to parse <cat-testrun-result-dir>/testinfo.csv
Created on Apr 12, 2018

@author: kaiyuanli
'''
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from Common.utils.restAPI import urlOpen
from Common.utils.constants import RESULT_FAIL, RESULT_PASS


class TestInfo(object):
   """Class to read / parse test result from testinfo.csv
   """

   def __init__(self, root_dir):
      """Init TestInfo instance, raise exception if file not exist
      """
      self._testinfo_csv_url = os.path.join(root_dir, 'testinfo.csv')
      try:
         self._testinfo = urlOpen(self._testinfo_csv_url, True)
      except:
         raise Exception("Failed to find %s" % self._testinfo_csv_url)

      self._test_result_list = []
      self._non_passed_test_result_list = []
      self._total_tests = 0
      self._failed_tests = 0

   def parseTestInfoLog(self):
      test_info_list = self._testinfo.strip().split('\n')
      for test_info in test_info_list:
         if not test_info:
            continue

         test_info = test_info.split(',')
         testname = test_info[1]
         is_pass = True

         if test_info[2] == '0':
            testresult = RESULT_PASS
         else:
            is_pass = False
            testresult = RESULT_FAIL

         try:
            execution = test_info[3]
         except:
            execution = 'N/A'

         self._test_result_list.append([testresult, testname, execution])
         self._total_tests += 1

         if not is_pass:
            self._non_passed_test_result_list.append([testresult, testname])
            self._failed_tests += 1

   def getTestInfoUrl(self):
      return self._testinfo_csv_url

   def getDetailedTestResults(self):
      """Return test result list, each item is in format
         (testresult, testname, execution)
      """
      return self._test_result_list

   def getNonPassedTestList(self):
      """Return non-passed test list, each item is in format (testresult, testname)
      """
      return self._non_passed_test_result_list

   def getNonPassedTestInfo(self):
      """Return non-passed test info as a str
      """
      readable_info_list = set()
      for non_passed_test in self._non_passed_test_result_list:
         readable_info_list.add('%s - %s' % (non_passed_test[0],
                                             non_passed_test[1]))

      return '\n'.join(list(readable_info_list))

   def getTotalTestNum(self):
      return self._total_tests

   def getFailedTestNum(self):
      return self._failed_tests


"""Below code is for test purpose
"""
if __name__ == '__main__':
   from argparse import ArgumentParser

   from Common.cat.object.testrun import Testrun

   parser = ArgumentParser(description='Show test script running result by parser testinfo.csv')

   parser.add_argument('-t', type=str, dest='testrunIds', action='append',
                       help="Testrun IDs")
   args = parser.parse_args()

   trIds = args.testrunIds

   trDatas = [Testrun(trId) for trId in trIds]
   for trId in trIds:
      tr = Testrun(trId)
      tr.initCatRawInfo()
      resultDir = tr.getResultDirUrl()
      testInfoLog = TestInfo(resultDir)
      testInfoLog.parseTestInfoLog()
      print("\n\nTestrun ID: %s, testinfo.csv log url: %s" % (trId,
                                 testInfoLog.getTestInfoUrl()))

      test_result_list = testInfoLog.getDetailedTestResults()

      print("\nDetailed %d script(s) info:" % len(test_result_list))
      print("============================")
      for detail in test_result_list:
         print(' | '.join(detail))

      print("\nError readable message:")
      print("=========================")
      print(testInfoLog.getNonPassedTestInfo())

      print("\nFailed Rate: %s / %s\n" % (testInfoLog.getFailedTestNum(),
                                          testInfoLog.getTotalTestNum()))
