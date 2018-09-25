'''Basic cat object library
Created on Aug 28, 2016

@author: kaiyuanli
'''
from Common.cat.lib.catApi import queryCatInfo, getCatHyperLink
from Common.cat.lib.jsonHandler import getId, getIds, getValue
from Common.utils.commonUtil import formatDict2Str
from Common.utils.htmlUtil import genHyperLink
from Common.utils.logger import getLogger

logger = getLogger()

class CatData(object):
   """Basic cat object data
   """
   _objType = None  # Please override it
   _leafNode = None # Please override it
   _subDataMap = None # Please override it
   _api = 'v2.0'
   _raw_initialized = False

   def __init__(self, catObjId, catObj=None):
      assert(self._objType is not None)
      assert(self._leafNode is not None)
      assert(self._subDataMap is not None)

      self._id = catObjId
      self._catObj = catObj
      if self._catObj is None:
         catData = queryCatInfo(self._objType, {'id': self._id},
                                apiVersion=self._api)
         if not catData:
            raise Exception("%s doesn't exist in CAT" % self)
         else:
            self._catObj = catData[0]
      else:
         # If defined catObj, treat as the baseline input
         self._id = getId(self._catObj)

      self._hyperlink = getCatHyperLink(self._objType, self._id)
      self._htmlId = genHyperLink(content=self._id, hyperlink=self._hyperlink)

      self._full_initialized = False

   def __str__(self):
      return '%s-%s' % (self._objType, self._id)

   def initCatRawInfo(self):
      """Initialize data by calling CAT restAPI
      """
      if self._leafNode:
         """If CAT Object is a leaf node,
         then no need to call initSubDataMap, initReadableInfo
         """
         self._raw_initialized = True
         self._full_initialized = True

   def initReadableInfo(self):
      """Initialize readable info after data fully initialzed
      """
      assert(self._raw_initialized)
      self._full_initialized = True

   @classmethod
   def _addSubData(cls, key, subId, subValue=None):
      """Add sub data to subDataMap
      """
      if key not in cls._subDataMap:
         cls._subDataMap[key] = {}

      if subId not in cls._subDataMap[key]:
         cls._subDataMap[key][subId] = subValue

   @classmethod
   def _getSubDataValue(cls, key, subId=None):
      if key not in cls._subDataMap:
         raise Exception("key %s not in subDataMap" % key)

      if subId is None:
         return cls._subDataMap[key]
      else:
         if subId not in cls._subDataMap[key]:
            raise Exception("sub id %s not in %s of subDataMap" % (subId, key))
         else:
            return cls._subDataMap[key][subId]

   @classmethod
   def initSubDataMap(cls):
      """Initialize sub data recored in subDataMap

      _subDataMap is shared by all instance of cls,
      in order to avoid multiple access rest api to get shared info,
      define initSubDataMap as a classmethod
      """
      if cls._leafNode:
         logger.debug("%s is a leaf node, don't need to init sub data map", str(cls))
         cls._raw_initialized = True
         return

      logger.debug("%s sub data info:\n%s", str(cls), cls._subDataMap)
      for dataType, subData in cls._subDataMap.items():
         if dataType not in CatData.__allSubClasses():
            continue

         for dataId, dataObj in subData.items():
            if dataObj is not None:
               continue
            obj = dataType(dataId)
            obj.initCatRawInfo()
            subData[dataId] = obj

         dataType.initSubDataMap()

         for dataObj in subData.values():
            dataObj.initReadableInfo()

      cls._raw_initialized = True

   def getId(self):
      """Return cat object id
      """
      return str(self._id)

   def getCatObj(self):
      """Return cat object
      """
      return self._catObj

   def getIdFromCatObj(self, attr, objType=None, version='v2.0'):
      return getId(self._catObj, attr, objType=objType, version=version)

   def getIdsFromCatObj(self, attr, subAttr, version='v2.0'):
      return getIds(self._catObj, attr, subAttr, version)

   def getValueFromCatObj(self, attr):
      return getValue(self._catObj, attr)

   def getHtmlId(self):
      """Return Html version ID

      e.g. <a href=https://cat.eng.vmware.com/tester/6883/>6883</a>
      """
      return self._htmlId

   def getHyperLink(self):
      """Return hyperlink of object
      """
      return self._hyperlink

   def getDetailedData(self):
      """Return detailed data info, mainly aimed for debug purpose
      """
      assert(self._full_initialized)
      detailed = ['%s data:' % str(self)]
      detailed.append(formatDict2Str(self.__dict__))

      detailed.append('%s sub data:' % str(self))
      detailed.append(formatDict2Str(self._subDataMap))
      return '\n'.join(detailed)

   def isFullyInitialzied(self):
      """Return True, if cat data is fully initialized
      """
      return self._full_initialized and self._raw_initialized

   @classmethod
   def isRawInitialzied(cls):
      """Return true, if cat data is raw initialized
      """
      return cls._raw_initialized

   @classmethod
   def _clearSubData(cls):
      """Clear init flag
      """
      cls._raw_initialized = False
      cls._subDataMap = {}

   @staticmethod
   def clearAllSubData():
      """Clear init flag in force to support other initialize
      """
      sub_classes = CatData.__allSubClasses()
      for clazz in sub_classes:
         clazz._clearSubData()

   @staticmethod
   def __allSubClasses():
      """Get all sub classes of CatData
      """
      return CatData.__subclasses__()

   @classmethod
   def getFullyInitializedCatObjectList(cls, objectIds, **kwargs):
      """Return a list of initialized cat object
      1. init raw data one by one
      2. init sub data together
      3. init readable data one by one
      """
      catDatas = []
      for objectId in objectIds:
         catData = cls(objectId)
         catData.initCatRawInfo()
         catDatas.append(catData)

      cls.initSubDataMap()

      for catData in catDatas:
         catData.initReadableInfo(**kwargs)

      return catDatas

   @classmethod
   def getFullyInitializedCatObject(cls, objectId, **kwargs):
      catData = cls(objectId)
      catData.initCatRawInfo()
      cls.initSubDataMap()
      catData.initReadableInfo(**kwargs)
      return catData

