''' Common parser functions
Created on Dec 15, 2017

@author: kaiyuanli
'''
import re

from Common.testesx.constants import *


KW_X = '*' * 6

def trunctStr(original, trunct_key, trunct_from_start=False):
   """Truncate the original string by trunct_key
   If trunct_from_start = True, return sub string from index 0 to the first index of trunct_key
   Or, return sub string from the first index after trunct_key to the end
   """
   if trunct_key not in original:
      return original

   if not trunct_from_start:
      end_index = original.index(trunct_key)
      return original[0:end_index].strip('\n')
   else:
      index = original.index(trunct_key) + len(trunct_key)
      return original[index:].strip('\n')

def replaceStr(info, oldNewList):
   """Replace info by defining a list of (old, new) tuple
   """
   for old, new in oldNewList:
      info = re.sub(old, new, info)

   return info

#===============================
# Unified info related functions
#===============================
def convertDigital2Star(info):
   """Convert digital to *
   """
   return re.sub('\d', '*', info)

def shortenStars(info):
   """If str contains > 6 sequential *, shorten them to 7
   """
   return re.sub('\*{7,}', KW_X, info)

def getUnifiedIpAddr(info):
   """Return unified IP Address info
   """
   return re.sub('\d+\.\d+\.\d+\.\d+', '***.***.***.***', info)

def getUnifiedPsodInfo(info):
   """Return unified PSOD info
   """
   if '#PF Exception' in info:
      # convert world id, and ip, addr info
      info = replaceStr(info,
                        [('world\s\d+:', 'world *******:'),
                         ('IP\s.*\saddr\s.*',
                          'IP 0x%s addr 0x%s' % (KW_X, KW_X))])

   elif 'Failed to reap world' in info:
      info = convertDigital2Star(info)

   elif 'Panic from another CPU' in info:
      # convert cpu, world ID and ip, randomOff addr info
      info = replaceStr(info,
                        [('\(cpu \d+, world \d+\)', '(cpu **, world %s)' % KW_X),
                        ('ip=0x.*\srandomOff=0x.*',
                         'ip=0x%s randomOff=0x%s' % (KW_X, KW_X))])

   return info

def getUnifiedUWCoredumpInfo(info):
   """Return unified userworld coredump info
   """
   # If zdump located in datastore, unified datastore name
   info = re.sub('/vmfs/volumes/.*?/', '/vmfs/volumes/*******/', info)
   info = convertDigital2Star(info)
   return info

def getUnifiedLogInfo(result, info):
   """Return unified info based on result
   """
   info = getUnifiedIpAddr(info)

   if result == LEVEL_PSOD:
      info = getUnifiedPsodInfo(info)

   elif result == LEVEL_UWCOREDUMP:
      info = getUnifiedUWCoredumpInfo(info)

   return shortenStars(info)