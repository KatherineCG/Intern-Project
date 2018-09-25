#!/build/toolchain/lin64/python-2.7.6/bin/python -u
'''
Created on Feb 4, 2016

@author: kaiyuanli
'''
from argparse import ArgumentParser, RawTextHelpFormatter
from commonUtil import formatList2Str
from constants import TESTRUN_RESULTS
from logger import getLogger

MULTIPLE_OPTION = '   This option can be passed multiple times.'
(NO_NEED, NEED, MUST_HAVE) = list(range(3))

DEFAULT_DAY = 1
BUG_HISTORY_DEFAULT_DAY = 7
DEFAULT_HELP_INDENT = 30

logger = getLogger()


def addOutputArguments(parser, defaultDir='.', defaultPrefix=None):
   parser.add_argument('--output-dir', type=str, dest='outputDir',
                       default=defaultDir,
                       help='Output directory. (default %s)' % defaultDir)

   parser.add_argument('--output-prefix', type=str, dest='outputPrefix',
                       default=defaultPrefix,
                       help=('Output file name prefix. '
                             '(default %s)' % defaultPrefix))

def getAppendableHelpMsg(helpMsg, indent=DEFAULT_HELP_INDENT):
   if not helpMsg.endswith('.'):
      helpMsg = '%s.' % helpMsg

   return '%s %s' % (helpMsg.ljust(indent), MULTIPLE_OPTION)



