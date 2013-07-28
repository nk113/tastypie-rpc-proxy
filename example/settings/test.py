# -*- coding: utf-8 -*-
from .local import *


# rpc_proxy
del(TASTYPIE_RPC_PROXY['API_URL'])


# apps
INSTALLED_APPS += (
    'django_nose',
)


# logging
LOGGING = {}


# test
TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
NOSE_ARGS = ('--with-fixture-bundling',
             # '--failed',
             # '--stop',
             )
