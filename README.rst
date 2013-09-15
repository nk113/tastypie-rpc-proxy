==================
tastypie-rpc-proxy
==================

.. image:: https://travis-ci.org/nk113/tastypie-rpc-proxy.png?branch=master
    :alt: Build Status
    :target: http://travis-ci.org/nk113/tastypie-rpc-proxy
.. image:: https://coveralls.io/repos/nk113/tastypie-rpc-proxy/badge.png
    :alt: Coverage Status
    :target: https://coveralls.io/r/nk113/tastypie-rpc-proxy

The concept of **tastypie-rpc-proxy**, an etension of `tastypie-queryset-client`_ - many kudos to the author, is to help coding `tastypie`_ based RPC in easy manner. With **rpc_proxy** you can handle remote `tastypie`_ resources as if operating over local `django`_ model objects. Now you don't need to separately code your business logics and unit tests for both central `django`_ models and API client to read the central data from remote boxes - in other word you can use the same application code for central database-accesible environment and remote API client, **rpc_proxy** looks after everything for you. In common situation you might write following unreadable code to operate remote resource objects behind `tastypie`_ API.

::

    headers = {'content-type': 'application/json'}
    auth = ('test', 'test',)
    filters = {
        'track__item__source_item_id__startswith': 't-2',
        'language_code': 'ja',
    }
    response = requests.get('http://127.0.0.1:8000/api/v1/meta/tracklocalization/',
                            params=filters,
                            headers=headers,
                            auth=auth)
    title_ja = response.json()['objects'][0]['title']

Don't you think it's convenient if you can code like below to do the same stuff as above?

::

    title_ja = Track.objects.get(item__source_item_id__startswith='t-2').localize('ja').title

Using **rpc_proxy** the code to operate over remote resources looks like this. As you see, this code is 100% compatible with `django`_ model / queryset api terminology so that means this code can be used to operate over both local model objects and remote resource objects. While you might code like this django model / queryset style business logic for the central database-accessible environment - which hosts tasypie resources API as well, until today, at the same time you also might have to write some code for the API client side like next above to access the central data resources which represents actual database. So you have needed to maintain 2 versions of code for local and remote environments actually. **rpc_proxy** is intended for getting you out of this sort of annoying situation. The proxy class tries to access remote `tastypie`_ resources if *API_URL* settings is provided, and to read local models if it's not. All right, take a look once at how **rpc_proxy** works. The **rpc_proxy** also can be used as a simple tastypie client which has similar interfaces as `django`_ queryset API.

Features enhanced from tastypie-queryset-client
===============================================

* data proxy layer, which enables switching between local model access and RPC depending on *API_URL* settings
* API namespace
* remote API schema and foreing key caching
* remote API foreign key object operation
* supporting custom field type

etc.

Notes
=====

* setting up `django`_ cache backend is strongly recommended to reduce API requests.
* defining `tastypie`_ resources inheriting *rpc_proxy.resources.ModelResource* is strongly recommended to fully support foreign key operations. 

Installation
============

Pip installation is available. Note that this does only install ``rpc_proxy`` library, doesn't contain example ``example`` application.

::

    pip install tastypie-rpc-proxy

Quick Start
===========

``example`` application is good to start with. Following section goes through the application to describe what you can enjoy from **rpc_proxy**. See the ``example`` application code for the implementation in detail. This test application has models that represent common music data scheme - Album, Track metadata and these localizations. The Item model associates them as parent and child relationship.

Define models
-------------

First of all, define `django`_ models as usual. The model methods will be implemented on *proxy* classes later instead of on the models so just define model fields here - ``example/models.py``.

::

    (...)
    META_TYPES = ((0, 'Track',), (1, 'Album',),)

    (...)
    class Item(Model):
        (...)
        meta_type = models.SmallIntegerField(choices=META_TYPES, default=0)
        parents = models.ManyToManyField('self', symmetrical=False, related_name='children', blank=True, null=True)
        source_item_id = models.CharField(max_length=64, unique=True)


    class Album(BasicLocalizable):

        item = models.OneToOneField(Item, primary_key=True)
        title = models.CharField(max_length=255, blank=True, null=False)
        (...)


    class AlbumLocalization(BasicLocalization, MusicLocalization):

        album = models.ForeignKey(Album)
        language_code = models.CharField(max_length=2, choices=getattr(settings, 'LANGUAGES'), blank=False, null=False)
        (...)

