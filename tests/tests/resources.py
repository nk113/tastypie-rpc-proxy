# -*- coding: utf-8 -*-
import logging

from datetime import datetime
from django.conf import settings
from tastypie.test import ResourceTestCase

from rpc_proxy.test import TestCase

from apps.test.models import *

API_PATH = '/api/v1'

logger = logging.getLogger(__name__)
proxy_settings = getattr(settings, 'TASTYPIE_RPC_PROXY', object())


class ItemResource(TestCase, ResourceTestCase):

    def setUp(self):
        super(ItemResource, self).setUp()

        self.list_endpoint = '%s/core/item/' % API_PATH
        self.detail_pk = 1
        self.detail_endpoint = '%s%s/' % (self.list_endpoint, self.detail_pk,)
        self.post_data = {
            'ctime': '2013-06-14T01:09:14Z', 
            'item_type': 0,
            'meta_type': 1,
            'parents': [
                '%s/core/item/%s/' % (API_PATH, 1,),
            ], 
            'source_item_id': 't-4@some.service',
            'utime': datetime.now(),
        }

    def get_credentials(self):
        return self.create_basic(username=proxy_settings.get('SUPERUSER_USERNAME', None),
                                 password=proxy_settings.get('SUPERUSER_PASSWORD', None))

    def test_get_list_unauthorzied(self):
        self.assertHttpUnauthorized(
            self.api_client.get(self.list_endpoint))

    def test_get_list_json(self):
        self.assertValidJSONResponse(
            self.api_client.get(self.list_endpoint,
                                format='json',
                                authentication=self.get_credentials()))

    def test_get_detail_unauthenticated(self):
        self.assertHttpUnauthorized(
            self.api_client.get(self.detail_endpoint))

    def test_get_detail_json(self):
        self.assertValidJSONResponse(
            self.api_client.get(self.detail_endpoint,
                                format='json',
                                authentication=self.get_credentials()))

    def test_post_list_unauthenticated(self):
        self.assertHttpUnauthorized(
            self.api_client.post(self.list_endpoint,
                                 format='json',
                                 data=self.post_data))

    def test_post_list(self):
        self.assertEqual(Item.objects.count(), 5)
        self.assertHttpCreated(
            self.api_client.post(self.list_endpoint,
                                 format='json',
                                 data=self.post_data,
                                 authentication=self.get_credentials()))
        self.assertEqual(Item.objects.count(), 6)

    def test_put_detail_unauthenticated(self):
        self.assertHttpUnauthorized(
            self.api_client.put(self.detail_endpoint, 
                                format='json', 
                                data=self.post_data))

    def test_put_detail(self):
        original_data = self.deserialize(
            self.api_client.get(self.detail_endpoint,
                                format='json',
                                authentication=self.get_credentials()))

        new_data = original_data.copy()
        new_data['source_item_id'] = 't-999@some.service'

        self.assertEqual(Item.objects.count(), 5)
        self.assertHttpAccepted(
            self.api_client.put(self.detail_endpoint,
                                format='json',
                                data=new_data,
                                authentication=self.get_credentials()))
        self.assertEqual(Item.objects.count(), 5)
        self.assertEqual(Item.objects.get(pk=self.detail_pk).source_item_id,
                         't-999@some.service')

    def test_delete_detail_unauthenticated(self):
        self.assertHttpUnauthorized(
            self.api_client.delete(self.detail_endpoint,
                                   format='json'))

    def test_delete_detail(self):
        self.assertEqual(Item.objects.count(), 5)
        self.assertHttpAccepted(
            self.api_client.delete(self.detail_endpoint,
                                   format='json',
                                   authentication=self.get_credentials()))
        self.assertEqual(Item.objects.count(), 4)


