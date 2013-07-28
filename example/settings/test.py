# -*- coding: utf-8 -*-
from .local import *


# rpc_proxy
del(TASTYPIE_RPC_PROXY['API_URL'])


# apps
INSTALLED_APPS += (
    'django_nose',
)


# logging
# LOGGING = {}
LOGGING['loggers'] = {
    '': {
        'handlers': ('test_log',),
        'level': 'CRITICAL',
        'propagate': True,
    },
}


# test
TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
NOSE_ARGS = ('--with-fixture-bundling',
             # '--failed',
             # '--stop',
             )
