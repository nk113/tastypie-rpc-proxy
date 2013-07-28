# -*- coding: utf-8 -*-
import logging

from django.conf import settings
from django.utils.importlib import import_module

from rpc_proxy import exceptions
from rpc_proxy import proxies

from apps.test.models import ITEM_TYPES, META_TYPES


logger = logging.getLogger(__name__)


def get_default_language_code():
    return getattr(settings, 'LANGUAGE_CODE', 'en-US').split('-')[0].lower()


class Localizable(proxies.Proxy):

    class Meta:

        abstract = True

    def __init_proxy__(self):
        super(Localizable, self).__init_proxy__()

        setattr(self, 'localization', getattr(import_module(self.__module__),
                                              '%sLocalization' % self.__class__.__name__))

    @property
    def localizations(self):
        return self.localization.objects.filter(**{
            self.__class__.__name__.lower(): self,
        })

    def localize(self, language_code=None):
        self.__init_proxy__()

        language_code = language_code if language_code else get_default_language_code()
        localizations = self.localizations.filter(language_code=language_code)

        if len(localizations) < 1:

            class EmptyLocalization(object):

                def __init__(self, *args, **kwargs):
                    for key in kwargs:
                        setattr(self, key, kwargs[key])

                def __getattr__(self, name):
                    try:
                        return super(EmptyLocalization,
                                     self).__getattr__(name)
                    except AttributeError, e:
                        return None

            localizations = (EmptyLocalization(language_code=language_code),)

        return localizations[0]


class Localization(proxies.Proxy):

    class Meta:

        abstract = True


class Item(proxies.Proxy):

    class Meta:

        namespace = 'core'

    @property
    def item_type_display(self):
        if 'get_item_type_display' in dir(self):
            return self.get_item_type_display()

        return ITEM_TYPES[self.item_type][1]

    @property
    def meta_type_display(self):
        if 'get_meta_type_display' in dir(self):
            return self.get_meta_type_display()

        return META_TYPES[self.meta_type][1]

    @property
    def metadata(self):
        try:
            meta = getattr(import_module(self.__module__),
                           self.meta_type_display)
        except Exception, e:
            logger.exception(e)
            raise exceptions.ProxyException(_('No metadata model for '
                                              '%s found.' % self.meta_type_display))

        return meta.objects.get(item=self)


class Album(Localizable):

    pass


class AlbumLocalization(Localization):

    pass


class Track(Localizable):

    pass


class TrackLocalization(Localization):

    pass
