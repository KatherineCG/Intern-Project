''' CAT 'bug' library

Created on Aug 31, 2016

@author: kaiyuanli
'''
from catdata import CatData
from Common.cat.lib.catApi import queryCatInfo, postResultToCat, patchResultToCat
from Common.cat.lib.jsonHandler import addValue, getId
from Common.utils.htmlUtil import genHyperLink
from Common.utils.logger import getLogger

logger = getLogger()

BUGZILLA_URL = 'https://bugzilla.eng.vmware.com'

class Bug(CatData):
   """Single Bug data
   """
   _objType = 'bugzilla'
   _leafNode = True
   _subDataMap = {}

   def __str__(self):
      try:
         return self._bug_name
      except:
         return self._bug_id

   def initCatRawInfo(self):
      super(Bug, self).initCatRawInfo()
      self._bug_id = self.getValueFromCatObj('number')
      self._bug_name = 'PR%s' % self._bug_id
      self._triaged_testruns = self.getIdsFromCatObj('testruns', 'testrun')
      self._hyperlink = "%s/show_bug.cgi?id=%s" % (BUGZILLA_URL, self._bug_id)
      self._htmlId = genHyperLink(content=self._bug_name,
                                  hyperlink=self._hyperlink)

   def getName(self):
      """Return readable bug name in bugzilla
      """
      return self._bug_name

   @staticmethod
   def getBugId(bugzillaId):
      retObjs = queryCatInfo('bugzilla', {'number': bugzillaId})
      if not retObjs:
         logger.error("Bug PR %s hasn't added into CAT database yet", bugzillaId)
         return None
      else:
         return getId(retObjs[0])

   @staticmethod
   def triageBugIdToTestrun(testrunId, bugId=None, bugIdinCat=None):
      return Bug.triageBugIdToTestruns([testrunId], bugId, bugIdinCat)

   @staticmethod
   def triageBugIdToTestruns(testrunIds, bugId=None, bugIdInCat=None):
      if not bugId and not bugIdInCat:
         raise Exception("Please provide at least one argument from bugId, bugIdInCat")

      # TODO: use api v3.0 once it's more stable
      apiVersion = 'v2.0'
      testrunIds = [str(testrunId) for testrunId in testrunIds]
      if bugIdInCat:
         logger.info("Triaging bug %s (id in cat DB) to testruns %s...",
                     bugIdInCat, testrunIds)
         bugObj = {}
         addValue(bugObj, 'testruns', testrunIds, convertToStr=False)
         return patchResultToCat('bugzilla', bugIdInCat, bugObj,
                                 apiVersion=apiVersion)
      else:
         logger.info("Triaging PR%s to testruns %s...", bugId, testrunIds)
         bugId_in_cat = Bug.getBugId(bugId)
         if bugId_in_cat:
            bugObj = {}
            addValue(bugObj, 'testruns', testrunIds,
                     convertToStr=False)
            return patchResultToCat('bugzilla', bugId_in_cat, bugObj,
                                    apiVersion=apiVersion)
         else:
            bugObj = {}
            addValue(bugObj, 'testruns', testrunIds,
                     convertToStr=False)
            addValue(bugObj, 'number', bugId, True)
            return postResultToCat('bugzilla', bugObj, apiVersion=apiVersion)


"""Below code is for test purpose
"""
if __name__ == '__main__':

   for i in range(1, 10):
      data = Bug(i)
      data.initCatRawInfo()
      print("CAT Bug ID %d, PR Name: %s" % (i, data.getName()))


   for i in [1672335, 1979446]:
      print("PR %s, CAT Bug ID: %s" % (i, Bug.getBugId(i)))
