'''
Created on Oct 23, 2015

@author: kaiyuanli
'''

import re

# -----------------------------------------
# Common funcs to get ID / Value from JSON #
# -----------------------------------------

def _getIdFromObjUrl(objType, url, version='v2.0'):
   """Get id from url /api/v2.0/<objType>/<id>/"""
   m = re.match('/api/%s/%s/(\d+)/' % (version, objType), url)
   return str(m.group(1))

def getId(obj, attr='id', objType=None, version='v2.0'):
   """Get Id (type: string) from jsonObj returned from CAT rest API
   @obj: jsonObj which id is located in
   @attr: the attribute of the id in @obj
   @objType: the objType in URL. Default = @attr
   @version: version of CAT restAPI

   eg. Get location id from below obj =
   {
      "location": "/api/v2.0/location/3/"
   }

   id = getId(obj, 'location')

   Get deliverable id from below obj:
   {
      "sitedeliverable": "/api/v2.0/deliverable/6619553/"
   }

   id = getId(obj, sitedeliverable, deliverable)
   """
   if attr == 'id':
      return str(obj[attr])
   else:
      if attr not in obj:
         return None

      if obj[attr] is None:
         return None

      if objType is None:
         objType = attr

      return _getIdFromObjUrl(objType, obj[attr], version)

def getIds(obj, attr, subAttr, version='v2.0'):
   """Get Ids from jsonObj returned from CAT rest API
   @obj: jsonObj which id is located in
   @attr: root attribute of the id
   @subAttr: sub attribute of the id
   @version: version of CAT restAPI

   eg. Get machine ids from below obj =
   {
        "machines":
            [
                "/api/v2.0/machine/6795/",
                "/api/v2.0/machine/6798/"
            ],
   }

   ids = getIds(obj, machines, machine)
   """
   returnIds = []
   urlList = obj[attr]
   for url in urlList:
      if isinstance(url, str) or isinstance(url, unicode): 
         returnIds.append(_getIdFromObjUrl(subAttr, url, version))
      elif isinstance(url, dict):
         returnIds.append(getId(url, subAttr, version=version))
      else:
         raise NotImplementedError("Please add code for parser type: %s" % type(url))

   return returnIds

def getValue(obj, attr):
   """Get value from jsonObj
   """
   if attr not in obj:
      raise Exception("Attribute %s is not exist in obj %r" % (attr, obj))

   info = obj[attr]
   if isinstance(info, list):
      infoList = []
      for msg in info:
         if isinstance(msg, unicode):
            infoList.append(msg.encode())
         else:
            infoList.append(msg)

      return ','.join(infoList)

   elif isinstance(info, unicode):
      return info.encode()
   else:
      return info

# ---------------------------------
# Common funcs to build a JSON obj #
# ---------------------------------
def addValue(obj, attr, value, convertToStr=True, ignoreEmpty=True):
   """Add value to obj:
   @obj[@attr] = value
   """
   if ignoreEmpty and value is None:
      return

   if convertToStr:
      value = str(value)
   obj[attr] = value


def addId(obj, attr, inputId, version='v2.0', ignoreEmpty=True):
   """Add id to obj:
   @obj[@attr] = '/api/@version/@attr/@id/'
   """
   if ignoreEmpty and inputId is None:
      return

   inputId = str(inputId)
   if attr == 'id':
      obj['id'] = inputId
   else:
      url = '/api/%s/%s/%s/' % (version, attr, inputId)
      obj[attr] = url

def addIds(obj, attr, subAttr, inputIds, version='v2.0'):
   """Add ids to obj
   @obj[@attr] = ['/api/@version/@subAttr/@inputId/',
                  '/api/@version/@subAttr/@inputId/',
                  ...,
                  ]
   """
   obj[attr] = []
   for inputId in inputIds:
      inputId = str(inputId)
      obj[attr].append('/api/%s/%s/%s/' % (version, subAttr, inputId))

if __name__ == '__main__':
   jsonObj = {}
   addId(jsonObj, 222, 'tester')
   print jsonObj