class TrackResource(TestCase, ResourceTestCase):

    def setUp(self):
        super(TrackResource, self).setUp()

        self.item = Item.objects.get(source_item_id='t-1@some.service')
        self.list_endpoint = '%s/meta/track/' % API_PATH
        self.detail_pk = self.item.pk
        self.detail_endpoint = '%s%s/' % (self.list_endpoint, self.detail_pk,)
        self.post_data = {
            'ctime': '2013-06-14T02:42:57Z',
            'isrc': 'ISRC-TEST-0003',
            'item': '%s/core/item/%s/' % (API_PATH, 5,),
            'length': 240,
            'release_date': '2013-06-14',
            'trial_duration': 45,
            'trial_start_position': 10,
            'utime': datetime.now(),
        }

    def get_credentials(self):
        return self.create_basic(username=proxy_settings.get('SUPERUSER_USERNAME', None),
                                 password=proxy_settings.get('SUPERUSER_PASSWORD', None))

    def test_get_list_unauthorzied(self):
        self.assertHttpUnauthorized(
            self.api_client.get(self.list_endpoint))

    def test_get_list_json(self):
        self.assertValidJSONResponse(
            self.api_client.get(self.list_endpoint,
                                format='json',
                                authentication=self.get_credentials()))

    def test_get_detail_unauthenticated(self):
        self.assertHttpUnauthorized(
            self.api_client.get(self.detail_endpoint))

    def test_get_detail_json(self):
        self.assertValidJSONResponse(
            self.api_client.get(self.detail_endpoint,
                                format='json',
                                authentication=self.get_credentials()))

    def test_post_list_unauthenticated(self):
        self.assertHttpUnauthorized(
            self.api_client.post(self.list_endpoint,
                                 format='json',
                                 data=self.post_data))

    def test_post_list(self):
        self.assertEqual(Track.objects.count(), 2)
        self.assertHttpCreated(
            self.api_client.post(self.list_endpoint,
                                 format='json',
                                 data=self.post_data,
                                 authentication=self.get_credentials()))
        self.assertEqual(Track.objects.count(), 3)

    def test_put_detail_unauthenticated(self):
        self.assertHttpUnauthorized(
            self.api_client.put(self.detail_endpoint, 
                                format='json', 
                                data=self.post_data))

    def test_put_detail(self):
        original_data = self.deserialize(
            self.api_client.get(self.detail_endpoint,
                                format='json',
                                authentication=self.get_credentials()))

        new_data = original_data.copy()
        new_data['isrc'] = 'ISRC-TEST-0001.rev-01'
        new_data['length'] = 600

        self.assertEqual(Track.objects.count(), 2)
        self.assertHttpAccepted(
            self.api_client.put(self.detail_endpoint,
                                format='json',
                                data=new_data,
                                authentication=self.get_credentials()))
        self.assertEqual(Track.objects.count(), 2)
        self.assertEqual(Track.objects.get(pk=self.detail_pk).isrc,
                         'ISRC-TEST-0001.rev-01')
        self.assertEqual(Track.objects.get(pk=self.detail_pk).length,
                         600)

    def test_delete_detail_unauthenticated(self):
        self.assertHttpUnauthorized(
            self.api_client.delete(self.detail_endpoint,
                                   format='json'))

    def test_delete_detail(self):
        self.assertEqual(Track.objects.count(), 2)
        self.assertHttpAccepted(
            self.api_client.delete(self.detail_endpoint,
                                   format='json',
                                   authentication=self.get_credentials()))
        self.assertEqual(Track.objects.count(), 1)