class TestrunFilters(ArgumentParser):
   """Parser used to filter testruns according to area, branch and wlNames
   """
   def __init__(self, desp, limit=NEED, areaBranch=NEED, wl=NEED,
                wu=NEED, tester=NEED, result=NO_NEED,
                testrun=NEED, email=NEED, bugzilla=NO_NEED):
      super(TestrunFilters, self).__init__(description=desp,
                                           formatter_class=RawTextHelpFormatter)
      # Init args flag
      self.__limitArg = limit
      self.__areaBranchArg = areaBranch
      self.__wlArg = wl
      self.__wuArg = wu
      self.__testerArg = tester
      self.__resultArg = result
      self.__testrunArg = testrun
      self.__emailArg = email
      self.__bugzillaArg = bugzilla

      # Init args
      self.areaNames = []
      self.areaIds = []
      self.branchNames = []
      self.wlNames = []
      self.testerIds = []
      self.wuIds = []
      self.results = []
      self.testrunIds = []

      self._addTestrunFilterArguments()
      self._addEmailArguments()
      self._addBugzillaArguments()
      self._argus_info = []

   def _addTestrunFilterArguments(self):
      """Add testrun filter related command line arguments.
         sorted option alphabetically
      """
      testrunGroup = self.add_argument_group('Options for filter testruns')
      if self.__areaBranchArg:
         self._areaArguments(testrunGroup)
         self._branchArguments(testrunGroup)

      if self.__limitArg:
         testrunGroup.add_argument("-d", metavar="limitDay", dest="limitDay",
                                   default=DEFAULT_DAY, type=int,
                                   help="The limited day for filter testruns. (default: %(default)s)")

         testrunGroup.add_argument("-D", metavar="bugHistoryDay", dest="bugHistoryDay",
                                   default=BUG_HISTORY_DEFAULT_DAY, type=int,
                                   help="The limited day for filter testruns while getting bug history. (default: %(default)s)")
         testrunGroup.add_argument("-l", metavar="limitNumber", dest="limitNumber",
                                   required=False, type=int, default=None,
                                   help="The latest N testruns retrieved from CAT. default: retrieve all testruns in the last <limitDay>")

      if self.__resultArg:
         testrunGroup.add_argument('-r', action='append', dest='results',
                                   choices=TESTRUN_RESULTS,
                                   required=True,
                                   help=getAppendableHelpMsg('Result type of testruns'))

      if self.__testerArg:
         testrunGroup.add_argument("-t", metavar='Tester', dest='testerIds',
                                   action='append', required=False,
                                   help=getAppendableHelpMsg('Tester Id of testruns'))

      if self.__wuArg:
         testrunGroup.add_argument("-u", metavar="WorkunitId", dest="wuIds",
                                   action='append', required=False,
                                   help=getAppendableHelpMsg('Workunit Id of testruns'))

      if self.__wlArg:
         testrunGroup.add_argument("-w", action="append", dest="wlNames",
                                   metavar="WorkloadName", required=False,
                                   help=getAppendableHelpMsg('Workunit Name of testruns'))

      if self.__testrunArg:
         testrunGroup.add_argument("--testrunid", action='append',
                                   dest='testrunIds', metavar='TestrunId',
                                   required=False,
                                   help=getAppendableHelpMsg('Ids of testruns'))

   def _areaArguments(self, testrunGroup):
      """Options for area
      """
      if self.__areaBranchArg is NO_NEED:
         return

      if self.__areaBranchArg is NEED:
         required= False
      elif self.__areaBranchArg is MUST_HAVE:
         required = True
      else:
         raise NotImplementedError("Please support argu type %s first" % \
                                   self.__areaBranchArg)

      areaInfo = testrunGroup.add_mutually_exclusive_group(required=required)
      areaInfo.add_argument("-a", action="append", dest="areaNames",
                            metavar="AreaName",
                            help=getAppendableHelpMsg('Area name of testruns'))

      areaInfo.add_argument("--areaId", action="append", dest="areaIds",
                            metavar="AreaId",
                            help=getAppendableHelpMsg('Area id of testruns'))

   def _branchArguments(self, testrunGroup):
      """Options for branch
      """
      if self.__areaBranchArg is NO_NEED:
         return

      if self.__areaBranchArg is NEED:
         required = False
      elif self.__areaBranchArg is MUST_HAVE:
         required = True
      else:
         raise NotImplementedError("Please support argu type %s first" % \
                                   self.__areaBranchArg)

      testrunGroup.add_argument("-b", action="append", dest="branchNames",
                                metavar="BranchName", required=required,
                                help=getAppendableHelpMsg('Branch name of testruns'))

      testrunGroup.add_argument("--bldType", action="append", dest="bldTypes",
                                metavar="BuildType", required=False,
                                help=getAppendableHelpMsg('Branch type of testruns'))

   def _addEmailArguments(self):
      """Options for email feature.
      """
      if not self.__emailArg:
         return

      emailGroup = self.add_argument_group('Options for sending auto-email')
      emailGroup.add_argument("--subject-prefix", dest="emailSubjectPrefix",
                              metavar="EmailSubjectPrefix",
                              help=getAppendableHelpMsg('The email subect prefix'))
      emailGroup.add_argument("-e", action="append", dest="emailToList",
                              metavar="LDAP", required=False,
                              help=getAppendableHelpMsg('LDAP user whom script will send email to'))

      emailGroup.add_argument("--cc-user", action="append", dest="emailCCUser",
                              metavar="LDAP", required=False,
                              help=getAppendableHelpMsg('LDAP user who will receive the mail copy'))
      emailGroup.add_argument("--email-sender", dest="emailSender",
                              metavar="LDAP", required=False,
                              help=getAppendableHelpMsg('LDAP user who will send the email'))

   def _addBugzillaArguments(self):
      """Options for bugzilla feature.
      """
      if not self.__bugzillaArg:
         return

      emailGroup = self.add_argument_group('Options for getting bug info from bugzilla')
      emailGroup.add_argument("--bugzilla-user", dest="bugzillaUsername",
                              metavar="bugzillaUsername",
                              help=getAppendableHelpMsg('The username for login bugzilla'))
      emailGroup.add_argument("--bugzilla-password", dest="bugzillaPassword",
                              metavar="bugzillaPassword",
                              help=getAppendableHelpMsg('The user password for login bugzilla'))


   def parse_args(self, **kw):
      args = super(TestrunFilters, self).parse_args(**kw)
      if self.__areaBranchArg:
         self.areaNames = args.areaNames
         self.areaIds = args.areaIds
         self.branchNames = args.branchNames
         self.bldTypes = args.bldTypes

      if self.__testerArg:
         self.testerIds = args.testerIds

      if self.__wlArg:
         self.wlNames = args.wlNames

      if self.__wuArg:
         self.wuIds = args.wuIds

      if self.__resultArg:
         self.results = args.results

      if self.__testrunArg:
         self.testrunIds = args.testrunIds

      if self.__limitArg:
         self.limitDay = args.limitDay
         self.bugHistoryDay = args.bugHistoryDay
         self.limitNumber = args.limitNumber

      if self.__emailArg:
         self.emailToList = args.emailToList
         self.emailSubjectPrefix = args.emailSubjectPrefix
         self.emailSender = args.emailSender
         self.emailCCUser = args.emailCCUser

      if self.__bugzillaArg:
         self.bugzillaUsername = args.bugzillaUsername
         self.bugzillaPassword = args.bugzillaPassword

      self._argus_info = self._initArgumentList()
      logger.debug("User's total input args: %s", args)
      return args

   def _appendInfo(self, info_list, key, value):
      if not value:
         return
      else:
         if isinstance(value, list):
            value = ', '.join(value)
         info_list.append((key, value))

   def _initArgumentList(self):
      argusInfo = []

      if self.__areaBranchArg:
         from Common.cat.object.area import Area
         if not self.areaIds and self.areaNames:
            self.areaIds = Area.getAreaIds(self.areaNames)

         if self.areaIds:
            areaDatas = Area.getFullyInitializedCatObjectList(self.areaIds)
            areaNames = [areeData.getAreaName() for areeData in areaDatas]
            self._appendInfo(argusInfo, 'Area Names', areaNames)

         self._appendInfo(argusInfo, 'Branch Names', self.branchNames)
         self._appendInfo(argusInfo, 'Build Type', self.bldTypes)

      if self.__testerArg:
         self._appendInfo(argusInfo, 'Tester Ids', self.testerIds)

      if self.__wlArg:
         self._appendInfo(argusInfo, 'Workload Names', self.wlNames)

      if self.__wuArg:
         self._appendInfo(argusInfo, 'Workunit Id', self.wuIds)

      if self.__resultArg:
         self._appendInfo(argusInfo, 'Filter result', self.results)

      if self.__testrunArg:
         self._appendInfo(argusInfo, 'Testrun Id', self.testrunIds)

      if self.__limitArg:
         self._appendInfo(argusInfo, 'Limit Day', self.limitDay)
         self._appendInfo(argusInfo, 'Limit Number', self.limitNumber)

      return argusInfo

   def __str__(self):
      """Customized input info which will be used for email body
      """
      formatted_output = formatList2Str(self._argus_info, overallIndex=' : ',
                                        appendIndex=False, title=False)
      return formatted_output


if __name__ == '__main__':
   parser = TestrunFilters(desp='Command Parser test', areaBranch=NEED,
                           testrun=NEED)
   parser.parse_args()
   print("Argu list:\n%s" % parser._initArgumentList())
   print('----------------------------')
   print("User input info:\n%s" % str(parser))
   print('----------------------------')