Define resources
----------------

Design `tastypie`_ resources carefully. Might need to have various filters, orderings and access controls - ``example/resources.py``. The resources should be defined inheriting *rpc_proxy.resources.ModelResource* class to support foreign key operations.

::

    (...)
    from rpc_proxy import resources

    (...)
    class Item(resources.ModelResource):

        class Meta(resources.SuperuserMeta):

            queryset = models.Item.objects.all()
            resource_name = 'item'
            (...)

        parents = fields.ToManyField('example.resources.Item', 'parents', null=True)
        children = fields.ToManyField('example.resources.Item', 'children', null=True)
        (...)


    class Album(resources.ModelResource):

        class Meta(resources.SuperuserMeta):

            queryset = models.Album.objects.all()
            resource_name = 'album'
            (...)

        item = fields.ForeignKey(Item, 'item')
        (...)


    class AlbumLocalization(resources.ModelResource):

        class Meta(resources.SuperuserMeta):

            queryset = models.AlbumLocalization.objects.all()
            resource_name = 'albumlocalization'
            (...)

        album = fields.ForeignKey(Album, 'album')
        (...)

Configure URLs
--------------

Separate metadata resources from Item resource to demonstrate namespaces - ``example/urls/url.py``

::

    (...)
    core_api = Api(api_name='core')
    core_api.register(resources.Item())

    meta_api = Api(api_name='meta')
    meta_api.register(resources.Album())
    meta_api.register(resources.AlbumLocalization())
    (...)

    urlpatterns = patterns('',
        # v1
        url(r'^api/v1/', include(core_api.urls)),
        url(r'^api/v1/', include(meta_api.urls)),
        # v2
        # ...
    )

Create proxies
--------------

Now it's time to code proxy, ``proxies.py`` is expected filename of the module *proxy* classes are defined by default. Write business logics usually we write on django models here. Proxies here are implementing some useful methods for localization - ``example/proxies.py``.

::

    (...)
    from example.models import ITEM_TYPES, META_TYPES

    (...)
    def get_default_language_code():
        return getattr(settings, 'LANGUAGE_CODE', 'en-US').split('-')[0].lower()


    (...)
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


    (...)
    class Item(proxies.Proxy):

        class Meta:

            namespace = 'core'

        (...)
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


Import proxies
--------------

All right, let's call those proxies with the ``manage.py shell``. After loading fixture, import them with no *API_URL* settings like below, then you can see accesses to the local models:

::

    TASTYPIE_RPC_PROXY = {
        'API_NAMESPACE': 'meta',
        'NON_DEFAULT_ID_FOREIGNKEYS': ('item',),
        'SUPERUSER_USERNAME': 'test',
        'SUPERUSER_PASSWORD': 'test',
    }

