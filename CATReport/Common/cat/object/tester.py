''' CAT 'tester' object library
Created on Sep 21, 2016

@author: kaiyuanli
'''
from catdata import CatData
from workunit import Workunit
from machine import Machine
from Common.cat.lib.catApi import postResultToCat, patchResultToCat
from Common.utils.logger import getLogger

logger = getLogger()

class Tester(CatData):
   """Single Tester data
   """
   _objType = 'tester'
   _leafNode = False
   _subDataMap = {}

   def initCatRawInfo(self):
      super(Tester, self).initCatRawInfo()
      self._workunit_ids = self.getIdsFromCatObj('workunits', 'workunit')
      self._machine_ids = self.getIdsFromCatObj('machines', 'machine')
      self._lastupdate = self.getValueFromCatObj('lastupdate')
      self._running = self.getValueFromCatObj('running')
      self._status = self.getValueFromCatObj('status')

      for wu_id in self._workunit_ids:
         Tester._addSubData(Workunit, wu_id)

      for machine_id in self._machine_ids:
         Tester._addSubData(Machine, machine_id)

   def isRunning(self):
      return self._running

   def getStatus(self):
      return self._status

   def initReadableInfo(self):
      super(Tester, self).initReadableInfo()
      self._workunit_datas = []
      for workunit_id in self._workunit_ids:
         workunit_data = Tester._getSubDataValue(Workunit, workunit_id)
         self._workunit_datas.append(workunit_data)

      self._machine_names = []
      for machine_id in self._machine_ids:
         machine_data = Tester._getSubDataValue(Machine, machine_id)
         self._machine_names.append(machine_data.getMachineName())

   def getWorkunitsData(self):
      assert(self.isFullyInitialzied())
      return self._workunit_datas

   def getMachineNames(self):
      assert(self.isFullyInitialzied())
      return ','.join(self._machine_names)

   @staticmethod
   def createTester(hostName, owner):
      logger.debug("Creating tester: %s" % vars())
      machine_id = Machine.getMachineId(hostName)
      machineData = Machine(machine_id)
      machineData.initCatRawInfo()
      Machine.initSubDataMap()
      machineData.initReadableInfo()
      machine_location = machineData.getLocation()
      logger.info("Machine %s location is %s", hostName, machine_location)

      if machine_location == 'PA':
         launchhost = "/api/v3.0/testermachine/141/"
      else:
         launchhost = "/api/v3.0/testermachine/230/"

      machines =  ["/api/v3.0/machine/%s/" % machine_id]
      testerObj = {"launch_host": launchhost,
                   "machines": machines,
                   "site": "/api/v2.0/site/1/",
                   "owner": owner}
      return postResultToCat('tester', testerObj, apiVersion='v3.0')

   @staticmethod
   def modifyTesterStatus(testerId, status):
      logger.info("Modifying tester: %s" % vars())
      choices = ['enable', 'disable', 'abort']
      if status not in choices:
         raise Exception("status %s invalid, choices: %s" % (status, choices))

      testerObj = {"action": status}
      return patchResultToCat('tester', testerId, testerObj, apiVersion='v3.0')


"""Below code is for test purpose
"""
if __name__ == '__main__':
   tester = Tester(27282)
   tester.initCatRawInfo()
   Tester.initSubDataMap()
   tester.initReadableInfo()

   print(tester.getDetailedData())

   '''
   # Create Tester
   print(Tester.createTester('PA', 3196, 'kaiyuanli'))
   '''