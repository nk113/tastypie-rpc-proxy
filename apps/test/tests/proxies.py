# -*- coding: utf-8 -*-
import logging

from datetime import datetime
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from queryset_client import client

from rpc_proxy import exceptions, test
from rpc_proxy.proxies import get_setting


logger = logging.getLogger(__name__)


class ItemProxy(test.Proxy):

    def test_get(self):
        from apps.test.proxies import Item

        self.assertEqual(Item.objects.get(source_item_id='t-1@some.service').source_item_id,
                         't-1@some.service')
        self.assertRaises((client.ObjectDoesNotExist, ObjectDoesNotExist),
                          lambda: Item.objects.get(source_item_id='a-999@some.service'))

    def test_filter(self):
        from apps.test.proxies import Item

        self.assertEqual(Item.objects.filter(source_item_id__startswith='t-').count(),
                         3)

    def test_save(self):
        from apps.test.proxies import Item

        self.assertRaises((client.ObjectDoesNotExist, ObjectDoesNotExist),
                          lambda: Item.objects.get(source_item_id='a-999@some.service'))

        i = Item.objects.get(source_item_id='a-1@some.service')
        i.source_item_id = 'a-999@some.service'
        i.save()

        self.assertEqual(Item.objects.get(source_item_id='a-999@some.service').source_item_id,
                         'a-999@some.service')

    def test_save(self):
        from apps.test.proxies import Item

        self.assertRaises((client.ObjectDoesNotExist, ObjectDoesNotExist),
                          lambda: Item.objects.get(source_item_id='a-999@some.service'))

        i = Item.objects.get(source_item_id='a-1@some.service')
        i.source_item_id = 'a-999@some.service'
        i.save()

        self.assertEqual(Item.objects.get(source_item_id='a-999@some.service').source_item_id,
                         'a-999@some.service')

    def test_create(self):
        from apps.test.proxies import Item

        self.assertEqual(Item.objects.count(),
                         5)

        Item.objects.create(source_item_id='t-999@some.service',
                            item_type=0,
                            meta_type=0)

        self.assertEqual(Item.objects.count(),
                         6)
        self.assertEqual(Item.objects.latest('id').source_item_id, 't-999@some.service')

    def test_parents_add(self):
        from apps.test.proxies import Item

        child = Item.objects.get(source_item_id='t-1@some.service')

        self.assertEqual(child.parents.count(), 1)

        new_child = Item.objects.create(source_item_id='a-999@some.service',
                                        item_type=0,
                                        meta_type=0)

        child.parents.add(new_child)
        child.save()

        parents = Item.objects.get(source_item_id='t-1@some.service').parents.all()

        self.assertEqual(parents.count(), 2)
        self.assertEqual(parents[0].meta_type_display, 'Album')

    def test_parents_remove(self):
        from apps.test.proxies import Item

        child = Item.objects.get(source_item_id='t-1@some.service')

        self.assertEqual(child.parents.count(), 1)

        child.parents.remove(child.parents.all()[0])
        child.save()

        parents = Item.objects.get(source_item_id='t-1@some.service').parents.all()

        self.assertEqual(parents.count(), 0)

    def test_parents_clear(self):
        from apps.test.proxies import Item

        child = Item.objects.get(source_item_id='t-1@some.service')

        self.assertEqual(child.parents.count(), 1)

        child.parents.clear()
        child.save()

        self.assertEqual(child.parents.count(), 0)

    def test_children(self):
        from apps.test.proxies import Item

        parent = Item.objects.get(source_item_id='a-1@some.service')
        children = parent.children.all()

        self.assertEqual(children.count(), 3)
        self.assertEqual(children[0].meta_type_display, 'Track')

    def test_children_add(self):
        from apps.test.proxies import Item

        parent = Item.objects.get(source_item_id='a-1@some.service')

        self.assertEqual(parent.children.count(), 3)

        new_parent = Item.objects.create(source_item_id='t-999@some.service',
                                        item_type=0,
                                        meta_type=0)

        parent.children.add(new_parent)
        parent.save()     

        children = Item.objects.get(source_item_id='a-1@some.service').children.all()
        self.assertEqual(children.count(), 4)
        self.assertEqual(children.latest('id').source_item_id, 't-999@some.service')

    def test_children_remove(self):
        from apps.test.proxies import Item

        parent = Item.objects.get(source_item_id='a-1@some.service')

        self.assertEqual(parent.children.count(), 3)

        parent.children.remove(parent.children.all()[0])
        parent.save()

        children = Item.objects.get(source_item_id='a-1@some.service').children.all()

        self.assertEqual(children.count(), 2)

    def test_children_clear(self):
        from apps.test.proxies import Item

        parent = Item.objects.get(source_item_id='a-1@some.service')

        self.assertEqual(parent.children.count(), 3)

        parent.children.clear()
        parent.save()

        self.assertEqual(parent.children.count(), 0)

    def test_item_type_display(self):
        from apps.test.proxies import Item

        self.assertEqual(Item.objects.get(source_item_id='a-1@some.service').item_type_display,
                         'Digital')

        self.assertEqual(Item.objects.get(source_item_id='t-1@some.service').item_type_display,
                         'Digital')

    def test_meta_type_display(self):
        from apps.test.proxies import Item

        self.assertEqual(Item.objects.get(source_item_id='a-1@some.service').meta_type_display,
                         'Album')
        self.assertEqual(Item.objects.get(source_item_id='t-1@some.service').meta_type_display,
                         'Track')

    def test_metadata(self):
        from apps.test.proxies import Item

        self.assertEqual(Item.objects.get(source_item_id='a-1@some.service').metadata.__class__.__name__,
                         'Album')
        self.assertEqual(Item.objects.get(source_item_id='t-1@some.service').metadata.__class__.__name__,
                         'Track')


