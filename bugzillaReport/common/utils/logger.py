'''Logger library
Created on Aug 28, 2016

@author: kaiyuanli
'''
import logging, os, stat, sys

from commonUtil import getBaseDate, getCurrentDate, getDateFromTimestamp, \
                       LOG_DIR, SCRIPT_NAME, SCRIPT_USER

_logger = None

CONSOLE_FORMAT = "%(message)s"
FILE_FORMAT = "%(asctime)s - %(filename)s:%(lineno)s - %(levelname)s - %(funcName)s: %(message)s"
CLEANUPDAYS = 3

def getLogger():
   global _logger
   logger = logging.getLogger(SCRIPT_NAME)

   if logger == _logger:
      return _logger

   _logger = logger
   logger.setLevel(logging.DEBUG)
   # create console handler and set level to debug
   ch = logging.StreamHandler(sys.stdout)
   ch.setLevel(logging.INFO)

   # create file handler and set level to DEBUG
   __setupLOG_DIR()

   logName = "%s-%s-%s.log" % (SCRIPT_NAME, SCRIPT_USER, getCurrentDate())
   logfile = os.path.join(LOG_DIR, logName)
   fh = logging.FileHandler(logfile)
   fh.setLevel(logging.DEBUG)

   # add formatter to ch and fh
   ch.setFormatter(logging.Formatter(CONSOLE_FORMAT))
   fh.setFormatter(logging.Formatter(FILE_FORMAT))

   # add ch, fh to logger
   logger.addHandler(ch)
   logger.addHandler(fh)
   return _logger

def __setupLOG_DIR():
   """Setup log dir
   1. Create dir if not exist
   2. Clean up log files if created <CLEANUPDAYS> days ago
   """
   if not os.path.exists(LOG_DIR):
      os.makedirs(LOG_DIR)
      os.chmod(LOG_DIR, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
   else:
      baseTime = getBaseDate(CLEANUPDAYS)
      for dirName, _, fileNames in os.walk(LOG_DIR):
         for fileName in fileNames:
            try:
               filePath = os.path.join(dirName, fileName)
               createTime = getDateFromTimestamp(os.path.getctime(filePath))
               if createTime < baseTime :
                  print('Removing file: %s' % filePath)
                  os.remove(filePath)
            except Exception as e:
               print('Failed to remove file %s: %s' % (fileName, str(e)))


"""For Testing purpose...
"""
if __name__ == '__main__':
   logger = getLogger()
   print logger
   logger = getLogger()
   print logger
