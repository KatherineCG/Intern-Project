''' Config info for testesx log parser / analyzer
Created on Aug 31, 2016

@author: kaiyuanli
'''

#=======================
# Internally Constants
#=======================
NOT_AVAILABLE = 'N/A'
NIMBUS_KEY = 'nimbus'
NIMBUS_ESX = 'nimbus-esx'

#=======================
# Log Location Constants
#=======================
TESTESX_DIR = 'testesx/'
TESTESX_LOG = 'testesx.log'


#=======================
# Log Format Constants
#=======================

# Sample: Jun 09 13:36:43
TESTESX_TIMESTAMP_DEPRECATED_RE = '\w+\s\d+\s\d+:\d+:\d+'
TESTESX_TIMESTAMP_DEPRECATED = '%b %d %H:%M:%S'

# Sample: 2017-09-03T22:45:55.098Z
TESTESX_TIMESTAMP_RE = '\d+-\d+-\d+T\d+:\d+:\d+.\d+Z'
TESTESX_TIMESTAMP = '%Y-%m-%dT%H:%M:%S'

# Sample: Jun 09 13:36:43
VMKERNEL_TIMESTAMP_RE = '\d+-\d+-\d+T\d+:\d+:\d+\.\d+Z'

# Sample; 0:00:01:03.889
VMKBOOT_TIMESTAMP_RE = '\d\:\d+\:\d+\:\d+\.\d+'

# Sample: 2016-08-31T08:50:31.610Z cpu28:1001390163)
VMKERNEL_LOG_FORMAT_RE = '%s\scpu\d+\:\d+\)' % (VMKERNEL_TIMESTAMP_RE)
VMKERNEL_LOG_WITH_MATCH_TS_FORMAT_RE = '(%s)\scpu\d+\:\d+\)' % (VMKERNEL_TIMESTAMP_RE)

# Sample: 0:00:01:03.889 cpu27:1002438583
VMKBOOT_LOG_FORMAT_RE = '%s\scpu\d+\:\d+\)' % (VMKBOOT_TIMESTAMP_RE)

#=======================
# Log Level Constants
#=======================
LEVEL_CONNECTIONLOST = 'CONNECTION_LOST'
LEVEL_DISABLED = 'DISABLED'
LEVEL_ERROR = 'ERROR'
LEVEL_FAIL = 'FAILED'
LEVEL_FAIL_COLLECT_VMSUPPORT = 'FAILED_COLLECT_VM_SUPPORT'
LEVEL_INFO = 'INFO'
LEVEL_INFRA = 'INFRA_ISSUE'
LEVEL_INFRA_BOOT_TIMEOUT = 'INFRA_ISSUE_BOOT_TIMEOUT'
LEVEL_INFRA_IPMI = 'INFRA_ISSUE_IPMI'
LEVEL_INFRA_NIMBUS = 'INFRA_ISSUE_NIMBUS'
LEVEL_INFRA_PXE = 'INFRA_ISSUE_PXE'
LEVEL_INFRA_TELNET = 'INFRA_ISSUE_TELNET'
LEVEL_INFRA_TESTESX = 'INFRA_ISSUE_TESTESX'
LEVEL_PASS = 'PASSED'
LEVEL_PSOD = 'PSOD'
LEVEL_SKIPPED = 'SKIPPED'
LEVEL_TIMEOUT = 'TIMEOUT'
LEVEL_UWCOREDUMP = 'UW_COREDUMP'
LEVEL_WARNING = 'WARNING'
LEVEL_POSITIVE_LIST = [LEVEL_DISABLED, LEVEL_PASS, LEVEL_SKIPPED, LEVEL_WARNING]
LEVEL_SCRIPT_LIST = [LEVEL_DISABLED, LEVEL_FAIL, LEVEL_PASS, LEVEL_SKIPPED,
                     LEVEL_TIMEOUT, LEVEL_CONNECTIONLOST]

# Level priority from low to high
LEVEL_PRIORITY = [# Benign log level / test result
                  LEVEL_DISABLED, LEVEL_SKIPPED, LEVEL_INFO, LEVEL_PASS,
                  LEVEL_WARNING,

                  # Infra related error
                  LEVEL_INFRA, LEVEL_INFRA_BOOT_TIMEOUT, LEVEL_INFRA_IPMI,
                  LEVEL_INFRA_PXE, LEVEL_INFRA_NIMBUS, LEVEL_INFRA_TELNET,
                  LEVEL_INFRA_TESTESX,

                  # Abnormal result
                  LEVEL_TIMEOUT, LEVEL_ERROR, LEVEL_CONNECTIONLOST,
                  LEVEL_FAIL_COLLECT_VMSUPPORT, LEVEL_FAIL,
                  LEVEL_UWCOREDUMP, LEVEL_PSOD]

#=================================
# TestScript Log Related Constants
#=================================
IGNORE_LIST = ["#BUGREPORT:LOGFILE"]
