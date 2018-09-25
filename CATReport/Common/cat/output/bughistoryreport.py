''' CAT 'build' library
Created on Oct 20, 2016

@author: zhengy
'''
import os
import sys
import json
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../'))

from Common.utils.htmlUtil import *
from Common.cat.object.catdata import CatData
from Common.cat.object.build import Build
from Common.cat.testrungroup import TestrunGroupsByWorkunit
from Common.cat.object.workunit import Workunit
from Common.cat.object.deliverable import Deliverable
from Common.cat.object.testrun import Testrun
from bug.bzlib import getBugSummary

def generateTableWithProperties(tableItems):
   table_content = '<TABLE border=1 cellspacing=0 bordercolorlight=#333333>\n'
   for i in range(len(tableItems)):
      row_content = '<TR>\n'
      for item in tableItems[i]:
          if type(item) is dict:
             if item.get("property"):
                row_content += "<td %s>%s</td>\n" % (item.get("property"),
                                                item.get("value"))
             else:
                row_content += "<td> %s </td>\n" % item.get("value")
          else:
             row_content += "<td> %s </td>\n" % item
      row_content += '</TR>\n'
      table_content += row_content
   table_content += "</TABLE>"
   return table_content

def genrateBugHistoryHtmlReport(limitDays, areaId, branchName,
                                bugzilla_username, bugzilla_password):
   table_header = ["BugID", "Creation Date", "Status",
                   "Reporter", "Assigned To", "Category", "Summary"]
   bug_list = []
   trGroup = TestrunGroupsByWorkunit()
   trGroup.retrieveTestruns(limitDays, 100 * limitDays, areaIds=[areaId], branchNames=branchName)
   if not trGroup.validTestrunsGroup():
       print("No testrun found from area (id=%s)" % areaId)
   testruns = trGroup.getTestruns()
   for testrun in testruns:
      for bug in testrun.getBugDatas():
         bug_list.append(bug.get("number"))

   bug_history = list(set(bug_list))
   production_table = [table_header]
   vdnet_table = [table_header]
   production_bug_table = boldMsg("Production Open Bug(s):")
   vdnet_bug_table = boldMsg("VDNet Open Bug(s):")
   total_bugs = len(bug_history)
   fix_bugs = production_bugs = vdnet_bugs = 0
   for bug in bug_history:
      bug_summary = getBugSummary(bug, bugzilla_username, bugzilla_password)
      if bug_summary.get('Status') in ['resolved', 'closed']:
         fix_bugs += 1
         continue
      buglinkrul = "https://bugzilla.eng.vmware.com/show_bug.cgi?id=%s" % bug
      table_data = [genHyperLink(bug, buglinkrul)]
      for column in table_header[1:]:
          table_data.append(bug_summary.get(column))
      if bug_summary.get('Category') == 'VDNet':
         vdnet_bugs += 1
         vdnet_table.append(table_data)
      else:
         production_bugs += 1
         production_table.append(table_data)

   vdnet_bug_table += tableMsg(vdnet_table)
   production_bug_table += tableMsg(production_table)
   report_summary = "Within the last %s day(s), %s bug(s) triaged, " % (limitDays, total_bugs)
   report_summary += "%s bug(s) resloved/closed, " % fix_bugs
   report_summary += "%s production bug(s) still not resolved, " % production_bugs
   report_summary += "%s vdnet bug(s) not resolved." % (vdnet_bugs)
   report_content = boldMsg(colorMsg(report_summary, "green")) + addLineBreak()
   if production_bugs > 0:
      report_content += production_bug_table
   if vdnet_bugs > 0:
      report_content += vdnet_bug_table
   return generateHtmlReport(report_content)

def generateBuildSummaryHtmlReport(areaId):
   workloads = []
   table_content = []
   table_header1 = []
   table_header2 = []
   workunits = Workunit.QueryEnabledWorkunitInArea(areaId)
   table_header1.append({"property": "rowspan='2'", "value": "Build"})
   for workunit in workunits:
      workunit.initReadableInfo()
      workload_name = workunit.getWorkloadName()
      workloads.append(workload_name)
      workload_link = ("https://cat2.eng.vmware.com/#/workload/%s/info" %
                       workunit.getWorkloadId())
      table_header1.append({"property": "colspan='2'",
                            "value": genHyperLink(workload_name,
                                                  workload_link)})

   table_content.append(table_header1)
   for workload in workloads:
      table_header2.extend(["Passed/Total(Passrate)", "TriageInfo"])
   table_content.append(table_header2)

   buildDatas =  Build.getBuildsByProductionInfo('nsx', 'nsx-equinox', 'beta')
   output = []
   for buildData in buildDatas:
      table_data = []
      deliverable_objs = []
      build_dict = {}
      testruns_dict = []
      build_id = buildData.getId()
      build_dict["build"] = build_id
      deliverable_obj = Deliverable.getDeliverablesByBuild(build_id)[0]
      nsx_build = deliverable_obj.getValueFromCatObj("sbbuildid")
      print("Current nsx sandbox build id is : %s" % nsx_build)
      build_link = "https://buildweb.eng.vmware.com/ob/%s" % nsx_build
      table_data.append(genHyperLink(nsx_build, build_link))
      deliverable_objs.extend(Deliverable.getDeliverablesByBuild(build_id))
      try:
          testruns = Testrun.queryTestrunsByDeliverableObjects(deliverable_objs, areaId)
      except Exception, e:
          continue
      print("There %s testruns whith build %s" % (len(testruns), build_id))
      for testrun in testruns:
         testrun_details = {}
         testrun.initReadableInfo()
         testrun_details["id"] = testrun.getId()
         workload_name = testrun.getWorkloadData().getWorkloadName()
         testrun_details["workload_name"] = workload_name
         testrun_result = testrun.getResult();
         testrun_details["result"] = testrun_result
         triage_info = testrun.getTriageInfo()
         total_cases = testrun.getTotalTestNum()
         testrun_details["total"] = total_cases
         passed_cases = testrun.getPassedTestNum()
         testrun_details["passed"] = passed_cases
         print("Workoad %s summary %s/%s" % (workload_name, passed_cases, total_cases) )
         build_dict[workload_name] = testrun_details
      for workload in workloads:
         testrun_info = build_dict.get(workload)
         if testrun_info:
            if testrun_info.get("total") == 0:
               test_summary = "No run"
            else:
               pass_rate = (testrun_info.get("passed") * 100 /
                            testrun_info.get("total"))
               test_summary = "%s/%s(%s%%)" % (testrun_info.get("passed"),
                                               testrun_info.get("total"),
                                               pass_rate)
            testrun_link = ("https://cat2.eng.vmware.com/#/testrun/%s/results" %
                            testrun_info.get("id"))
            table_data.append(genHyperLink(test_summary, testrun_link))
            table_data.append(triage_info)
         else:
            table_data.extend(["", ""])
      table_content.append(table_data)
   return generateHtmlReport(generateTableWithProperties(table_content))
 
if __name__ == '__main__':
   print '-------------------------------'
   print 'Test get Build info by CLN     '
   print '-------------------------------'
   content = genrateBugHistoryHtmlReport(7, 14721, 'nsx-eclipse', 'svc.nsxujo', 'SLSW85wFukn5b9.@..^')
   print(content)
   with open('bugreport.html', 'w') as f:
       f.write(content)
   bug_list = []
   exit()
   with open('report.html', 'w') as f:
      f.write(generateBuildSummaryHtmlReport(19658))
   exit()
