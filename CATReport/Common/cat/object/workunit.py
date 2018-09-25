'''CAT 'workunit' library

@author: kaiyuanli
'''

from catdata import CatData
from Common.cat.lib.catApi import postResultToCat, patchResultToCat, queryCatInfo
from Common.cat.lib.jsonHandler  import addId, addValue, getId
from Common.utils.constants import NOT_AVALIABLE
from Common.utils.logger import getLogger

from area import Area
from builder import Builder
from workload import Workload

logger = getLogger()


class Workunit(CatData):
   """Single Workunit data
   """
   _objType = 'workunit'
   _leafNode = False
   _subDataMap = {}

   def __init__(self, wuId):
      super(Workunit, self).__init__(wuId)
      self._deleted = False
      self._enabled = True

   def initCatRawInfo(self):
      super(Workunit, self).initCatRawInfo()
      tester_id = self.getIdFromCatObj('tester')
      if not tester_id:
         self._tester_id = NOT_AVALIABLE
         logger.warn("Workunit %s has already been deleted" % self._id)
         self._deleted = True
      else:
         self._tester_id = tester_id

      self._workload_id = self.getIdFromCatObj('workload')
      self._area_id = self.getIdFromCatObj('area')
      self._builder_ids = self.getIdsFromCatObj('builddefs', 'builder')
      self._builder_id = self._builder_ids[0]

      if self._deleted:
         self._enabled = False
      else:
         self._enabled = self.getValueFromCatObj('enabled')

      Workunit._addSubData(Workload, self._workload_id)
      Workunit._addSubData(Area, self._area_id)

      for builder_id in self._builder_ids:
         Workunit._addSubData(Builder, builder_id)

   def initReadableInfo(self):
      super(Workunit, self).initSubDataMap()
      self._raw_initialized = True
      super(Workunit, self).initReadableInfo()
      self._wl_data = Workunit._getSubDataValue(Workload, self._workload_id)
      self._wl_name = self._wl_data.getWorkloadName()

      self._area_data = Workunit._getSubDataValue(Area, self._area_id)
      self._area_name = self._area_data.getAreaName()

      self._builder_datas = []
      for builder_id in self._builder_ids:
         builder_data = Workunit._getSubDataValue(Builder, builder_id)
         self._builder_datas.append(builder_data)

      self._builder_data = self._builder_datas[0]
      self._branch_name = self._builder_data.getBranchName()
      self._bld_type = self._builder_data.getBuildType()

   def getWorkunitInfo(self):
      """(wlName, areaName, branchName, bldType). Treat it as a unique tuple
      """
      assert(self.isFullyInitialzied())
      return (self._wl_name, self._area_name, self._branch_name, self._bld_type)

   def getWorkloadData(self):
      assert(self.isFullyInitialzied())
      return self._wl_data

   def getWorkloadName(self):
      assert(self.isFullyInitialzied())
      return self._wl_name

   def getWorkloadId(self):
      return self._workload_id

   def getAreaData(self):
      assert(self.isFullyInitialzied())
      return self._area_data

   def getAreaName(self):
      assert(self.isFullyInitialzied())
      return self._area_name

   def getAreaId(self):
      return self._area_id

   def getBuilderData(self):
      """Return the first builder's data
      """
      assert(self.isFullyInitialzied())
      return self._builder_data

   def getBuilderDatas(self):
      """Return all builders' data
      """
      assert(self.isFullyInitialzied())
      return self._builder_datas

   def getBuildInfo(self):
      """Return the first builder's build info
      """
      assert(self.isFullyInitialzied())
      return '%s:%s' % (self._branch_name, self._bld_type)

   def getBuilderId(self):
      """Return the first builder's id
      """
      return self._builder_id

   def getBuilderIds(self):
      """Return all builders' id
      """
      return self._builder_ids

   def getTesterId(self):
      return self._tester_id

   def isDeleted(self):
      # If workunit's tester id is empty, the workunit is deleted
      return self._deleted

   @staticmethod
   def addWorkunit(testerId, builderId, areaId, wlId):
      """Add workunit into tester operation
      """
      logger.debug("Add workunit with info: %s" % vars())
      wuObj = {}
      addId(wuObj, 'tester', testerId)
      addId(wuObj, 'workload', wlId)
      addId(wuObj, 'area', areaId)
      addValue(wuObj, 'host_platform', 'visor')

      wuObj['builddefs'] = []

      # Workunits can be associated with multiple builders
      if not isinstance(builderId, list):
         builderIds = [builderId]
      else:
         builderIds = builderId

      for builderId in builderIds:
         buildObj = {}

         addId(buildObj, 'builder', builderId)
         addValue(buildObj, 'deployment', '-')
         addValue(buildObj, 'recommended', None, convertToStr=False,
                  ignoreEmpty=False)

         wuObj['builddefs'].append(buildObj)

      return postResultToCat('workunit', wuObj)

   @staticmethod
   def modifyWorkunit(wuId, wlId=None, builderId=None, areaId=None):
      """Modify workunit (workunit id = @wuId) info
      """
      logger.info("Modify workunit with info: %s" % vars())
      wuObj = {}
      addId(wuObj, 'workload', wlId)
      addId(wuObj, 'area', areaId)

      if builderId:
         #If modify builder id, need to update builddef info
         wuData = Workunit(wuId)
         wuData.initCatRawInfo()
         builddefObj = wuData.getCatObj()['builddefs'][0]
         build_def_id = builddefObj['id']
         build_obj = {}
         addId(build_obj, 'builder', builderId)
         rc, result = patchResultToCat('builddef', build_def_id,
                                       build_obj, apiVersion='v3.0')

      if wlId is None and areaId is None:
         return (rc, result)
      else:
         wuObj = {}
         addId(wuObj, 'workload', wlId)
         addId(wuObj, 'area', areaId)
         return patchResultToCat('workunit', wuId, wuObj, apiVersion='v3.0')

   @staticmethod
   def modifyWorkunitEnableStatus(wuId, enable):
      """@enable: True, enable workunit. False, disable it
      """
      logger.info("Modify workunit %s enable status as %s", wuId, enable)
      wuObj = {}
      addValue(wuObj, 'enabled', enable, convertToStr=False)
      return patchResultToCat('workunit', wuId, wuObj, apiVersion='v3.0')

   @staticmethod
   def modifyWorkunitParallelStatus(wuId, parallel):
      """@enable: True, parallel workunit. False, sequence it
      """
      logger.info("Modify workunit %s parallel status as %s", wuId, parallel)
      wuObj = {}
      addValue(wuObj, 'parallel', parallel, convertToStr=False)
      return patchResultToCat('workunit', wuId, wuObj, apiVersion='v3.0')

   @staticmethod
   def modifyWorkunitIteration(wuId, iteration):
      """Set workunit iteration as @iteration
      """
      logger.info("Modify workunit %s iteration as %s" % (wuId, iteration))
      wuObj = {}
      addValue(wuObj, 'run_every_nth_iteration', iteration, convertToStr=False)
      return patchResultToCat('workunit', wuId, wuObj, apiVersion='v3.0')

   @staticmethod
   def QueryEnabledWorkunitInArea(areaId):
      workunitObjs = []
      search_obj = {'enabled':'true', 'area':areaId}
      workunitDatas = queryCatInfo('workunit', search_obj, apiVersion='v3.0')
      if not workunitDatas:
         raise Exception("Cannot find any workunit in area %s" % areaId)
      for workunitData in workunitDatas:
         wuId = getId(workunitData, "id")
         workunit = Workunit(wuId)
         workunit.initCatRawInfo()
         workunitObjs.append(workunit)
      return workunitObjs

   @staticmethod
   def getWorkunitCommonInfo(wuDatas):
      wuData_info_dict = {'workunit_id': set(), 'tester_id': set(),
                          'workload_name': set(), 'area_name': set(),
                          'build_info': set()}
      for wuData in wuDatas:
         wuData_info_dict['workunit_id'].add(wuData.getId())
         wuData_info_dict['tester_id'].add(wuData.getTesterId())
         wuData_info_dict['workload_name'].add(wuData.getWorkloadName())
         wuData_info_dict['build_info'].add(wuData.getBuildInfo())
         wuData_info_dict['area_name'].add(wuData.getAreaName())

      def genInfo(info, trunctList, commonlimit=10):
         # Treat as a common info only when contain <= different kinds of info
         if not trunctList:
            return
         elif len(trunctList) > commonlimit:
            return
         else:
            msg = '%s%s' % (trunctList[0], '...' if len(trunctList) > 1 else '')
            info.append(msg)

      info = []
      genInfo(info, list(wuData_info_dict['build_info']))
      genInfo(info, list(wuData_info_dict['area_name']))
      genInfo(info, list(wuData_info_dict['workload_name']), 2)
      genInfo(info, list(wuData_info_dict['tester_id']), 1)
      genInfo(info, list(wuData_info_dict['workunit_id']), 1)

      return ' - '.join(info)


