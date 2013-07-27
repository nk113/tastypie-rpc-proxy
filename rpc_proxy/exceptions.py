# -*- coding: utf-8 -*-
import logging


logger = logging.getLogger(__name__)


class ProxyException(Exception):

    def __init__(self, message, *args, **kwargs):
        self.errors = kwargs.get('errors', None)

        super(ProxyException, self).__init__(message, *args, **kwargs)
