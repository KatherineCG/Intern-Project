''' CAT 'workload' lib

Created on Aug 28, 2016

@author: kaiyuanli
'''
import re

from catdata import CatData
from Common.cat.lib.catApi import queryCatInfo, postResultToCat, patchResultToCat
from Common.cat.lib.jsonHandler  import addId, addValue, getId
from Common.utils.constants import NOT_AVAILABLE
from Common.utils.logger import getLogger

logger = getLogger()

TESTESX_FLAG = 'testesx'
TESTESX_NIMBUS_FLAG = '--hostType nimbus'
TESTESX_HWDB_FLAG = '--hostType hwdb'
TESTESX_NO_VMTREE_FLAG = '--no-vmtree'


class Workload(CatData):
   """Single Workload data
   """
   _objType = 'workload'
   _api = 'v3.0'
   _leafNode = True
   _subDataMap = {}

   def initCatRawInfo(self):
      super(Workload, self).initCatRawInfo()
      self._name = self.getValueFromCatObj('name')
      self._executable = self.getValueFromCatObj('executable')
      self._launch_host = self.getValueFromCatObj('launch_host')
      self._timeout = self.getValueFromCatObj('timeout')
      self._skip_boot = self.getValueFromCatObj('skip_boot')
      self._needs_reboot = self.getValueFromCatObj('needs_reboot')
      self._tags = self.getValueFromCatObj('tags')

      if TESTESX_FLAG in self._executable:
         self._testesx_workload = True
      else:
         self._testesx_workload = False

   def getWorkloadName(self):
      """Get workload name
      """
      assert (self._full_initialized)
      return self._name

   def getShortenVersionWorkloadName(self):
      assert (self._full_initialized)
      workload_name = self._name
      replace_dict = {'testesxgroup-': '+',
                      '-hwdb': '',
                      '-nimbus': '',
                      '-L0TestCoverage': '',
                      '-L1TestCoverage': ''}
      for old, new in replace_dict.items():
         workload_name = workload_name.replace(old, new)
      return workload_name

   def isTestesxWorkload(self):
      return self._testesx_workload 

   def getHostType(self):
      """Get Host Type
      """
      if not self.isTestesxWorkload():
         return NOT_AVAILABLE
      elif TESTESX_HWDB_FLAG in self._executable:
         return 'hwdb'
      elif TESTESX_NIMBUS_FLAG in self._executable:
         return 'nimbus'
      else:
         return 'physical'

   def isNoVmTree(self):
      if not self.isTestesxWorkload():
         return NOT_AVAILABLE
      elif TESTESX_NO_VMTREE_FLAG in self._executable:
         return 'True'
      else:
         return ''

   def _parseValueByCmdOption(self, commandKey, defaultValue=None):
      """Parse value out by command option in workload executable field.

      e.g. executable: /test-entry --group a --group b --group c
      commandKey = group, return ['a', 'b', 'c']
      """
      info = '%s ' % self.getExecutable()
      pattern = '--%s\s(\S+)' % commandKey
      result_list = re.findall(pattern, info)

      if not result_list:
         if defaultValue is not None:
            return defaultValue
         else:
            return NOT_AVAILABLE
      else:
         return ','.join([str(result) for result in result_list])

   def getGroups(self):
      """Get cover group
      """
      return self._parseValueByCmdOption('group')

   def getJobs(self):
      """Get Job Level
      """
      if not self.isTestesxWorkload():
         return NOT_AVAILABLE
      else:
         return self._parseValueByCmdOption('jobs')

   def getNumHosts(self):
      """Get Host Number
      """
      if not self.isTestesxWorkload():
         return NOT_AVAILABLE
      else:
         return self._parseValueByCmdOption('numHosts', defaultValue=1)

   def getBootOptions(self):
      """Get Boot Options
      """
      if not self.isTestesxWorkload():
         return NOT_AVAILABLE
      else:
         return self._parseValueByCmdOption('bootOption', defaultValue='')

   def getFeatureSwitches(self):
      """Get Feature Switch
      """
      if not self.isTestesxWorkload():
         return NOT_AVAILABLE
      else: 
         return self._parseValueByCmdOption('enableFeature', defaultValue='')

   def getExecutable(self):
      return self._executable

   def getTimeout(self):
      return self._timeout

   def getTags(self):
      return self._tags

   @staticmethod
   def getWorkloadIds(wlNames):
      """Get workload id via workload name @wlName
      """
      wlIds = []
      for wlName in wlNames:
         retObj = queryCatInfo('workload', {'name': wlName})

         if not retObj:
            raise Exception("No workload named as %s " % wlName)
         else:
            wlIds.append(getId(retObj[0]))

      return wlIds

   @staticmethod
   def addWorkload(name, executable, launchhost, timeout,
                   needsreboot, skipboot):
      """Add workload into CAT
      """
      logger.debug("Adding workload: %s" % vars())
      wlObj = {}
      addValue(wlObj, 'name', name)
      addValue(wlObj, 'executable', executable)
      addValue(wlObj, 'launch_host', launchhost)
      addValue(wlObj, 'timeout', timeout)
      addValue(wlObj, 'needs_reboot', needsreboot, convertToStr=False)
      addValue(wlObj, 'skip_boot', skipboot, convertToStr=False)
      addId(wlObj, 'site', 1)
      return postResultToCat('workload', wlObj)

   @staticmethod
   def modifyWorkload(wlId, name=None, executable=None, launchhost=None,
                      timeout=None, needsreboot=None, skipboot=None):
      """Modify workload (workload id = @wlId) info
      """
      logger.debug("Modifying workload: %s" % vars())
      wlObj = {}

      if name:
         addValue(wlObj, 'name', name)

      if executable:
         addValue(wlObj, 'executable', executable)

      if launchhost:
         addValue(wlObj, 'launch_host', launchhost)

      if timeout:
         addValue(wlObj, 'timeout', timeout)

      if needsreboot:
         addValue(wlObj, 'needs_reboot', needsreboot, convertToStr=False)

      if skipboot:
         addValue(wlObj, 'skip_boot', skipboot, convertToStr=False)

      return patchResultToCat('workload', wlId, wlObj)


