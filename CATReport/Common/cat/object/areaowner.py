''' CAT 'areaowner' library
Created on Aug 28, 2016

@author: kaiyuanli
'''
from area import Area
from branch import Branch
from catdata import CatData
from Common.cat.lib.catApi import patchResultToCat, postResultToCat, queryCatInfo
from Common.cat.lib.jsonHandler import addId, addValue, getId
from Common.utils.logger import getLogger

logger = getLogger()


class AreaOwner(CatData):
   """Single AreaOwner data
   """
   _objType = 'areaowner'
   _leafNode = False
   _subDataMap = {}

   def initCatRawInfo(self):
      super(AreaOwner, self).initCatRawInfo()

      self._area_id = self.getIdFromCatObj('area')
      self._branch_id = self.getIdFromCatObj('branch')
      self._owners = self.getValueFromCatObj('owners')
      self._triage_owners = self.getValueFromCatObj('triage_owners')
      self._cost_center_manager = self.getValueFromCatObj('cost_center_manager')

      AreaOwner._addSubData(Area, self._area_id)
      AreaOwner._addSubData(Branch, self._branch_id)

   def initReadableInfo(self):
      super(AreaOwner, self).initReadableInfo()
      self._area_name = AreaOwner._getSubDataValue(Area, self._area_id).getAreaName()
      self._branch_name = AreaOwner._getSubDataValue(Branch, self._branch_id).getBranchName()

   def getAreaOwnerInfo(self):
      """Return info (areaName, branchName, owner, triage_owner, manager)
      """
      assert(self._full_initialized)
      return (self._area_name, self._branch_name, self._owners,
              self._triage_owners, self._cost_center_manager)

   @staticmethod
   def getAreaownerIds(areaIds, branchIds):
      """Get areaowner ids via area ids and branch ids
      """
      areaowners = []
      for areaId in areaIds:
         for branchId in branchIds:
            tmpObjs = queryCatInfo('areaowner',
                                   {'area': areaId, 'branch': branchId},
                                   apiVersion='v3.0')
            for tmpObj in tmpObjs:
               areaowners.append(getId(tmpObj))
      return areaowners

   @staticmethod
   def addAreaowner(areaId, branchId, owners, manager):
      logger.info("Add areaowner with info: %s" % vars())
      owners = '%s' % ','.join(owners)
      areaOwnerObj = {}
      addId(areaOwnerObj, 'area', areaId)
      addId(areaOwnerObj, 'branch', branchId)
      addValue(areaOwnerObj, 'owners', owners)
      addValue(areaOwnerObj, 'bug_shepherds', owners)
      addValue(areaOwnerObj, 'triage_owners', owners)
      addValue(areaOwnerObj, 'cost_center_manager', manager)
      return postResultToCat('areaowner', areaOwnerObj, 'v3.0')

   @staticmethod
   def modifyAreaowner(areaownerId, owners=None, manager=None):
      logger.info("Modify areaowner with info: %s" % vars())
      areaOwnerObj = {}
      if owners is not None:
         owners = '%s' % ','.join(owners)
         addValue(areaOwnerObj, 'owners', owners)
         addValue(areaOwnerObj, 'bug_shepherds', owners)
         addValue(areaOwnerObj, 'triage_owners', owners)
   
      if manager is not None:
         addValue(areaOwnerObj, 'cost_center_manager', manager)
   
      return patchResultToCat('areaowner', areaownerId, areaOwnerObj, 'v3.0')


"""Below code is for test purpose
"""
if __name__ == '__main__':
   from Common.cat.lib.catApi import getTotalQueryRequestTimes
   from Common.utils.commonUtil import getCurrentDate, getExecutionTime
   start = getCurrentDate()

   areaOwnerDatas = []

   for i in range(1, 10):
      try:
         areaowner = AreaOwner(i)
      except Exception as e:
         print(e)
         continue
      areaOwnerDatas.append(areaowner)
      areaowner.initCatRawInfo()

   AreaOwner.initSubDataMap()

   for areaowner in areaOwnerDatas:
      areaowner.initReadableInfo()
      print(areaowner.getAreaOwnerInfo())

   end = getCurrentDate()
   print('Cost Time: %s' % getExecutionTime(start, end))
   print("Total CAT request: %s" % getTotalQueryRequestTimes())