class TrackLocalizationResource(TestCase, ResourceTestCase):

    def setUp(self):
        super(TrackLocalizationResource, self).setUp()

        self.track = Track.objects.get(item__source_item_id='t-1@some.service')
        self.list_endpoint = '%s/meta/tracklocalization/' % API_PATH
        self.detail_pk = 1
        self.detail_endpoint = '%s%s/' % (self.list_endpoint, self.detail_pk,)
        self.post_data = {
            'artist': 'Test',
            'ctime': '2013-06-14T01:09:14Z',
            'description': u'Beschreibung für den Pop-Song 1.',
            'label': 'Label Test',
            'language_code': 'de',
            'title': 'A Pop Song 1',
            'track': '%s/meta/track/%s/' % (API_PATH, 2),
            'utime': datetime.now(),
        }

    def get_credentials(self):
        return self.create_basic(username=proxy_settings.get('SUPERUSER_USERNAME', None),
                                 password=proxy_settings.get('SUPERUSER_PASSWORD', None))

    def test_get_list_unauthorzied(self):
        self.assertHttpUnauthorized(
            self.api_client.get(self.list_endpoint))

    def test_get_list_json(self):
        self.assertValidJSONResponse(
            self.api_client.get(self.list_endpoint,
                                format='json',
                                authentication=self.get_credentials()))

    def test_get_detail_unauthenticated(self):
        self.assertHttpUnauthorized(
            self.api_client.get(self.detail_endpoint))

    def test_get_detail_json(self):
        self.assertValidJSONResponse(
            self.api_client.get(self.detail_endpoint,
                                format='json',
                                authentication=self.get_credentials()))

    def test_post_list_unauthenticated(self):
        self.assertHttpUnauthorized(
            self.api_client.post(self.list_endpoint,
                                 format='json',
                                 data=self.post_data))

    def test_post_list(self):
        self.assertEqual(TrackLocalization.objects.count(), 4)
        self.assertHttpCreated(
            self.api_client.post(self.list_endpoint,
                                 format='json',
                                 data=self.post_data,
                                 authentication=self.get_credentials()))
        self.assertEqual(TrackLocalization.objects.count(), 5)

    def test_put_detail_unauthenticated(self):
        self.assertHttpUnauthorized(
            self.api_client.put(self.detail_endpoint, 
                                format='json', 
                                data=self.post_data))

    def test_put_detail(self):
        original_data = self.deserialize(
            self.api_client.get(self.detail_endpoint,
                                format='json',
                                authentication=self.get_credentials()))

        new_data = original_data.copy()
        new_data['description'] = u'Beschreibung für den Pop-Song 1.'
        new_data['language_code'] = 'de'

        self.assertEqual(TrackLocalization.objects.count(), 4)
        self.assertHttpAccepted(
            self.api_client.put(self.detail_endpoint,
                                format='json',
                                data=new_data,
                                authentication=self.get_credentials()))
        self.assertEqual(TrackLocalization.objects.count(), 4)
        self.assertEqual(TrackLocalization.objects.get(pk=self.detail_pk).description,
                         u'Beschreibung für den Pop-Song 1.')
        self.assertEqual(TrackLocalization.objects.get(pk=self.detail_pk).language_code,
                         'de')
        self.assertEqual(TrackLocalization.objects.get(pk=self.detail_pk).title,
                         'A Pop Song 1')

    def test_delete_detail_unauthenticated(self):
        self.assertHttpUnauthorized(
            self.api_client.delete(self.detail_endpoint,
                                   format='json'))

    def test_delete_detail(self):
        self.assertEqual(TrackLocalization.objects.count(), 4)
        self.assertHttpAccepted(
            self.api_client.delete(self.detail_endpoint,
                                   format='json',
                                   authentication=self.get_credentials()))
        self.assertEqual(TrackLocalization.objects.count(), 3)


class AlbumResource(TestCase, ResourceTestCase):

    def setUp(self):
        super(AlbumResource, self).setUp()

        self.item = Item.objects.get(source_item_id='a-1@some.service')
        self.list_endpoint = '%s/meta/album/' % API_PATH
        self.detail_pk = self.item.pk
        self.detail_endpoint = '%s%s/' % (self.list_endpoint, self.detail_pk,)
        self.post_data = {
            'ctime': '2013-06-14T01:09:14Z', 
            'item': '%s/core/item/%s/' % (API_PATH, 4,),
            'release_date': '2050-12-31', 
            'utime': datetime.now(),
        }

    def get_credentials(self):
        return self.create_basic(username=proxy_settings.get('SUPERUSER_USERNAME', None),
                                 password=proxy_settings.get('SUPERUSER_PASSWORD', None))

    def test_get_list_unauthorzied(self):
        self.assertHttpUnauthorized(
            self.api_client.get(self.list_endpoint))

    def test_get_list_json(self):
        self.assertValidJSONResponse(
            self.api_client.get(self.list_endpoint,
                                format='json',
                                authentication=self.get_credentials()))

    def test_get_detail_unauthenticated(self):
        self.assertHttpUnauthorized(
            self.api_client.get(self.detail_endpoint))

    def test_get_detail_json(self):
        self.assertValidJSONResponse(
            self.api_client.get(self.detail_endpoint,
                                format='json',
                                authentication=self.get_credentials()))

    def test_post_list_unauthenticated(self):
        self.assertHttpUnauthorized(
            self.api_client.post(self.list_endpoint,
                                 format='json',
                                 data=self.post_data))

    def test_post_list(self):
        self.assertEqual(Album.objects.count(), 1)
        self.assertHttpCreated(
            self.api_client.post(self.list_endpoint,
                                 format='json',
                                 data=self.post_data,
                                 authentication=self.get_credentials()))
        self.assertEqual(Album.objects.count(), 2)

    def test_put_detail_unauthenticated(self):
        self.assertHttpUnauthorized(
            self.api_client.put(self.detail_endpoint, 
                                format='json', 
                                data=self.post_data))

    def test_put_detail(self):
        original_data = self.deserialize(
            self.api_client.get(self.detail_endpoint,
                                format='json',
                                authentication=self.get_credentials()))

        new_data = original_data.copy()
        new_data['release_date'] = '2050-12-31'

        self.assertEqual(Album.objects.count(), 1)
        self.assertHttpAccepted(
            self.api_client.put(self.detail_endpoint,
                                format='json',
                                data=new_data,
                                authentication=self.get_credentials()))
        self.assertEqual(Album.objects.count(), 1)
        self.assertEqual(Album.objects.get(pk=self.detail_pk).release_date,
                         datetime(2050, 12, 31).date())

    def test_delete_detail_unauthenticated(self):
        self.assertHttpUnauthorized(
            self.api_client.delete(self.detail_endpoint,
                                   format='json'))

    def test_delete_detail(self):
        self.assertEqual(Album.objects.count(), 1)
        self.assertHttpAccepted(
            self.api_client.delete(self.detail_endpoint,
                                   format='json',
                                   authentication=self.get_credentials()))
        self.assertEqual(Album.objects.count(), 0)


