# -*- coding: utf-8 -*-
import os
import warnings

from .settings import *


# rpc proxy
TASTYPIE_RPC_PROXY = {
    # version
    'APP_VERSION': '0.1.0',
    # pathes
    'APP_ROOT': os.environ.get('APP_ROOT',
                               os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                            '../../../'))),
    'API_NAMESPACE': 'meta',
    'API_URL': 'http://127.0.0.1:8000/api',
    'NON_DEFAULT_ID_FOREIGNKEYS': ('item',),
    'SUPERUSER_USERNAME': 'test',
    'SUPERUSER_PASSWORD': 'test',
}

# django
ROOT_URLCONF = 'urls.urls'
WSGI_APPLICATION = 'wsgi.wsgi.application'


# database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '/dev/shm/proxy.db',
    }
}

# cache
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': 'localhost:11211',
    }
}


# apps
INSTALLED_APPS += (
    'example',
)


# logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': '[%(asctime)s: %(levelname)s: %(name)s: %(funcName)s (%(pathname)s l.%(lineno)d): %(process)d.%(thread)d] %(message)s'
        },
        'normal': {
            'format': '[%(asctime)s: %(levelname)s: %(name)s: %(funcName)s] %(message)s'
        },
        'simple': {
            'format': '[%(asctime)s] %(message)s'
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        }
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'normal',
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ('require_debug_false',),
            'class': 'django.utils.log.AdminEmailHandler',
        },
        'django_log': {
            'level': 'INFO',
            'class': 'logging.handlers.WatchedFileHandler',
            'formatter': 'normal',
            'filename': os.path.join(TASTYPIE_RPC_PROXY['APP_ROOT'], 'logs/django.log'),
        },
        'debug_log': {
            'level': 'DEBUG',
            'class': 'logging.handlers.WatchedFileHandler',
            'formatter': 'verbose',
            'filename': os.path.join(TASTYPIE_RPC_PROXY['APP_ROOT'], 'logs/django-debug.log'),
        },
        'sql_log': {
            'level': 'DEBUG',
            'class': 'logging.handlers.WatchedFileHandler',
            'formatter': 'simple',
            'filename': os.path.join(TASTYPIE_RPC_PROXY['APP_ROOT'], 'logs/django-sql.log'),
        },
        'test_log': {
            'level': 'DEBUG',
            'class': 'logging.handlers.WatchedFileHandler',
            'formatter': 'normal',
            'filename': os.path.join(TASTYPIE_RPC_PROXY['APP_ROOT'], 'logs/django-test.log'),
        },
    },
    'loggers': {
        '': {
            'handlers': ('console',),
            'level': 'DEBUG',
            'propagate': True,
        },
    }
}


# warnings
warnings.filterwarnings(action='ignore',
                        category=UserWarning,
                        module=r'tastypie.*')
warnings.filterwarnings(action='ignore',
                        category=DeprecationWarning,
                        module=r'django.*')
warnings.filterwarnings('error',
                        r'DateTimeField received a naive datetime',
                        RuntimeWarning,
                        r'django\.db\.models\.fields')
