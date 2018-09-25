#!/build/toolchain/lin64/python-2.7.6/bin/python -u
'''
Created on Apr 28, 2015

Collect a patch of testruns' status
@author: kaiyuanli
'''
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from Common.cat.testrungroup import generateReportByParser, TestrunGroupsByWorkunit
from Common.utils.commandParser import TestrunFilters
from Common.utils.emailUtil import sendEmail
from Common.utils.htmlUtil import getHtmlTitle, getEmailHighLight
from Common.utils.logger import getLogger

logger = getLogger()

if __name__ == '__main__':
   aim = "Collect a patch of testruns' status"
   parser = TestrunFilters(desp=aim)
   parser.parse_args()
   logger.info("User Input Info:\n%s\n", parser)
   group = TestrunGroupsByWorkunit()
   overall_output, detail_output, bug_output, attach_files = generateReportByParser(group,parser)

   if not overall_output and not detail_output:
      sys.exit()
   else:
      parser_info = getEmailHighLight('Testruns are filtered from')
      user_input = '%s:\n%s\n' % (parser_info, str(parser))
      overall_output = "%s\n\n%s" % (getHtmlTitle('Overall Report'), overall_output)
      detail_output = "\n%s\n%s" % (getHtmlTitle('Detail Report'), detail_output)
      email_body = '\n\n'.join([user_input, overall_output, detail_output])
      if bug_output:
         bug_output = "\n\n\n%s\n%s" % (getHtmlTitle('Bug Report'), bug_output)
         email_body += '\n\n'.join([bug_output])
      sendEmail(group.getOverallSummary(), email_body,
                attach_files, parser.emailToList, sender=parser.emailSender)