class AlbumLocalizationResource(TestCase, ResourceTestCase):

    def setUp(self):
        super(AlbumLocalizationResource, self).setUp()

        self.album = Album.objects.get(item__source_item_id='a-1@some.service')
        self.list_endpoint = '%s/meta/albumlocalization/' % API_PATH
        self.detail_pk = 1
        self.detail_endpoint = '%s%s/' % (self.list_endpoint, self.detail_pk,)
        self.post_data = {
            'album': '%s/meta/album/%s/' % (API_PATH, 1),
            'artist': 'Test',
            'ctime': '2013-06-14T01:09:14Z',
            'description': u'Beschreibung für den Pop-Song.',
            'label': 'Label Test',
            'language_code': 'de',
            'title': 'A Pop Song Collection',
            'utime': datetime.now(),
        }

    def get_credentials(self):
        return self.create_basic(username=proxy_settings.get('SUPERUSER_USERNAME', None),
                                 password=proxy_settings.get('SUPERUSER_PASSWORD', None))

    def test_get_list_unauthorzied(self):
        self.assertHttpUnauthorized(
            self.api_client.get(self.list_endpoint))

    def test_get_list_json(self):
        self.assertValidJSONResponse(
            self.api_client.get(self.list_endpoint,
                                format='json',
                                authentication=self.get_credentials()))

    def test_get_detail_unauthenticated(self):
        self.assertHttpUnauthorized(
            self.api_client.get(self.detail_endpoint))

    def test_get_detail_json(self):
        self.assertValidJSONResponse(
            self.api_client.get(self.detail_endpoint,
                                format='json',
                                authentication=self.get_credentials()))

    def test_post_list_unauthenticated(self):
        self.assertHttpUnauthorized(
            self.api_client.post(self.list_endpoint,
                                 format='json',
                                 data=self.post_data))

    def test_post_list(self):
        self.assertEqual(AlbumLocalization.objects.count(), 2)
        self.assertHttpCreated(
            self.api_client.post(self.list_endpoint,
                                 format='json',
                                 data=self.post_data,
                                 authentication=self.get_credentials()))
        self.assertEqual(AlbumLocalization.objects.count(), 3)

    def test_put_detail_unauthenticated(self):
        self.assertHttpUnauthorized(
            self.api_client.put(self.detail_endpoint, 
                                format='json', 
                                data=self.post_data))

    def test_put_detail(self):
        original_data = self.deserialize(
            self.api_client.get(self.detail_endpoint,
                                format='json',
                                authentication=self.get_credentials()))

        new_data = original_data.copy()
        new_data['description'] = u'Beschreibung für den Pop-Song.'
        new_data['language_code'] = 'de'

        self.assertEqual(AlbumLocalization.objects.count(), 2)
        self.assertHttpAccepted(
            self.api_client.put(self.detail_endpoint,
                                format='json',
                                data=new_data,
                                authentication=self.get_credentials()))
        self.assertEqual(AlbumLocalization.objects.count(), 2)
        self.assertEqual(AlbumLocalization.objects.get(pk=self.detail_pk).description,
                         u'Beschreibung für den Pop-Song.')
        self.assertEqual(AlbumLocalization.objects.get(pk=self.detail_pk).language_code,
                         'de')
        self.assertEqual(AlbumLocalization.objects.get(pk=self.detail_pk).title,
                         'A Pop Song Collection')

    def test_delete_detail_unauthenticated(self):
        self.assertHttpUnauthorized(
            self.api_client.delete(self.detail_endpoint,
                                   format='json'))

    def test_delete_detail(self):
        self.assertEqual(AlbumLocalization.objects.count(), 2)
        self.assertHttpAccepted(
            self.api_client.delete(self.detail_endpoint,
                                   format='json',
                                   authentication=self.get_credentials()))
        self.assertEqual(AlbumLocalization.objects.count(), 1)