"""Below code is for test purpose
"""
if __name__ == '__main__':

   wuIds = """
160897
160894
156535
166117
160891
160170
162799
160945
160143
162796
160155
"""
   wuIds = wuIds.strip().split('\n')
   wuDatas = []

   for wuId in wuIds:
      wuData = Workunit(wuId)
      wuDatas.append(wuData)
      wuData.initCatRawInfo()

   Workunit.initSubDataMap()

   for wuData in wuDatas:
      wuData.initReadableInfo()
      wlData = wuData.getWorkloadData()
      print('wu: %s, tester: %s, area: %s, branch info: %s, wl name: %s, '
            'group %s, boot option: %s, feature switch: %s'
            % (wuData.getId(), wuData.getTesterId(), wuData.getAreaName(),
               wuData.getBuildInfo(), wlData.getWorkloadName(),
               wlData.getGroups(), wlData.getBootOptions(),
               wlData.getFeatureSwitches()))
      print("show all builder ids: %s" % ', '.join(wuData.getBuilderIds()))

   print Workunit.getWorkunitCommonInfo(wuDatas)

   '''
   for wuId in wuIds:
      Workunit.modifyWorkunit(wuId, areaId=13)

   #Modify workunits per tester
   from Common.cat.lib.catApi import queryCatInfo
   tester = queryCatInfo('tester', {'id': 27327})[0]
   wu_ids = getIds(tester, 'workunits', 'workunit')

   testerId = 27327
   builderId = 105

   for wu_id in wu_ids:
      Workunit.modifyWorkunit(wu_id, builderId=builderId)
   '''

