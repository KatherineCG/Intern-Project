'''
Created on Sep 1, 2016

@author: kaiyuanli
'''
from catdata import CatData
from Common.cat.lib.catApi import queryCatInfo
from Common.cat.lib.jsonHandler import getId, getValue
from Common.utils.constants import NOT_AVALIABLE

import math

MB = 1024

class Machine(CatData):
   """Single Machine data
   """
   _objType = 'machine'
   _api = 'v3.0'
   _leafNode = False
   _subDataMap = {}

   def initCatRawInfo(self):
      super(Machine, self).initCatRawInfo()
      self._hostname = self.getValueFromCatObj('hostname')
      if self._hostname is None:
         self._hostname = NOT_AVALIABLE
      elif '-HWDB' in self._hostname:
         self._hostname = self._hostname[0: self._hostname.index('-HWDB')]

      self._ilo_hostname = self.getValueFromCatObj('ilo_hostname')
      self._ilo_username = self.getValueFromCatObj('ilo_username')
      self._ilo_password = self.getValueFromCatObj('ilo_password')
      self._serial_host = self.getValueFromCatObj('serial_host')
      self._serial_port = self.getValueFromCatObj('serial_port')
      self._suite_location = self.getValueFromCatObj('suite_location')
      self._macAddrs = self.getValueFromCatObj('mac_addresses')
      self._location_id = self.getIdFromCatObj('location', version='v3.0')

      # Hardware Info
      self._vendor = self.getValueFromCatObj('dmi_vendor_name')
      self._product = self.getValueFromCatObj('dmi_product_name')
      self._cpu_cores = self.getValueFromCatObj('cpu_num_cores')

      cpu_model_info = self.getValueFromCatObj('cpu_model_name')
      if cpu_model_info:
         cpu_model_info = cpu_model_info.split()
         cpu_model_name = [i for i in cpu_model_info if i != '']
         self._cpu_model_name = ' '.join(cpu_model_name)
      else:
         self._cpu_model_name = NOT_AVALIABLE

      physical_memory_total = self.getValueFromCatObj('physical_memory_total')
      phy_mem = float(physical_memory_total) / (MB * MB)
      phy_mem = int(math.ceil(phy_mem))
      self._physical_memory = "%d GB" % phy_mem
      self._physical_memory_in_gb = "%d" % phy_mem

      cpu_family = self.getValueFromCatObj('cpu_family')
      if cpu_family:
         self._cpu_family = self.__convertToHex(cpu_family)
      else:
         self._cpu_family = NOT_AVALIABLE

      cpu_model = self.getValueFromCatObj('cpu_model')
      if cpu_model:
         self._cpu_model = self.__convertToHex(cpu_model)
      else:
         self._cpu_model = NOT_AVALIABLE

      self._bios_version = self.getValueFromCatObj('bios_version')
      self._bios_release_date = self.getValueFromCatObj('bios_release_date')

      Machine._addSubData('location_id', self._location_id)

   def __convertToHex(self, value):
      return hex(value)[2:].upper()

   @classmethod
   def initSubDataMap(cls):
      locationData = cls._getSubDataValue('location_id')
      for location_id in locationData.keys():
         if locationData[location_id]:
            continue

         try:
            locationObj = queryCatInfo('location', {'id': location_id},
                                       apiVersion='v3.0')[0]
            locationData[location_id] = getValue(locationObj, 'name')
         except:
            locationData[location_id] = NOT_AVALIABLE

      cls._raw_initialized = True

   def initReadableInfo(self):
      super(Machine, self).initReadableInfo()
      self._location = Machine._getSubDataValue('location_id', self._location_id)

   def getMachineName(self):
      assert(self._full_initialized)
      return self._hostname

   def getLocation(self):
      assert(self._full_initialized)
      return self._location

   @staticmethod
   def getMachineId(hostName):
      retObjs = queryCatInfo('machine', {'hostname': hostName}, apiVersion='v3.0')
      if not retObjs:
         raise Exception("No machine named as %s" % hostName)
      else:
         return getId(retObjs[0])


if __name__ == '__main__':

   machineData = Machine.getFullyInitializedCatObject(6341)
   print(machineData.getDetailedData())

