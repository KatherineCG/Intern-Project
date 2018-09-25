''' CAT related constants
Created on Sep 2, 2016

@author: kaiyuanli
'''
#========================
# CAT Info Constants
#========================
CAT_URL = 'https://cat2.eng.vmware.com'
CAT_AUTH = {'username': 'kaiyuanli',
            'api_key': '801495a070d40ea1d399fe1a24f197717bff3e76'}
CAT_API_URL_BASE = 'http://cat-api.eng.vmware.com'
CAT_PA_RESULT_BASE = 'https://cat.eng.vmware.com'
CAT_WDC_RESULT_BASE = 'https://wdc-prd-cat-services001.eng.vmware.com'
ALREADY_IN_CAT = 'DuplicateValueInFieldWithUniqueConstraint'

RESULT_PASS = 'PASS'
RESULT_FAIL = 'FAIL'
RESULT_INFO = 'INFO'
RESULT_PSOD = 'PSOD'
RESULT_TIMEOUT = "TIMEOUT"
RESULT_INVALID = 'INVALID'
RESULT_INVALID_INFRA = 'INVALID-I'
TESTRUN_RESULTS = [RESULT_PASS, RESULT_FAIL, RESULT_TIMEOUT, RESULT_PSOD,
                   RESULT_INVALID, RESULT_INVALID_INFRA]

NOT_AVAILABLE = 'N/A'
NOT_AVALIABLE = 'N/A' # deprecated, typo variables

