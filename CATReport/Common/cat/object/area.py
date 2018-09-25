''' CAT 'area' object library
Created on Aug 28, 2016

@author: kaiyuanli
'''
from catdata import CatData
from Common.cat.lib.catApi import queryCatInfo
from Common.cat.lib.jsonHandler import getId, getValue
from Common.utils.logger import getLogger

logger = getLogger()

class Area(CatData):
   """Single Area data
   """
   _objType = 'area'
   _leafNode = False
   _subDataMap = {}

   def initCatRawInfo(self):
      super(Area, self).initCatRawInfo()
      self._name = self.getValueFromCatObj('name')
      self._sla_id = self.getIdFromCatObj('slatype', 'sla')
      self._viewtype_id = self.getIdFromCatObj('viewtype')

      Area._addSubData('slatype', self._sla_id)
      Area._addSubData('viewtype', self._viewtype_id)

   @classmethod
   def initSubDataMap(cls):
      slatypeData = cls._getSubDataValue('slatype')
      for sla_id in slatypeData.keys():
         if slatypeData[sla_id]:
            continue
         slaObj = queryCatInfo('sla', {'id': sla_id})[0]
         slatypeData[sla_id] = getValue(slaObj, 'name')

      viewtypeData = cls._getSubDataValue('viewtype')
      for view_id in viewtypeData.keys():
         if viewtypeData[view_id]:
            continue
         viewObj = queryCatInfo('viewtype', {'id': view_id})[0]
         viewtypeData[view_id] = getValue(viewObj, 'name')

      cls._raw_initialized = True

   def initReadableInfo(self):
      super(Area, self).initReadableInfo()
      self._sla_name = Area._getSubDataValue('slatype', self._sla_id)
      self._view_name = Area._getSubDataValue('viewtype', self._viewtype_id)

   def getAreaName(self):
      assert(self.isFullyInitialzied())
      return '%s:%s:%s' % (self._name, self._sla_name, self._view_name)

   @staticmethod
   def getAreaIds(areaNames):
      """Get area Ids via area name @areaName
      """
      areaIds = []
      for areaName in areaNames:
         retObjs = queryCatInfo('area', {'name': areaName})
         if not retObjs:
            raise Exception("No area named as %s " % areaName)
         else:
            for retObj in retObjs:
               areaIds.append(getId(retObj))
   
      return areaIds

   @staticmethod
   def getChildrenAreaIds(parentAreaIds):
      """Get children area Ids via parent area Ids
      """
      childAreaIds = []
      logger.debug("Get child area ids from parent area %s" % parentAreaIds)
      for parentAreaId in parentAreaIds:
         retObjs = queryCatInfo('area', {'parent': parentAreaId})
         for retObj in retObjs:
            if not getValue(retObj, 'visible'):
               logger.debug("Child area %s is not visable ,skip" % getId(retObj))
               continue
            childAreaIds.append(getId(retObj))

      return childAreaIds

"""Below code is for test purpose
"""
if __name__ == '__main__':
   from Common.cat.lib.catApi import getTotalQueryRequestTimes
   from Common.utils.commonUtil import getCurrentDate, getExecutionTime
   start = getCurrentDate()
   areaIds = [2, 13, 61]
   areaDatas = []

   for areaId in areaIds:
      area = Area(areaId)
      areaDatas.append(area)
      area.initCatRawInfo()

   Area.initSubDataMap()

   for area in areaDatas:
      area.initReadableInfo()
      #print (area.getDetailedData())
      print (area.getAreaName())

   print(Area.getAreaIds(['p:VMKernel-Core']))
   print(Area.getChildrenAreaIds([2, 13, 61]))

   end = getCurrentDate()
   print('Cost Time: %s' % getExecutionTime(start, end))
   print("Total CAT request: %s" % getTotalQueryRequestTimes())