class AlbumProxy(test.Proxy):

    def test_get(self):
        from apps.test.proxies import Album

        self.assertEqual(Album.objects.get(item__source_item_id='a-1@some.service').release_date,
                         datetime(2013, 6, 14).date())
        self.assertRaises((client.ObjectDoesNotExist, ObjectDoesNotExist),
                          lambda: Album.objects.get(item__source_item_id='a-999@some.service'))

    def test_filter(self):
        from apps.test.proxies import Album

        self.assertEqual(Album.objects.filter(item__source_item_id__startswith='a-').count(),
                         1)

    def test_save(self):
        from apps.test.proxies import Album

        release_date = datetime(2099, 9, 9).date()

        self.assertEqual(Album.objects.get(item__source_item_id='a-1@some.service').release_date,
                         datetime(2013, 6, 14).date())

        a = Album.objects.get(item__source_item_id='a-1@some.service')
        a.release_date = release_date
        a.save()

        self.assertEqual(Album.objects.get(item__source_item_id='a-1@some.service').release_date,
                         release_date)

    def test_create(self):
        from apps.test.proxies import Album, Item

        self.assertEqual(Album.objects.count(),
                         1)

        item = Item.objects.get(source_item_id='a-2@some.service')
        Album.objects.create(item=item,
                             release_date=datetime.now().date())

        self.assertEqual(Album.objects.count(),
                         2)
        self.assertEqual(Album.objects.latest('item').item.source_item_id, 'a-2@some.service')

    def test_localize(self):
        from apps.test.proxies import Album

        a = Album.objects.get(item__source_item_id__startswith='a-1@some.service')

        en = a.localize()
        self.assertEqual(en.language_code, 'en')
        self.assertEqual(en.title, 'A Pop Song Collection')

        ja = a.localize('ja')
        self.assertEqual(ja.language_code, 'ja')
        self.assertEqual(ja.title, u'ポップ・ソング集')

    def test_localization_add(self):
        from apps.test.proxies import Album

        a = Album.objects.get(item__source_item_id__startswith='a-1@some.service')

        self.assertEqual(a.localizations.count(), 2)

        new_data = a.localize('en').data.copy()
        del(new_data['id'])
        new_data['description'] = u'Beschreibung für den Pop-Song.'
        new_data['language_code'] = 'de'

        a.localization.objects.create(**new_data)

        self.assertEqual(a.localizations.count(), 3)
        self.assertEqual(a.localizations.latest('id').description, u'Beschreibung für den Pop-Song.')

    def test_localization_remove(self):
        from apps.test.proxies import Album

        a = Album.objects.get(item__source_item_id__startswith='a-1@some.service')

        self.assertEqual(a.localizations.count(), 2)

        a.localize('ja').delete()

        self.assertEqual(a.localizations.count(), 1)

    def test_album_track_relation(self):
        from apps.test.proxies import Album, Track

        a = Album.objects.get(item__source_item_id__startswith='a-1@some.service')

        self.assertEqual(a.item.children.count(), 3)
        self.assertEqual(Track.objects.count(), 2)

        a.item.children.filter(source_item_id__startswith='t-1')[0].delete()

        self.assertEqual(a.item.children.count(), 2)
        self.assertEqual(Track.objects.count(), 1)
        

