# -*- coding: utf-8 -*-
import os
import sys


APP_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
# APP_DIR = os.path.abspath(os.path.dirname(__file__))
DJANGO_SETTINGS_MODULE = sys.argv[1] if sys.argv[0] != 'setup.py' and len(sys.argv) > 1 else 'settings.test'

sys.path.insert(0, APP_ROOT)
# sys.path.insert(0, APP_DIR)
os.environ['DJANGO_SETTINGS_MODULE'] = os.environ.get('DJANGO_SETTINGS_MODULE',
                                                      DJANGO_SETTINGS_MODULE)

from django.conf import settings
from django.test.utils import get_runner

def runtests():
    runner = get_runner(settings)(verbosity=1, interactive=True)
    sys.exit(bool(runner.run_tests(('tests',))))

if __name__ == '__main__':
    runtests()