::

    >>> from example.proxies import *
    >>> a = Album.objects.get(item__source_item_id__startswith='a-1')
    [DEBUG: django.db.backends: execute] (0.001) SELECT "test_album"."ctime", "test_album"."utime", "test_album"."item_id", "test_album"."release_date" FROM "test_album" INNER JOIN "test_item" ON ("test_album"."item_id" = "test_item"."id") WHERE "test_item"."source_item_id" LIKE a-1% ESCAPE '\' ; args=(u'a-1%',)
    >>> a.localize('en').title
    [DEBUG: django.db.backends: execute] (0.000) SELECT "test_item"."id", "test_item"."ctime", "test_item"."utime", "test_item"."item_type", "test_item"."meta_type", "test_item"."source_item_id" FROM "test_item" WHERE "test_item"."id" = 1 ; args=(1,)
    [DEBUG: django.db.backends: execute] (0.000) SELECT "test_albumlocalization"."id", "test_albumlocalization"."ctime", "test_albumlocalization"."utime", "test_albumlocalization"."language_code", "test_albumlocalization"."title", "test_albumlocalization"."description", "test_albumlocalization"."artist", "test_albumlocalization"."label", "test_albumlocalization"."album_id" FROM "test_albumlocalization" WHERE ("test_albumlocalization"."album_id" = 1  AND "test_albumlocalization"."language_code" = en ); args=(1, 'en')
    u'A Pop Song Collection'
    >>> t_en = a.item.children.get(source_item_id__startswith='t-1').metadata.localize('en')
    [DEBUG: django.db.backends: execute] (0.000) SELECT "test_item"."id", "test_item"."ctime", "test_item"."utime", "test_item"."item_type", "test_item"."meta_type", "test_item"."source_item_id" FROM "test_item" INNER JOIN "test_item_parents" ON ("test_item"."id" = "test_item_parents"."from_item_id") WHERE ("test_item_parents"."to_item_id" = 1  AND "test_item"."source_item_id" LIKE t-1% ESCAPE '\' ); args=(1, u't-1%')
    [DEBUG: django.db.backends: execute] (0.000) SELECT "test_track"."ctime", "test_track"."utime", "test_track"."item_id", "test_track"."release_date", "test_track"."isrc", "test_track"."length", "test_track"."trial_start_position", "test_track"."trial_duration" FROM "test_track" WHERE "test_track"."item_id" = 2 ; args=(2,)
    [DEBUG: django.db.backends: execute] (0.000) SELECT "test_item"."id", "test_item"."ctime", "test_item"."utime", "test_item"."item_type", "test_item"."meta_type", "test_item"."source_item_id" FROM "test_item" WHERE "test_item"."id" = 2 ; args=(2,)
    [DEBUG: django.db.backends: execute] (0.000) SELECT "test_tracklocalization"."id", "test_tracklocalization"."ctime", "test_tracklocalization"."utime", "test_tracklocalization"."language_code", "test_tracklocalization"."title", "test_tracklocalization"."description", "test_tracklocalization"."artist", "test_tracklocalization"."label", "test_tracklocalization"."track_id" FROM "test_tracklocalization" WHERE ("test_tracklocalization"."track_id" = 2  AND "test_tracklocalization"."language_code" = en ); args=(2, 'en')
    >>> t_en.title
    u'A Pop Song 1'
    >>> t_en.title = 'A Pop Song 1 revised title'
    >>> t_en.save()
    [DEBUG: django.db.backends: execute] (0.000) SELECT (1) AS "a" FROM "test_tracklocalization" WHERE "test_tracklocalization"."id" = 1  LIMIT 1; args=(1,)
    [DEBUG: django.db.backends: execute] (0.000) UPDATE "test_tracklocalization" SET "ctime" = 2013-06-14 02:04:20, "utime" = 2013-07-27 00:47:35.058121, "language_code" = en, "title" = A Pop Song 1 revised title, "description" = Description for the Pop Song 1., "artist" = Test, "label" = Label Test, "track_id" = 2 WHERE "test_tracklocalization"."id" = 1 ; args=(u'2013-06-14 02:04:20', u'2013-07-27 00:47:35.058121', u'en', 'A Pop Song 1 revised title', u'Description for the Pop Song 1.', u'Test', u'Label Test', 2, 1)
    >>> t_en.title
    'A Pop Song 1 revised title'

OK then reset database and let's do the same things with *API_URL* settings, you can find that the proxy calls remote `tastypie`_ API this time:

::

    TASTYPIE_RPC_PROXY = {
        'API_NAMESPACE': 'meta',
        'API_URL': 'http://127.0.0.1:8000/api',
        (...)
    }

::

    >>> from example.proxies import *
    (...)
    >>> a = Album.objects.get(item__source_item_id__startswith='a-1')
    [DEBUG: requests.packages.urllib3.connectionpool: _make_request] "GET /api/v1/meta/album/?item__source_item_id__startswith=a-1 HTTP/1.1" 200 None
    [DEBUG: rpc_proxy.proxies: to_python] to_python (release_date <date>): '2013-07-26' -> datetime.date(2013, 7, 26)
    >>> a.localize('en').title
    [INFO: requests.packages.urllib3.connectionpool: _new_conn] Starting new HTTP connection (1): 127.0.0.1
    [DEBUG: requests.packages.urllib3.connectionpool: _make_request] "GET /api/v1/meta/albumlocalization/?album=1 HTTP/1.1" 200 None
    [DEBUG: requests.packages.urllib3.connectionpool: _make_request] "GET /api/v1/meta/albumlocalization/?id__in=1&id__in=2&language_code=en HTTP/1.1" 200 None
    'A Pop Song Collection'
    >>> t_en = a.item.children.get(source_item_id__startswith='t-1').metadata.localize('en')
    [DEBUG: rpc_proxy.proxies: __getattr__] item: /api/v1/core/item/1/, need namespace schema (http://127.0.0.1:8000/api/v1/core/)
    (...)
    [DEBUG: rpc_proxy.proxies: _response] getting cache... (/api/v1/core/item/1/)
    [INFO: requests.packages.urllib3.connectionpool: _new_conn] Starting new HTTP connection (1): 127.0.0.1
    [DEBUG: requests.packages.urllib3.connectionpool: _make_request] "GET /api/v1/core/item/1/ HTTP/1.1" 200 None
    [DEBUG: rpc_proxy.proxies: _response] setting cache... (/api/v1/core/item/1/ -> {"ctime": "2013-06-13T19:42:56", "source_item_id": "a-1@some.service", "children": ["/api/v1/core/item/2/", "/api/v1/core/item/3/", "/api/v1/core/item/5/"], "item_type": 0, "meta_type": 1, "parents": [], "utime": "2013-06-13T20:02:38", "id": 1, "resource_uri": "/api/v1/core/item/1/"})
    [DEBUG: rpc_proxy.proxies: __getattr__] children: ['/api/v1/core/item/2/', '/api/v1/core/item/3/', '/api/v1/core/item/5/'], need namespace schema (http://127.0.0.1:8000/api/v1/core/)
    (...)
    [INFO: requests.packages.urllib3.connectionpool: _new_conn] Starting new HTTP connection (1): 127.0.0.1
    [DEBUG: requests.packages.urllib3.connectionpool: _make_request] "GET /api/v1/core/item/?id__in=2&id__in=3&id__in=5 HTTP/1.1" 200 None
    [DEBUG: requests.packages.urllib3.connectionpool: _make_request] "GET /api/v1/core/item/?source_item_id__startswith=t-1&id__in=2&id__in=3&id__in=5 HTTP/1.1" 200 None
    [INFO: requests.packages.urllib3.connectionpool: _new_conn] Starting new HTTP connection (1): 127.0.0.1
    [DEBUG: requests.packages.urllib3.connectionpool: _make_request] "GET /api/v1/meta/track/?item=2 HTTP/1.1" 200 None
    [DEBUG: rpc_proxy.proxies: to_python] to_python (release_date <date>): '2013-06-14' -> datetime.date(2013, 6, 14)
    [INFO: requests.packages.urllib3.connectionpool: _new_conn] Starting new HTTP connection (1): 127.0.0.1
    [DEBUG: requests.packages.urllib3.connectionpool: _make_request] "GET /api/v1/meta/tracklocalization/?track=2 HTTP/1.1" 200 None
    [DEBUG: requests.packages.urllib3.connectionpool: _make_request] "GET /api/v1/meta/tracklocalization/?id__in=1&id__in=2&language_code=en HTTP/1.1" 200 None
    >>> t_en.title
    'A Pop Song 1'
    >>> t_en.title = 'A Pop Song 1 revised title'
    >>> t_en.save()
    [DEBUG: requests.packages.urllib3.connectionpool: _make_request] "PUT /api/v1/meta/tracklocalization/1/ HTTP/1.1" 204 0
    >>> t_en.title
    'A Pop Song 1 revised title'

That's it! Hope this enpowers you to write clean code and reduce time to code boring redundant stuff!

Testing proxy code
==================

Unit tests for proxy classes can be ran in both local `django`_ model and remote `tastypie`_ API context. Those tests should inherit ``rpc_client.test.Proxy`` class. If you are to run the unit tests for both contexts separated settings need to be prepared - API context with *API_URL*, local model context with **NO** *API_URL* settings. Please take a look at how the unit tests for ``example`` application works - see ``runtests.py`` and ``tox.ini``.

As a simple tastypie client
===========================

You can also utilize **rpc_proxy** with no proxy definition - just call remote tastypie API with queryset interface. In this case **rpc_proxy** doesn't need to be imported within django application context. Only standard CRUD / REST operations `tastypie`_ implements by default are supported. See `tastypie-queryset-client`_ for detailed usages.

::

    >>> from datetime import datetime
    >>> from rpc_proxy.proxies import *
    >>>
    >>> api = ProxyClient('http://127.0.0.1:8000/api/',
    ...                   version='v1',
    ...                   namespace='meta',
    ...                   auth=('test', 'test',))
    >>> api.proxies
    {'album': queryset_client.client.Model,
     'albumlocalization': queryset_client.client.Model,
     'track': queryset_client.client.Model,
     'tracklocalization': queryset_client.client.Model}
    >>>
    >>> Track = api.track
    >>> track = Track.objects.filter(item__source_item_id__startswith='t-1')[0]
    >>> album = track.item.parents.all()[0].album
    >>> album.release_date = datetime.now().date()
    >>> album.save()
    >>> album.item.children.all()[0].parents.all()[0].album.release_date == datetime.now().date()
    True
    >>> str(album.item.children.all()[0].track) == str(track)
    True

.. note:: You have to uncomment following fields on the Item resource in ``example.resources.py`` and to clear cache to work above expectedly though.

::

    (...)
    # album = fields.OneToOneField('example.resources.Album', 'album', null=True)
    # track = fields.OneToOneField('example.resources.Track', 'track', null=True)

Namespace and Resource Endpoint
===============================

The final URL of an API resource endpoint consists of:

::

    '%s/%s/%s/%s/' % (API_URL, API_VERSION, API_NAMESPACE, resource_name,)

Proxy Meta class options
========================

abstract
--------

*Boolean*, optional, indicates if the Meta class is abstract class.

api_url
-------

*String*, optional, base url prefix of the API endpoint, if not given **rpc_proxy** tries to load corresponding django model in local.

auth
----

*Tuple* or *List*, optional, a combination of username and password to access the API e.g. ``(username, password,)``. SUPERUSER_USERNAME and SUPERUSER_PASSWORD settings variables will be applied by default.

client
------

*ProxyClient* class, optional, intended for extending ProxyClient class, *ProxyClient* class by default.

model
-----

`django`_ *Model* class, optional, a model that proxy loads when *API_URL* is not provided in the settings, if this option is not given, the proxy class looks for corresponding model class which has the same name as the proxy class on ``models.py`` module in the same module as ``proxies.py`` belongs to, by default.

namespace
---------

*String*, optional, defines namespace of the resource follows to version, *API_NAMESPACE* will be applied if it's not provided e.g. ``core``.

resource_name
-------------

*String*, optional, defines resource name of the proxy, the name of the proxy class will be applied if not provided e.g. ``'track'``.

version
-------

*String*, optional, defines version of the resource follows to *api_url*, ``'v1'`` will be used if *API_VERSION* is not provided.

Settings
========

**rpc_proxy** accepts following settings variables defined as **TASTYPIE_RPC_PROXY** dictionary in `django`_ settings. The settings look like:

::

    TASTYPIE_RPC_PROXY = {
        'API_URL': 'http://127.0.0.1:8000/api',
        'SUPERUSER_USERNAME': 'test',
        'SUPERUSER_PASSWORD': 'test',
        (...)
    }


API_NAMESPACE
-------------

*String*, optional, specifies default remote API namespace follows to the version section e.g. ``'core/content'``.

API_URL
-------

String, optional, defines default base prefix URL of remote tastypie API, **rpc_proxy** loads local models as proxy class if this is not specified e.g. ``'https://example.com/django/app/api'``.

.. note:: This value could technically be updated dynamically but it does not take any effect until the application is reloaded.  

API_VERSION
-----------

String, optional, defines default versioning of remote API follows to *API_URL* e.g. ``'v1'``.

NON_DEFAULT_ID_FOREIGNKEYS
--------------------------

Tuple or List, optional, defines custom primary key field names appear in remote resouces e.g. ``('user',)``.

SUPERUSER_USERNAME
------------------

String, optional, defines default username of superuser for API authentication, useful to allow internal system user to operate over all remote resources e.g. ``'test'``.

SUPERUSER_PASSWORD
------------------

String, optional, defines default password of superuser for API authentication, useful to allow internal system user to operate over all remote resources e.g. ``'test'``.

GitHub
======

https://github.com/nk113/tastypie-rpc-proxy


.. _tastypie-queryset-client: https://github.com/ikeikeikeike/tastypie-queryset-client
.. _tastypie: https://github.com/toastdriven/django-tastypie
.. _django: https://www.djangoproject.com
