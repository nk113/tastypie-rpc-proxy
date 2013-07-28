# -*- coding: utf-8 -*-
import logging

from datetime import date
from django.conf import settings
from django.db import models


ITEM_TYPES = ((0, 'Digital'),)
META_TYPES = ((0, 'Track',), (1, 'Album',),)

logger = logging.getLogger(__name__)


class Model(models.Model):

    class Meta:

        abstract = True

    ctime = models.DateTimeField(auto_now_add=True)
    utime = models.DateTimeField(auto_now=True)


class Localizable(Model):

    class Meta:

        abstract = True


class Localization(Model):

    class Meta:

        abstract = True

    language_code = models.CharField(max_length=2, choices=getattr(settings, 'LANGUAGES'), blank=False, null=False)


class Item(Model):

    item_type = models.SmallIntegerField(choices=ITEM_TYPES, default=0)
    meta_type = models.SmallIntegerField(choices=META_TYPES, default=0)
    parents = models.ManyToManyField('self', symmetrical=False, related_name='children', blank=True, null=True)
    source_item_id = models.CharField(max_length=64, unique=True)


class Metadata(models.Model):

    class Meta:

        abstract = True

    item = models.OneToOneField(Item, primary_key=True)


class MetadataLocalizable(Metadata, Localizable):

    class Meta:

        abstract = True


class MetadataLocalization(Localization):

    class Meta:

        abstract = True


class BasicLocalizable(MetadataLocalizable):

    class Meta:

        abstract = True

    release_date = models.DateField(default=date.today)

    def __unicode__(self):
        return '%s' % self.item


class RecordingLocalizable(models.Model):

    class Meta:

        abstract = True

    isrc = models.CharField(max_length=20, blank=True, null=False)
    length = models.IntegerField(default=0)
    trial_start_position = models.IntegerField(default=0, blank=True, null=False)
    trial_duration = models.IntegerField(default=45, blank=True, null=False)


class BasicLocalization(MetadataLocalization):

    class Meta:

        abstract = True

    title = models.CharField(max_length=255, blank=True, null=False)
    description = models.TextField(blank=True, null=False)

    def __unicode__(self):
        return '(%s): %s' % (self.language_code,
                             self.title,)


class MusicLocalization(models.Model):

    class Meta:

        abstract = True

    artist = models.CharField(max_length=255, blank=True, null=False)
    label = models.CharField(max_length=255, blank=True, null=False)


class Album(BasicLocalizable):

    pass


class AlbumLocalization(BasicLocalization, MusicLocalization):

    album = models.ForeignKey(Album)


class Track(BasicLocalizable, RecordingLocalizable):

    pass


class TrackLocalization(BasicLocalization, MusicLocalization):

    track = models.ForeignKey(Track)
