''' CAT 'builder' library
Created on Aug 28, 2016

@author: kaiyuanli
'''
from catdata import CatData
from Common.utils.logger import getLogger
from Common.cat.lib.catApi import queryCatInfo
from Common.cat.lib.jsonHandler import getId

logger = getLogger()

class Branch(CatData):
   """Single Branch data
   """
   _objType = 'branch'
   _leafNode = True
   _subDataMap = {}

   def initCatRawInfo(self):
      super(Branch, self).initCatRawInfo()
      self._name = self.getValueFromCatObj('name')

   def getBranchName(self):
      return self._name

   @staticmethod
   def getBranchIds(branchNames):
      """Get branch Ids via branch name @branchName
      """
      branchIds = []
      for branchName in branchNames:
         retObjs  = queryCatInfo('branch', {'name': branchName})
         if not retObjs:
            raise Exception("No branch named as %s" % branchName)
         else:
            for retObj in retObjs:
               branchIds.append(getId(retObj))
      return branchIds

"""Below code is for test purpose
"""
if __name__ == '__main__':
   from Common.cat.lib.catApi import getTotalQueryRequestTimes
   from Common.utils.commonUtil import getCurrentDate, getExecutionTime
   start = getCurrentDate()

   branchDatas = []
   for branchId in range(1, 10):
      print('Working for branch %s' % branchId)
      branchData = Branch(branchId)
      branchData.initCatRawInfo()
      branchDatas.append(branchData)

   for branchData in branchDatas:
      branchData.initReadableInfo()
      print(branchData.getBranchName())

   print Branch.getBranchIds(['vmcore-main', 'layer1-stage', 'super-main'])
   end = getCurrentDate()
   print('Cost Time: %s' % getExecutionTime(start, end))
   print("Total CAT request: %s" % getTotalQueryRequestTimes())