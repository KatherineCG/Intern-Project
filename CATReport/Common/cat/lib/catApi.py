"""Cat RestAPI Lib.
"""
import json, urllib

from Common.utils.constants import CAT_AUTH, CAT_API_URL_BASE, CAT_URL
from Common.utils.commonUtil import getBaseDate
from Common.utils.htmlUtil import genHyperLink
from Common.utils.logger import getLogger
from Common.utils.restAPI import urlOpen, httpJsonPost
logger = getLogger()


DEFAULT_QUERY_VERSION = 'v2.0'
DEFAULT_POST_VERSION = 'v2.0'

def __genCatRequestUrl(nameSpace, filterMap, orderBy=None,
                       limitDay=None, limit=None,
                       apiVersion=DEFAULT_QUERY_VERSION):
   baseRequest = "%s/?format=json" % nameSpace
   if filterMap:
      filterInfo = ''
      for filterKey, filterValue in filterMap.items():
         filterInfo += '&%s=%s' % (filterKey, str(filterValue))
      baseRequest = '%s%s' % (baseRequest, filterInfo)

   if limit:
      baseRequest = '%s&limit=%s' % (baseRequest, limit)

   if orderBy:
      baseRequest = '%s&order_by=%s' % (baseRequest, orderBy)

   if limitDay:
      if nameSpace == "build":
         baseRequest = '%s&submit_time__gt=%s' % (baseRequest,
                                             getBaseDate(limitDay, "%Y-%m-%d"))
      else:
         baseRequest = '%s&starttime__gt=%s' % (baseRequest,
                                             getBaseDate(limitDay, "%Y-%m-%d"))
   logger.debug("BaseRequest %s" % baseRequest)
   url = '%s/api/%s/%s&%s' % (CAT_API_URL_BASE, apiVersion,
                              baseRequest, urllib.urlencode(CAT_AUTH))
   return url


def queryCatInfo(nameSpace, filterMap, orderBy=None,
                 limitDay=None, limit=None, apiVersion=DEFAULT_QUERY_VERSION):
   """Query objs from CAT

   @namespace:  CAT base query info
   @filterMap:  CAT RestAPI filter info
   @orderBy:    CAT query objs order
   @limitDay:   The limit latest days of query objs
   @limit:      The limit number of query objs.
                If limit is None, retrieve all CAT objects based on request
   @apiVersion: The CAT Rest API version, default is v2.0

   @return: A list of CAT Objs, [jsonObjs]

   eg. restAPI URL:
   'https://cat-api.eng.vmware.com/api/v2.0/testrun/?format=json&tester=222
    &limit=10&order_by=-endtime'

   Function Usage:
   queryCatInfo(nameSpace=testrun, filterMap={'tester': 222}, limit=10)
   """

   url = __genCatRequestUrl(nameSpace, filterMap, orderBy, limitDay,
                            limit, apiVersion)
   try:
      return_objects = []
      while True:
         request = urlOpen(url, True, retry=3)
         return_data = json.loads(request)
         next_url = return_data['meta']['next']
         return_objects.extend(return_data['objects'])
         if not next_url:
            break
         elif limit is not None:
            break
         else:
            url = '%s%s' % (CAT_API_URL_BASE, next_url)
      return return_objects
   except Exception as e:
      logger.error("RESTAPI Query action failed. URL: %s\nError Info: %s",
                   url, e)

def postResultToCat(namespace, obj, apiVersion=DEFAULT_POST_VERSION):
   """Post an obj to CAT.
   """
   URL_BASE = "%s/api/%s" % (CAT_API_URL_BASE, apiVersion)
   url = "%s/%s/?%s" % (URL_BASE, namespace, urllib.urlencode(CAT_AUTH))
   return httpJsonPost(url, obj)

def patchResultToCat(namespace, patchId, obj, apiVersion=DEFAULT_POST_VERSION):
   """Patch an obj to CAT.
   """
   patchId = str(patchId)
   URL_BASE = "%s/api/%s" % (CAT_API_URL_BASE, apiVersion)
   url = "%s/%s/%s/?%s" % (URL_BASE, namespace, patchId,
                           urllib.urlencode(CAT_AUTH))
   return httpJsonPost(url, obj, method='PATCH')

def getCatHyperLink(objType, objId):
   return "%s/%s/%s" % (CAT_URL, objType, objId)


def getCatHtmlableContent(objType, objId):
   """Return a readable and htmlable content, e.g.
   objType = tester, objId = 6883, return a str:
   <a href=https://cat.eng.vmware.com/tester/6883/>tester-6883</a>
   """
   hyperlink = getCatHyperLink(objType, objId)
   return genHyperLink('%s-%s' % (objType, objId), hyperlink)


"""For Testing purpose...
"""
if __name__ == '__main__':
   from pprint import pprint
   from Common.utils.commonUtil import getCurrentDate, getExecutionTime

   def printOutput(data, info, detailed=True):
      print '\n'
      print '-' * 30
      print 'Test -- %s' % info
      print '-' * 30
      print 'Return length: %s' % len(data)
      if detailed:
         if len(data) <= 2:
            pprint(data)
         else:
            print 'Only print out the first object'
            pprint(data[0])
            print '\nAnd the last one'
            pprint(data[-1])

   start = getCurrentDate()

   printOutput(queryCatInfo('builder', {'id': '107'}), 'CAT Builder Info')
   printOutput(queryCatInfo('machine', {'id': '3196'}), 'CAT Machine Info')

   data = queryCatInfo('testrun', filterMap={'deliverables__build__branch__in': 'vmcore-main',
                                             'area__id__in': '2'},
                       orderBy='-endtime')
   printOutput(data, 'CAT testrun info from CAT without limited')

   data = queryCatInfo('testrun', filterMap={'deliverables__build__branch__in': 'vmcore-main',
                                             'area__id__in': '13'},
                       orderBy='-endtime', limitDay=3, limit=200)
   printOutput(data, 'CAT testrun info with limitDay=3, limit=200')

   data = queryCatInfo('testrun', filterMap={'deliverables__build__branch__in': 'vmcore-main',
                                             'area__id__in': '13'},
                       orderBy='-endtime', limitDay=1, limit=500)
   printOutput(data, 'CAT testrun info with limitDay=1, limit=500 ')

   printOutput(queryCatInfo('testrun', filterMap={'deliverables__id__in': '7353360'}),
               'Query testrun info with default limit number')

   printOutput(queryCatInfo('testrun', filterMap={'deliverables__id__in': '7353360'},
                            total=True),
               'Query all testruns info')

   printOutput(queryCatInfo('machine', {'id': 0}), "Negative Test: Object Not Exist")

   end = getCurrentDate()
   print getExecutionTime(start, end)