"""Below code is for test purpose
"""
if __name__ == '__main__':

   wlIds = """
43410
35214
43416
19613
5427
35217
2369
48726
"""

   wlIds = wlIds.strip().split('\n')
   wlDatas = []

   for wlId in wlIds:
      wlData = Workload(wlId)
      wlData.initCatRawInfo()
      wlDatas.append(wlData)

   Workload.initSubDataMap()

   for wlData in wlDatas:
      wlData.initReadableInfo()
      print("Workload Name %s (ID: %s), from testesx %s" % \
            (wlData.getWorkloadName(), wlData.getId(),
             wlData.isTestesxWorkload()))
      print("  Host Type: %s, Jobs: %s, Num Hosts: %s" % (wlData.getHostType(),
                                                          wlData.getJobs(),
                                                          wlData.getNumHosts()))
      print("  Groups: %s" % wlData.getGroups())
      print("  --no-vmtree? : %s" % wlData.isNoVmTree())
      print("  Bootoptions: %s" % wlData.getBootOptions())
      print("  FeatureSwitches: %s" % wlData.getFeatureSwitches())
      print("  Executable: %s" % wlData.getExecutable())
      print("  Timeout: %s" % wlData.getTimeout())
      print("  Tags: %s" % wlData.getTags())
      print("---------------------------\n")

   '''
   # Get workload from tester and modify workload info one by one
   from Common.cat.lib.catApi import queryCatInfo
   from Common.cat.lib.jsonHandler import getIds
   from workunit import Workunit
   tester = queryCatInfo('tester', {'id': 27327})[0]
   wu_ids = getIds(tester, 'workunits', 'workunit')
   print wu_ids

   wuDatas = []
   for wu_id in wu_ids:
      wuData = Workunit(wu_id)
      wuData.initCatRawInfo()
      wuDatas.append(wuData)

   Workunit.initSubDataMap()

   for wuData in wuDatas:
      wuData.initReadableInfo()
      wlData = wuData.getWorkloadData()
      print wlData

      new_workload_name = '%s-hwdb' % wlData.getWorkloadName()
      new_executable = '%s --hostType hwdb' % wlData.getExecutable()
      print new_workload_name
      print new_executable

      Workload.modifyWorkload(wlData.getId(), new_workload_name, new_executable)
   '''

   '''
   # Create workload
   workloadName = 'testesxgroup-jumpstart-layer1-nimbus'
   launchHost = 'sc-prd-cat-worker021.eng.vmware.com'
   executable = '/dbc/pa-dbc1102/kaiyuanli/testesxlauncher/main-stage/git/mts-git/bin/nimbus-testesxdeploy-launcher --group jumpstart --nimbusConfigFile /mts/git/nimbus-configs/config --hostType nimbus --jobs 1'
   Workload.addWorkload(workloadName, executable, launchHost, 7200, False, True)

   workloadName = 'testesxgroup-hp-layer1-nimbus'
   launchHost = 'sc-prd-cat-worker021.eng.vmware.com'
   executable = '/dbc/pa-dbc1102/kaiyuanli/testesxlauncher/main-stage/git/mts-git/bin/nimbus-testesxdeploy-launcher --group hp --nimbusConfigFile /mts/git/nimbus-configs/config --hostType nimbus --jobs 1'
   Workload.addWorkload(workloadName, executable, launchHost, 7200, False, True)
   '''
