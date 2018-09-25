"""CAT 'testrun' Library
"""
import itertools

from Common.cat.lib.jsonHandler import addId, addIds, getId
from Common.cat.lib.catApi import postResultToCat, patchResultToCat, queryCatInfo
from Common.logparser.testinfo import TestInfo
from Common.testesx.parser.testesxparser import TestesxLog
from Common.utils.commonUtil import DATE_FORMAT_CAT, getExecutionTime,\
                                    getTimeDeltaInMinutes, SCRIPT_USER
from Common.utils.constants import CAT_PA_RESULT_BASE, CAT_WDC_RESULT_BASE,\
                                   RESULT_INVALID, RESULT_INVALID_INFRA,\
                                   RESULT_PASS
from Common.utils.logger import getLogger

from area import Area
from bugzilla import Bug
from build import Build
from catdata import CatData
from helpnow import Helpnow
from machine import Machine
from workunit import Workunit
from deliverable import Deliverable

logger = getLogger()

KW_STILL_RUNNING = 'Still-Running'
KW_IGNORED = 'Ignored'
KW_TRIAGE_ALERT = 'NeedTriage'

TEST_TYPE = (GENERAL, TESTESX) = list(range(2))

class Testrun(CatData):
   """Class defined the basic single Testrun Data info
   """
   _objType = 'testrun'
   _leafNode = False
   _subDataMap = {}

   def initCatRawInfo(self):
      super(Testrun, self).initCatRawInfo()

      # Initialize root data
      self._is_valid = True
      self._test_result_log = None
      self._test_type = GENERAL
      self._total_tests = 0
      self._failed_tests = 0

      self._tester_id = self.getIdFromCatObj('tester')
      self._workunit_id = self.getIdFromCatObj('workunit')
      self._deliverable_id = self.getIdFromCatObj('sitedeliverable', 'deliverable')
      self._machine_ids = self.getIdsFromCatObj('machines', 'machine')
      self._result = self.getValueFromCatObj('result')
      self._result_dir = self.getValueFromCatObj('resultsdir')
      self._start_time = self.getValueFromCatObj('starttime')
      self._end_time = self.getValueFromCatObj('endtime')
      if 'PA' in self._result_dir:
         self._http_result_dir = '%s%s' % (CAT_PA_RESULT_BASE, self._result_dir)
      else:
         self._http_result_dir = '%s%s' % (CAT_WDC_RESULT_BASE, self._result_dir)

      if self._result:
         self._run_time = getExecutionTime(self._start_time, self._end_time,
                                           DATE_FORMAT_CAT)
         if self._result == RESULT_INVALID_INFRA:
            self._result = RESULT_INVALID
      else:
         self._result = KW_STILL_RUNNING
         self._run_time = KW_STILL_RUNNING
         self._end_time = KW_STILL_RUNNING

      self._run_time_in_minutes = getTimeDeltaInMinutes(self._run_time)

      self._ignored = self.getValueFromCatObj('ignored')
      self._triage_time = self.getValueFromCatObj('triagetime')

      self._bug_objs = self._catObj['bugs']
      self._ticket_objs = self._catObj['helpnows']

      self._need_triage = False
      if self._run_time != KW_STILL_RUNNING and self._result != RESULT_PASS:
         if not self._triage_time:
            self._need_triage = True

      for sub_id in [self._workunit_id, self._deliverable_id]:
         if sub_id is None:
            # If sub id is None, this testrun is invalid as its RestAPI
            # information is not entire
            self._is_valid = False
            return

      # Initialize sub data
      Testrun._addSubData(Workunit, self._workunit_id)
      Testrun._addSubData(Deliverable, self._deliverable_id)

      for machine_id in self._machine_ids:
         Testrun._addSubData(Machine, machine_id)

      for bug_obj in self._bug_objs:
         Testrun._addSubData('bug_obj', bug_obj['id'], bug_obj)

      for ticket_obj in self._ticket_objs:
         Testrun._addSubData('ticket_obj', ticket_obj['id'], ticket_obj)

   @classmethod
   def initSubDataMap(cls):
      super(Testrun, cls).initSubDataMap()
      if 'bug_obj' in cls._subDataMap:
         bug_data = cls._getSubDataValue('bug_obj')
         for bug_id in bug_data.keys():
            bug_obj = bug_data[bug_id]
            if isinstance(bug_obj, dict):
               bug_data[bug_id] = Bug(bug_id, bug_obj)
               bug_data[bug_id].initCatRawInfo()

      if 'ticket_obj' in cls._subDataMap:
         ticket_data = cls._getSubDataValue('ticket_obj')
         for ticket_id in ticket_data.keys():
            ticket_obj = ticket_data[ticket_id]
            if isinstance(ticket_obj, dict):
               ticket_data[ticket_id] = Helpnow(ticket_id, ticket_obj)
               ticket_data[ticket_id].initCatRawInfo()

      cls._raw_initialized = True

   def initReadableInfo(self, parserLog=True):
      super(Testrun, self).initReadableInfo()
      self._deliverable_data = Testrun._getSubDataValue(Deliverable,
                                                        self._deliverable_id)
      self._cln = self._deliverable_data.getChangeset()

      self._hostnames = []
      self._machine_datas = []
      for machine_id in self._machine_ids:
         machine_data = Testrun._getSubDataValue(Machine, machine_id)
         self._machine_datas.append(machine_data)
         self._hostnames.append(machine_data.getMachineName())

      self._wu_data = Testrun._getSubDataValue(Workunit, self._workunit_id)
      self._wl_name, self._area_name, \
      self._branch_name, self._bld_type = self.getWorkunitInfo()
      self.__initTriageInfo()

      if not parserLog:
         # Only parserLog if required,
         return
      else:
         self._parseTestrunLog()

   def _parseTestrunLog(self):
      if self.getWorkloadData().isTestesxWorkload():
         self._test_type = TESTESX
         # Parse and Handle testesx log
         try:
            self._test_result_log = TestesxLog(self._http_result_dir)
         except KeyboardInterrupt:
            raise
         except:
            # testesx.log is lost
            pass
         else:
            # If testesx log is available
            self._test_result_log.parseTestesxLog()
            testesx_hostnames = self._test_result_log.getHostNames()
            if testesx_hostnames:
               self._hostnames = testesx_hostnames

      else:
         # Parse and Handle testinfo.csv if contains
         try:
            self._test_result_log = TestInfo(self._http_result_dir)
         except KeyboardInterrupt:
            raise
         except:
            # no testinfo.csv exist
            pass
         else:
            self._test_result_log.parseTestInfoLog()

   def __initTriageInfo(self):
      if self._result == KW_STILL_RUNNING:
         self._triage_info = None
      elif self._ignored:
         self._triage_info = KW_IGNORED
      elif self._need_triage:
         self._triage_info = KW_TRIAGE_ALERT
      else:
         triage_list = []
         if self._bug_objs:
            for bug_obj in self._bug_objs:
               triage_list.append(Testrun._getSubDataValue('bug_obj',
                                                           bug_obj['id']))

         if self._ticket_objs:
            for ticket_obj in self._ticket_objs:
               triage_list.append(Testrun._getSubDataValue('ticket_obj',
                                                           ticket_obj['id']))

         if triage_list == []:
            self._triage_info = None
         else:
            self._triage_info = triage_list

   def getTestrunInfo(self):
      """(id, wlName, areaName, branchName, bldType, deliverable_id, cln,
          start_time, end_time, run_time, result, hostnames, triage_info).
      Treat it as a unique tuple
      """
      assert(self.isFullyInitialzied())
      return (self._id, self._area_name, self._branch_name, self._bld_type,
              self._deliverable_id, self._cln, self._start_time, self._end_time,
              self._run_time, self._result, self._hostnames, self._triage_info, self._bug_objs)

   def isValid(self):
      return self._is_valid

   def getBugDatas(self):
      assert(self.isFullyInitialzied())
      return self._bug_objs

   def getBugID(self):
      assert(self.isFullyInitialzied())
      bugid = []
      buglink = ''
      bugdata = self._bug_objs
      if bugdata:
          for bug in bugdata:
              if bug[u'number'] not in bugid:
                  bugid.append(bug[u'number'])
                  buglink += '<a href=https://bugzilla.eng.vmware.com/show_bug.cgi?id=' + str(bug[u'number']) + '>' + str(bug[u'number']) + '</a>' + '\n'
      return [bugid, buglink]

   def getDeliverableData(self):
      assert(self.isFullyInitialzied())
      return self._deliverable_data

   def getWorkunitData(self):
      assert(self.isFullyInitialzied())
      return self._wu_data

   def getWorkunitInfo(self):
      return self.getWorkunitData().getWorkunitInfo()

   def getWorkloadData(self):
      return self.getWorkunitData().getWorkloadData()

   def getWorkunitId(self):
      """Return workunit id, and don't need testrun fully initialized in ahead
      """
      return self._workunit_id

   def getHostNames(self):
      return ','.join(self._hostnames)

   def isTestesxLogAvailable(self):
      assert(self.isFullyInitialzied())
      if (self._test_type == TESTESX) and (self._test_result_log is not None):
         return True
      else:
         return False

   def isTestInfoLogAvailable(self):
      """True, if testrun contains testinfo.csv file
      """
      assert(self.isFullyInitialzied())
      if (self._test_type == GENERAL) and (self._test_result_log is not None):
         return True
      else:
         return False

   def getCLN(self):
      assert(self.isFullyInitialzied())
      return self._cln

   def getResult(self):
      return self._result

   def getStartTime(self):
      return self._start_time

   def getEndTime(self):
      return self._end_time

   def getRunTime(self):
      return self._run_time

   def getRunTimeInMinutes(self):
      return self._run_time_in_minutes

   def getResultDirUrl(self):
      return self._http_result_dir

   def isNeedTriage(self):
      assert(self.isFullyInitialzied())
      if self._triage_info == KW_TRIAGE_ALERT:
         return True
      else:
         return False

   def getTriageInfo(self):
      assert(self.isFullyInitialzied())
      return self._triage_info

   def getTotalTestNum(self):
      assert(self.isFullyInitialzied())
      try:
         return self._test_result_log.getTotalTestNum()
      except:
         return 0

   def getPassedTestNum(self):
      assert(self.isFullyInitialzied())
      try:
         return (self._test_result_log.getTotalTestNum() -
                 self._test_result_log.getFailedTestNum())
      except:
         return 0

   def getDetailedLogMessages(self):
      """Return a list of detailed script level result
      each item is in format (hostname, testresult, testname, execution time)
      """
      if self.isTestesxLogAvailable():
         return self._test_result_log.getScriptLevelDetailedInfo()

      elif self.isTestInfoLogAvailable():
         test_log_info = self._test_result_log.getDetailedTestResults()
         hostnames = ','.join(self._hostnames)
         for test_info in test_log_info:
            test_info.insert(0, hostnames)
         return test_log_info

      else:
         return None

   def getErrorLogReadableInfo(self):
      if self.isTestesxLogAvailable():
         return self._test_result_log.getErrorLogReadableInfo()
      elif self.isTestInfoLogAvailable():
         return self._test_result_log.getNonPassedTestInfo()
      else:
         return None

   def getUnifiedErrorMessages(self):
      """Return unified error message as a list

      Each element is in format (result, unified-error-message)
      """
      if self.isTestesxLogAvailable():
         return self._test_result_log.getUnifiedErrorMessages()
      else:
         # If testesx is unavailable, return workunit info
         wuData = self.getWorkunitData()
         wuInfo = "Workload %s - Build %s - Area %s" % (wuData.getWorkloadName(),
                                                        wuData.getBuildInfo(),
                                                        wuData.getAreaName())
         return [(self.getResult().lower(), wuInfo)]

   def getDetailedMachineMessages(self):
      if self.isTestesxLogAvailable():
         return self._test_result_log.getMachineLevelDetailedInfo()
      else:
         return None

   #============================================
   # Testrun Post / Patch related static methods
   #============================================
   @staticmethod
   def rerunTestrunByCln(cln, wuData=None, trData=None):
      """Rerun testrun with defined cln
      """
      if (not wuData) and (not trData):
         raise Exception("Please provide either wuData or trData")

      if not wuData:
         # If user provide wuData, use wuData directly
         # Or, use trData to retrieve wuData
         wuData = trData.getWorkunitData()

      # Get CAT deliverable datas whose changeset equals to @cln
      clnBuildDatas = Build.getBuildsByChangeset(cln)
      clnDeliverableDatas = []
      for clnBuildData in clnBuildDatas:
         clnDeliverableDatas += clnBuildData.getDeliverablesDatas()

      # Prepare rerun post object
      wuId = wuData.getId()

      '''One CAT build is associated with an unique CLN, and would generate
      M deliverables, each deliverable comes from one unique builder.
      Only care about the deliverable(s) whose builder id is
      in workunit's builder id list
      '''
      wuBuilderIds = wuData.getBuilderIds()
      deliverableIds = []

      for clnDeliverableData in clnDeliverableDatas:
         clnDeliverableBuilderId = clnDeliverableData.getBuilderId()
         if clnDeliverableBuilderId in wuBuilderIds:
            deliverableIds.append(clnDeliverableData.getId())

      if not deliverableIds:
         raise Exception("No CAT Deliverable with CLN %s from builder %s" % \
                         (cln, ', '.join(wuBuilderIds)))

      return Testrun.rerunTestrun(wuId, deliverableIds)

   @staticmethod
   def rerunTestrun(wuId, deliverableIds):
      jsonObj = {}
      addId(jsonObj, 'workunit', wuId)
      addIds(jsonObj, 'deliverables', 'deliverable', deliverableIds)
      logger.debug("Re-run testruns with workunit id: %s, delvierable: %s",
                   wuId, ', '.join(deliverableIds))
      return postResultToCat('testrun', jsonObj)

   @staticmethod
   def ignoreTestrun(testrunId, ignoredReason):
      jsonData = {}
      jsonData['ignoredby'] = SCRIPT_USER
      jsonData['ignored'] = True
      jsonData['ignore_reason'] = ignoredReason
      (ret, _) = patchResultToCat('testrun', testrunId,
                                  jsonData, apiVersion='v3.0')
      if ret:
         logger.info("Succeed to ignore testrun: %s with reason %s",
                      testrunId, ignoredReason)
      else:
         logger.info("Failed to ignore testrun: %s, please triage it manually",
                     testrunId)

   #====================================
   # Testrun PUT related static methods
   #====================================
   @staticmethod
   def getTestrunsTriageInfo(testrunIds, isPlain=True):
      """Return a dict to record testrun triage info in format:
         {testrunId: [triageInfo]}
      """
      triageInfoDict = {}

      logger.info("Query real time %d testruns' triage info from CAT...",
                  len(testrunIds))
      testrunDatas = Testrun.getFullyInitializedCatObjectList(testrunIds,
                                                              parserLog=False)
      for trData in testrunDatas:
         triageInfo = []
         triageData = trData.getTriageInfo()

         if isinstance(triageData, str):
            triageInfo.append(triageData)
         elif isinstance(triageData, list):
            for triageSubData in triageData:
               if isPlain:
                  triageInfo.append(triageSubData.getName())
               else:
                  triageInfo.append(triageSubData.getHtmlId())

         triageInfoDict[trData.getId()] = triageInfo

      return triageInfoDict

   @staticmethod
   def filterTestrunsByResults(trDatas, results):
      """Return testrun data list, each testrun's result should in results list

      @rtype: a list of Testrun instances
      """
      validTrDatas = []

      for trData in trDatas:
         if trData.getResult() in results:
            validTrDatas.append(trData)
         else:
            logger.info("Ignore testrun %s whose result is %s",
                        trData.getId(), trData.getResult())

      return validTrDatas

   @staticmethod
   def queryTestrunsByObjs(testrunObjs, skipRunning=True, skipPass=False,
                           parserLog=True):
      """Return a list of testrun instances by testrun obj
      """
      trDatas = []

      for testrunObj in testrunObjs:
         trId = getId(testrunObj, 'id')
         trData = Testrun(trId, testrunObj)
         trData.initCatRawInfo()
         if skipRunning and trData.getResult() == KW_STILL_RUNNING:
            logger.warn("Skip query testrun %s info since it still running",
                        trId)
            continue
         elif skipPass and trData.getResult() == RESULT_PASS:
            logger.warn("Skip query testrun %s info since its result is PASS",
                        trId)
            continue
         elif trData.isValid():
            trDatas.append(trData)
         else:
            logger.warn('Skip %s because its RestAPI information is not entire',
                        str(trData))

      logger.info("Initializing %d testruns shared information...",
                  len(trDatas))
      Testrun.initSubDataMap()

      logger.info("Initializing %d testruns detailed information, "
                  "this operation could take some time...", len(trDatas))
      for trData in trDatas:
         trData.initReadableInfo(parserLog)

      logger.debug("Total found %d testruns" % len(trDatas))
      return trDatas

   @staticmethod
   def queryTestrunsByIds(testrunIds, skipRunning=True, skipPass=False,
                          parserLog=True):
      """Return a list of Testrun instances by testrun ids
      """
      trObjs = []
      for trId in testrunIds:
         trData = Testrun(trId)
         trObjs.append(trData.getCatObj())

      return Testrun.queryTestrunsByObjs(trObjs, skipRunning=False, skipPass=False, parserLog=True)

   @staticmethod
   def queryTestrunDatas(limitDay, limitNumber, wuIds=None, wlNames=None,
                         areaIds=None, areaNames=None, branchNames=None,
                         testerIds=None, bldTypes=None, skipRunning=True,
                         skipPass=False, parserLog=True):
      """Get testruns RestAPI raw data
      @limitDay: define how many days data you want to get back from current time
      @limitNubmer: limit the testruns number from CAT

      @return: [testrunDatas]
      @rtype: a list of Testrun instances
      """

      def _queryTrObjsByWuIds(wuIds):
         trObjs = []
         for wuId in wuIds:
            logger.info("Retrieving testrun data with workunit id %s", wuId)
            wuTrObjs = queryCatInfo('testrun', {'workunit': wuId},
                                    limitDay=limitDay, limit=limitNumber,
                                    orderBy="-endtime")
            if wuTrObjs:
               logger.info("Totally get %d testruns" % len(wuTrObjs))
               trObjs.extend(wuTrObjs)

         return trObjs

      def _queryTrObjsByCatView(wlNames=None, areaIds=None, areaNames=None,
                                branchNames=None, testerIds=None, bldTypes=None):
         def _argsWrapper(args):
            if not args:
               return [None]
            else:
               return args

         if not wlNames:
            wlIds = [None]
         else:
            from workload import Workload
            wlIds = Workload.getWorkloadIds(wlNames)

         if areaNames:
            areaIds = Area.getAreaIds(areaNames)
         elif areaIds:
            childrenIds = Area.getChildrenAreaIds(areaIds)
            if childrenIds:
               areaIds.extend(childrenIds)
         else:
            areaIds = [None]

         # The order for filterKey and filterLoop should be matched
         filterKey = ['workload', 'area__id__in', 'deliverables__build__branch__in',
                      'tester__id__in', 'deliverables__build__bldtype__in']
         filterLoop = itertools.product(wlIds, areaIds, _argsWrapper(branchNames),
                                        _argsWrapper(testerIds),
                                        _argsWrapper(bldTypes))
         filterLoop = list(filterLoop)

         trObjs = []
         for item in filterLoop:
            filterMap = {}
            for i in range(len(item)):
               if item[i] is None:
                  continue
   
               filterMap[filterKey[i]] = item[i]
   
            logger.info("Retrieving testrun data via RestAPI with filterInfo: %s",
                        filterMap)
            tmpTrObjs = queryCatInfo('testrun', filterMap, limitDay=limitDay,
                                     limit=limitNumber, orderBy="-endtime")
            if tmpTrObjs:
               logger.info("Totally get %d testruns" % len(tmpTrObjs))
               trObjs.extend(tmpTrObjs)

         return trObjs

      logger.debug("args for queryTestrunDatas: %s" % vars())

      # 1. Retrieve all testruns info from CAT based on input
      if wuIds:
         allTrObjs = _queryTrObjsByWuIds(wuIds)
      else:
         allTrObjs = _queryTrObjsByCatView(wlNames, areaIds, areaNames,
                                           branchNames, testerIds, bldTypes)

      # 2. Init valid testrun datas using testrun objs
      return Testrun.queryTestrunsByObjs(allTrObjs,skipRunning=False, skipPass=False, parserLog=True)

   @staticmethod
   def queryWorkunitIds(limitDay, limitNumber, wlNames=None,
                        areaIds=None, areaNames=None, branchNames=None,
                        testerIds=None, bldTypes=None):
      """Return workunit id list by query testruns

      @rtype: a list of Workunit instances
      """
      trDatas = Testrun.queryTestrunDatas(limitDay, limitNumber, None,
                                          wlNames, areaIds, areaNames,
                                          branchNames, testerIds, bldTypes,
                                          skipRunning=False, skipPass=False,
                                          parserLog=False)

      wuIds = set()
      for testrun in trDatas:
         wuIds.add(testrun.getWorkunitId())
      logger.info("Totally found %d workunit(s)" % len(wuIds))
      return wuIds

   @staticmethod
   def queryTestrunsByDeliverableObjects(deliverableObjects, areaId, skipRunning=True):
      testrunObjs = []
      for deliverable_obj in deliverableObjects:
          deliverableId= deliverable_obj.getId()
          testrunObjs.extend(queryCatInfo('testrun', {'deliverables':deliverableId, 'area':areaId}))
      if not testrunObjs:
         raise Exception("No testrun run against with deliverables %s in area %s"\
                          % (deliverableId, areaId))

      return Testrun.queryTestrunsByObjs(testrunObjs, skipRunning,
                                         skipPass=False, parserLog=False)

   @staticmethod
   def queryTestrunsByDeliverableId(deliverableId, areaId, skipRunning=True):
      """
      Quary all testruns by deliverable id
      """
      testrunObjs = queryCatInfo('testrun', {'deliverables':deliverableId, 'area':areaId})
      if not testrunObjs:
         raise Exception("No testrun run against with deliverables %s in area %s"\
                          % (deliverableId, areaId))

      return Testrun.queryTestrunsByObjs(testrunObjs, skipRunning,
                                         skipPass=False, parserLog=False)

   @staticmethod
   def queryTestrunsByCLN(cln, skipRunning=True):
      """Query testruns by CLN

      @rtype: a list of Testrun instances
      """
      build_datas = Build.getBuildsByChangeset(cln)
      deliverable_ids = []

      for build_data in build_datas:
         sub_deliverable_ids = build_data.getDeliverableIds()
         if sub_deliverable_ids:
            deliverable_ids.extend(sub_deliverable_ids)

      logger.info("Retrieving testrun data which deliverable id is in %s",
                   deliverable_ids)
      testrunObjs = queryCatInfo('testrun', {'deliverables__id__in':
                                             ','.join(deliverable_ids)})
      if not testrunObjs:
         raise Exception("No testrun run against with deliverables %s"\
                          % deliverable_ids)

      return Testrun.queryTestrunsByObjs(testrunObjs, skipRunning,
                                         skipPass=False, parserLog=False)


