''' CAT 'build' library
Created on Oct 20, 2016

@author: kaiyuanli
'''
from Common.cat.lib.catApi import queryCatInfo
from Common.utils.logger import getLogger

from catdata import CatData
from deliverable import Deliverable

logger = getLogger()


class Build(CatData):
   """Single Build data
   """
   _objType = 'build'
   _leafNode = False
   _subDataMap = {}

   def initCatRawInfo(self):
      super(Build, self).initCatRawInfo()
      self._bldType = self.getValueFromCatObj('bldtype')
      self._branch = self.getValueFromCatObj('branch')
      self._changeset = self.getValueFromCatObj('changeset')
      self._deliverable_ids = self.getIdsFromCatObj('deliverables', 'deliverable')
      self._submit_time = self.getValueFromCatObj('submit_time')
      self._submit_user = self.getValueFromCatObj('submit_user')

      for deliverable in self._deliverable_ids:
         Build._addSubData(Deliverable, deliverable)

   def initReadableInfo(self):
      super(Build, self).initReadableInfo()
      self._deliverable_datas = []
      for deliverable_id in self._deliverable_ids:
         deliverable_data = Build._getSubDataValue(Deliverable, deliverable_id)
         self._deliverable_datas.append(deliverable_data)

   def getBuildType(self):
      return self._bldType

   def getBranchName(self):
      return self._branch

   def getChangeset(self):
      return self._changeset

   def getDeliverableIds(self):
      return self._deliverable_ids

   def getDeliverablesDatas(self):
      assert(self._full_initialized)
      return self._deliverable_datas

   @staticmethod
   def getBuildsByChangeset(changeset):
      """Return a list of Build instances whose CLN equals to changeset
      """
      retObjs = queryCatInfo('build', {'changeset': changeset})
      if not retObjs:
         raise Exception("No CAT build generated against CLN %s" % changeset)
      else:
         buildIds = [retObj['id'] for retObj in retObjs]
         return Build.getFullyInitializedCatObjectList(buildIds)

   @staticmethod
   def getBuildsByProductionInfo(product, branch, bldtype, limitDay=1):
      """
      Get build info by product.
      """
      retObjs = queryCatInfo('build', {'site_name':product, 'branch':branch,
                                       'bldtype':bldtype}, limitDay=limitDay)
      if not retObjs:
         raise Exception("No CAT build generated against CLN %s" % changeset)
      else:
         buildIds = [retObj['id'] for retObj in retObjs]
         return Build.getFullyInitializedCatObjectList(buildIds)


"""Below code is for test purpose
"""
if __name__ == '__main__':

   print '-------------------------------'
   print 'Test get Build info by CLN     '
   print '-------------------------------'

   changeset_list = [4559527, 4560357, 4560338, 4560244, 5591458]
   changeset_build_ids = []
   for cln in changeset_list:
      print('CLN: %s' % cln)
      buildDatas =  Build.getBuildsByChangeset(cln)
      for buildData in buildDatas:
         print("  CAT Build: %s" % (buildData.getId()))

