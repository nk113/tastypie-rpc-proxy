# -*- coding: utf-8 -*-
import base64
import inspect
import json
import logging
import requests
import types

from django.conf import settings
from django.core.management import call_command
from django_nose import FastFixtureTestCase
from functools import wraps
from mock import patch
from tastypie.test import ResourceTestCase, TestApiClient 

from rpc_proxy.proxies import get_setting


INITIAL_DATA = ('initial_data',)
TEST_DATA = ('test_data',)

logger = logging.getLogger(__name__)


def mock_request(obj, method, url, **kwargs):
    client = TestApiClient()
    authentication = 'Basic %s' % base64.b64encode(':'.join([
        get_setting('SUPERUSER_USERNAME', None),
        get_setting('SUPERUSER_PASSWORD', None),
    ]))

    if method == 'GET':
        data = kwargs.get('params', {})
        djresponse = client.get(url, data=data, authentication=authentication)
    elif method == 'POST':
        data = json.loads(kwargs.get('data', '{}'))
        djresponse = client.post(url, data=data, authentication=authentication)
    elif method == 'PUT':
        data = json.loads(kwargs.get('data', '{}'))
        djresponse = client.put(url, data=data, authentication=authentication)
    elif method == 'PATCH':
        data = json.loads(kwargs.get('data', '{}'))
        djresponse = client.patch(url, data=data, authentication=authentication)
    elif method == 'DELETE':
        data = kwargs.get('params', {})
        djresponse = client.delete(url, data=data, authentication=authentication)

    # convert django.http.HttpResponse to requests.models.Response
    response = requests.models.Response()
    response.status_code = djresponse.status_code
    response.headers = {}
    try:
        response.headers['content-type'] = djresponse['content-type']
        response.headers['location'] = djresponse['location']
    except:
        pass
    response.encoding = requests.utils.get_encoding_from_headers(response.headers)
    response._content = djresponse.content

    return response

def mock_cache_set(key, value, timeout=None):
    # do nothing
    pass

def mock_api(func, **decorator_kwargs):
    @patch('requests.sessions.Session.request', mock_request)
    @patch('tastypie.cache.SimpleCache.set', mock_cache_set)
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper


class TestCase(FastFixtureTestCase):
    """
    Don't be smart in test cases!
    """
    fixtures = INITIAL_DATA

    def __new__(cls, name):
        testcase = super(TestCase, cls).__new__(cls)

        if get_setting('API_URL', None):
            try:
                func_type = types.UnboundMethodType
            except:
                func_type = types.FunctionType

            for name, func in inspect.getmembers(testcase):
                if isinstance(func, func_type) and name.startswith('test_'):
                    setattr(testcase, name, mock_api(func))

        return testcase

    def setUp(self):
        call_command('loaddata', *TEST_DATA)
        super(TestCase, self).setUp()


class Proxy(TestCase):
    """
    Don't be smart in test cases!

    CAVEAT: Proxy classes have to be imported within each test method
            to mock the requests
    """
    pass
