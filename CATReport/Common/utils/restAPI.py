"""HTTP RestAPI Lib.
"""
import json, urllib2

from logger import getLogger
logger = getLogger()

# Unset proxy to avoid exception during RestAPI operations
proxy_support = urllib2.ProxyHandler({})
opener = urllib2.build_opener(proxy_support)
urllib2.install_opener(opener)

def urlOpen(url, raiseErr=False, retry=1, timeout=120):
   """Open URL via urllib2

   @raiseErr: True, will raise Exception out if still failed after @rety times
   @retry: the retry times of url open, or may hit Connection timed out exception
           due to intermimment network issue
   @timeout: url open timeout value in second
   """
   for i in range(retry):
      try:
         logger.debug("Opening url %s" % url)
         request = urllib2.urlopen(url, timeout=timeout)
         return request.read()
      except KeyboardInterrupt:
         raise
      except Exception as e:
         if i < (retry - 1):
            logger.debug("Failed to open url: %s, reason %s, retrying...",
                         url, str(e))
            continue
         elif raiseErr:
            raise
         else:
            logger.debug("Failed to open url: %s after %d times retry", url,
                         retry)
            break

def httpJsonPost(url, params, method='POST'):
   """Send an HTTP POST request with content-type as JSON.

   @return: If succeed, [True,  postObj]
         If failed,  [False, errorInfo]
   """
   data = json.dumps(params)
   header = {"Content-type": "application/json",
             "Content-Length": len(data)}
   logger.debug("%s obj %r to URL %s", method, data, url)

   req = urllib2.Request(url, data, header)
   req.get_method = lambda: method
   try:
      data = urlOpen(req, True)
      obj = json.loads(data)
      return (True, obj)
   except urllib2.HTTPError, e:
      errMsg = e.read()
      logger.debug('FAILED to %s %r to url %s. Reason: %s', method, data,
                    url, errMsg)
      return (False, errMsg)

if __name__ == '__main__':
   url = 'http://cat-api.eng.vmware.com/api/v2.0/testrun/?format=json&area__id__in=21772&deliverables__build__branch__in=vmcore-main&deliverables__build__bldtype__in=beta&limit=100&order_by=-endtime&starttime__gt=2017-09-09&username=kaiyuanli&api_key=801495a070d40ea1d399fe1a24f197717bff3e76'
   print urlOpen(url)
