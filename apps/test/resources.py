# -*- coding: utf-8 -*-
import logging

from django.utils.importlib import import_module
from tastypie import fields
from tastypie.http import HttpForbidden
from tastypie.resources import ALL, ALL_WITH_RELATIONS

from apps.test import models
from rpc_proxy import resources


logger = logging.getLogger(__name__)


class Item(resources.ModelResource):

    class Meta(resources.SuperuserMeta):

        queryset = models.Item.objects.all()
        resource_name = 'item'
        filtering = {
            'children': ALL_WITH_RELATIONS,
            'parents' : ALL_WITH_RELATIONS,
            'source_item_id': ('exact', 'startswith',)
        }

    parents = fields.ToManyField('apps.test.resources.Item', 'parents', null=True)
    children = fields.ToManyField('apps.test.resources.Item', 'children', null=True)
    # album = fields.OneToOneField('apps.test.resources.Album', 'album', null=True)
    # track = fields.OneToOneField('apps.test.resources.Track', 'track', null=True)


class Album(resources.ModelResource):

    class Meta(resources.SuperuserMeta):

        queryset = models.Album.objects.all()
        resource_name = 'album'
        filtering = {
            'item': ALL_WITH_RELATIONS,
        }
        ordering = ('item',)

    item = fields.ForeignKey(Item, 'item')
    release_date = fields.DateField('release_date')


class AlbumLocalization(resources.ModelResource):

    class Meta(resources.SuperuserMeta):

        queryset = models.AlbumLocalization.objects.all()
        resource_name = 'albumlocalization'
        filtering = {
            'album': ALL_WITH_RELATIONS,
            'language_code': ('exact', 'in',),
            'title': ('exact', 'in', 'startswith',),
        }

    album = fields.ForeignKey(Album, 'album')


class Track(resources.ModelResource):

    class Meta(resources.SuperuserMeta):

        queryset = models.Track.objects.all()
        resource_name = 'track'
        filtering = {
            'item': ALL_WITH_RELATIONS,
        }
        ordering = ('item',)

    item = fields.ForeignKey(Item, 'item')
    release_date = fields.DateField('release_date')


class TrackLocalization(resources.ModelResource):

    class Meta(resources.SuperuserMeta):

        queryset = models.TrackLocalization.objects.all()
        resource_name = 'tracklocalization'
        filtering = {
            'language_code': ('exact', 'in',),
            'title': ('exact', 'in', 'startswith',),
            'track': ALL_WITH_RELATIONS,
        }

    track = fields.ForeignKey(Track, 'track')