class TrackProxy(test.Proxy):

    def test_get(self):
        from apps.test.proxies import Track

        self.assertEqual(Track.objects.get(item__source_item_id='t-1@some.service').release_date,
                         datetime(2013, 6, 14).date())
        self.assertRaises((client.ObjectDoesNotExist, ObjectDoesNotExist),
                          lambda: Track.objects.get(item__source_item_id='t-999@some.service'))

    def test_filter(self):
        from apps.test.proxies import Track

        self.assertEqual(Track.objects.filter(item__source_item_id__startswith='t-').count(),
                         2)

    def test_save(self):
        from apps.test.proxies import Track

        release_date = datetime(2099, 9, 9).date()

        self.assertEqual(Track.objects.get(item__source_item_id='t-1@some.service').release_date,
                         datetime(2013, 6, 14).date())

        t = Track.objects.get(item__source_item_id='t-1@some.service')
        t.release_date = release_date
        t.save()

        self.assertEqual(Track.objects.get(item__source_item_id='t-1@some.service').release_date,
                         release_date)

    def test_create(self):
        from apps.test.proxies import Track, Item

        self.assertEqual(Track.objects.count(),
                         2)

        item = Item.objects.get(source_item_id='t-3@some.service')
        Track.objects.create(item=item,
                             release_date=datetime.now().date())

        self.assertEqual(Track.objects.count(),
                         3)
        self.assertEqual(Track.objects.latest('item').item.source_item_id, 't-3@some.service')

    def test_localize(self):
        from apps.test.proxies import Track

        t = Track.objects.get(item__source_item_id__startswith='t-1@some.service')

        en = t.localize()
        self.assertEqual(en.language_code, 'en')
        self.assertEqual(en.title, 'A Pop Song 1')

        ja = t.localize('ja')
        self.assertEqual(ja.language_code, 'ja')
        self.assertEqual(ja.title, u'ポップ・ソング 1')

    def test_localization_add(self):
        from apps.test.proxies import Track

        t = Track.objects.get(item__source_item_id__startswith='t-1@some.service')

        self.assertEqual(t.localizations.count(), 2)

        new_data = t.localize('en').data.copy()
        del(new_data['id'])
        new_data['description'] = u'Beschreibung für den Pop-Song 1.'
        new_data['language_code'] = 'de'

        t.localization.objects.create(**new_data)

        self.assertEqual(t.localizations.count(), 3)
        self.assertEqual(t.localizations.latest('id').description, u'Beschreibung für den Pop-Song 1.')

    def test_localization_remove(self):
        from apps.test.proxies import Track

        t = Track.objects.get(item__source_item_id__startswith='t-1@some.service')

        self.assertEqual(t.localizations.count(), 2)

        t.localize('ja').delete()

        self.assertEqual(t.localizations.count(), 1)

    def test_track_album_relation(self):
        from apps.test.proxies import Album, Track

        t = Track.objects.get(item__source_item_id__startswith='t-1@some.service')

        self.assertEqual(t.item.parents.count(), 1)
        self.assertEqual(t.item.parents.filter(source_item_id__startswith='a-1')[0].children.count(), 3)
        self.assertEqual(Track.objects.count(), 2)

        t.item.parents.filter(source_item_id__startswith='a-1')[0].children.filter(source_item_id__startswith='t-2')[0].delete()

        self.assertEqual(t.item.parents.filter(source_item_id__startswith='a-1')[0].children.count(), 2)
        self.assertEqual(Track.objects.count(), 1)
