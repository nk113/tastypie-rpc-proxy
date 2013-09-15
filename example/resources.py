# -*- coding: utf-8 -*-
import logging

from django.contrib.auth.models import User
from django.utils.importlib import import_module
from tastypie import fields
from tastypie.authentication import BasicAuthentication
from tastypie.authorization import DjangoAuthorization
from tastypie.http import HttpForbidden
from tastypie.resources import ALL, ALL_WITH_RELATIONS
from tastypie.cache import SimpleCache
from tastypie.throttle import CacheThrottle

from example import models
from rpc_proxy import resources


logger = logging.getLogger(__name__)


class Throttle(CacheThrottle):

    def should_be_throttled(self, identifier, **kwargs):
        try:
            user = User.objects.get(username=identifier)
            if user.is_superuser:
                return False
        except User.DoesNotExist, e:
            pass

        return super(Throttle, self).should_be_throttled(identifier,
                                                         **kwargs)


class BaseMeta(object):

    allowed_methods = ('get',)
    authentication = BasicAuthentication()
    authorization = DjangoAuthorization()
    cache = SimpleCache()
    ordering = ('id',)
    throttle = Throttle()


class Item(resources.ModelResource):

    class Meta(BaseMeta):

        queryset = models.Item.objects.all()
        resource_name = 'item'
        filtering = {
            'children': ALL_WITH_RELATIONS,
            'parents' : ALL_WITH_RELATIONS,
            'source_item_id': ('exact', 'startswith',)
        }

    parents = fields.ToManyField('example.resources.Item', 'parents', null=True)
    children = fields.ToManyField('example.resources.Item', 'children', null=True)
    # album = fields.OneToOneField('example.resources.Album', 'album', null=True)
    # track = fields.OneToOneField('example.resources.Track', 'track', null=True)


class Album(resources.ModelResource):

    class Meta(BaseMeta):

        queryset = models.Album.objects.all()
        resource_name = 'album'
        filtering = {
            'item': ALL_WITH_RELATIONS,
        }
        ordering = ('item',)

    item = fields.ForeignKey(Item, 'item')
    release_date = fields.DateField('release_date')


class AlbumLocalization(resources.ModelResource):

    class Meta(BaseMeta):

        queryset = models.AlbumLocalization.objects.all()
        resource_name = 'albumlocalization'
        filtering = {
            'album': ALL_WITH_RELATIONS,
            'language_code': ('exact', 'in',),
            'title': ('exact', 'in', 'startswith',),
        }

    album = fields.ForeignKey(Album, 'album')


class Track(resources.ModelResource):

    class Meta(BaseMeta):

        queryset = models.Track.objects.all()
        resource_name = 'track'
        filtering = {
            'item': ALL_WITH_RELATIONS,
        }
        ordering = ('item',)

    item = fields.ForeignKey(Item, 'item')
    release_date = fields.DateField('release_date')


class TrackLocalization(resources.ModelResource):

    class Meta(BaseMeta):

        queryset = models.TrackLocalization.objects.all()
        resource_name = 'tracklocalization'
        filtering = {
            'language_code': ('exact', 'in',),
            'title': ('exact', 'in', 'startswith',),
            'track': ALL_WITH_RELATIONS,
        }

    track = fields.ForeignKey(Track, 'track')