"""Below code is for testing purpose
"""
if __name__ == '__main__':

   def printTrData(trData):
      print("Testrun: %s" % trData)
      print(" Testrun Info: %s" % (trData.getTestrunInfo(), ))
      print(" Workunit Info: %s" % (trData.getWorkunitInfo(), ))
      print(" Readable Error Info:\n%s" % (trData.getErrorLogReadableInfo(), ))
      print(" Is testesx available: %s" % trData.isTestesxLogAvailable())
      print("------------------------\n")

   def printTrDatas(trDatas):
      for trData in trDatas:
         printTrData(trData)

   trIds = """
54901685
54766537
"""
   trIds = trIds.strip().split('\n')

   print("\nTesting initialize testrun datas")
   trDatas = Testrun.getFullyInitializedCatObjectList(trIds)
   printTrDatas(trDatas)

   trDatas = Testrun.getFullyInitializedCatObjectList(trIds, parserLog=False)
   for trId in trIds:
      trData = Testrun(trId)
      trData.initCatRawInfo()
      trDatas.append(trData)

   Testrun.initSubDataMap()

   for trData in trDatas:
      trData.initReadableInfo()
      printTrData(trData)

   print("\nTesting queryTestrunDatas function")
   trDatas = Testrun.queryTestrunDatas(1, 10, areaIds=[2],
                                       branchNames=['vmcore-main'])
   printTrDatas(trDatas)

   print("\nTesting queryTestrunDatas function with skipPass=True")
   trDatas = Testrun.queryTestrunDatas(1, 10, areaIds=[2],
                                       branchNames=['vmcore-main'],
                                       skipPass=True)
   printTrDatas(trDatas)

   print("\nTesting queryTestrunByCLN...")
   trDatas = Testrun.queryTestrunsByCLN(cln=5591458)
   printTrDatas(trDatas)

   print("\nTesting queryTestrunsByIds...")
   trDatas = Testrun.queryTestrunsByIds(testrunIds=[56073512, 56073518])
   printTrDatas(trDatas)

   print("\nTesting queryWorkunitIds function")
   Testrun.queryWorkunitIds(1, None, areaIds=[2], branchNames=['vmcore-main'])
