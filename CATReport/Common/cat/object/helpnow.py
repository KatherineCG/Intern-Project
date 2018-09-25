''' CAT 'bug' library

Created on Aug 31, 2016

@author: kaiyuanli
'''
from catdata import CatData
from Common.cat.lib.catApi import patchResultToCat
from Common.cat.lib.jsonHandler import addValue
from Common.utils.htmlUtil import genHyperLink
from Common.utils.logger import getLogger

logger = getLogger()

class Helpnow(CatData):
   """Single Helpnow data
   """
   _objType = 'helpnow'
   _leafNode = True
   _subDataMap = {}

   def __str__(self):
      try:
         return self._ticket
      except:
         return self._id

   def initCatRawInfo(self):
      super(Helpnow, self).initCatRawInfo()
      self._ticket = self.getValueFromCatObj('ticket')
      self._hyperlink = self.getValueFromCatObj('url')
      self._triaged_testruns = self.getIdsFromCatObj('testruns', 'testrun')
      self._htmlId = genHyperLink(self._ticket, self._hyperlink)

   def getName(self):
      """Return Ticket Name
      """
      return self._ticket

   @staticmethod
   def patchHelpTicketInCAT(ticketIdInCat, testrunID):
      helpnows = {}
      addValue(helpnows, 'testrun_ids', [str(testrunID)], convertToStr=False)
      return patchResultToCat('helpnow', ticketIdInCat, helpnows, apiVersion='v3.0')

"""Below code is for test purpose
"""
if __name__ == '__main__':
   from Common.cat.lib.catApi import getTotalQueryRequestTimes
   from Common.utils.commonUtil import getCurrentDate, getExecutionTime
   start = getCurrentDate()

   for i in range(1020, 1025):
      try:
         data = Helpnow(i)
      except:
         print("Helpnow id %s doesn't exist" % i)
      data.initCatRawInfo()
      #print(data.getDetailedData())
      print(data.getName())

   end = getCurrentDate()
   print ('Cost Time: %s' % getExecutionTime(start, end))
   print("Total CAT request: %s" % getTotalQueryRequestTimes())
