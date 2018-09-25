''' CAT 'builder' library
Created on Aug 28, 2016

@author: kaiyuanli
'''
from branch import Branch
from catdata import CatData
from Common.utils.logger import getLogger

logger = getLogger()

class Builder(CatData):
   """Single Builder data
   """
   _objType = 'builder'
   _leafNode = False
   _subDataMap = {}

   def initCatRawInfo(self):
      super(Builder, self).initCatRawInfo()
      self._bldType = self.getValueFromCatObj('bldtype')

      if self._catObj['sbtargets']:
         self._target = self.getValueFromCatObj('sbtargets')
      else:
         self._target = self.getValueFromCatObj('buildtargets')

      self._branch_id = self.getIdFromCatObj('branch')
      Builder._addSubData(Branch, self._branch_id)

   def initReadableInfo(self):
      super(Builder, self).initReadableInfo()
      self._branch_name = Builder._getSubDataValue(Branch, self._branch_id).getBranchName()

   def getBranchName(self):
      assert(self.isFullyInitialzied())
      return self._branch_name

   def getBuildType(self):
      assert(self.isFullyInitialzied())
      return self._bldType


"""Below code is for test purpose
"""
if __name__ == '__main__':
   from Common.cat.lib.catApi import getTotalQueryRequestTimes
   from Common.utils.commonUtil import getCurrentDate, getExecutionTime
   start = getCurrentDate()

   builderIds = [105, 107, 3107, 2216]
   builderDatas = []
   for builderId in builderIds:
      print('Working for builder %s' % builderId)
      builderData = Builder(builderId)
      builderDatas.append(builderData)
      builderData.initCatRawInfo()

   Builder.initSubDataMap()

   for builder in builderDatas:
      builder.initReadableInfo()
      #print(builder.getDetailedData())
      print(builder.getBranchName())

   end = getCurrentDate()
   print('Cost Time: %s' % getExecutionTime(start, end))
   print("Total CAT request: %s" % getTotalQueryRequestTimes())