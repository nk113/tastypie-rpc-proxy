==================
tastypie-rpc-proxy
==================

.. image:: https://travis-ci.org/nk113/tastiypie-rpc-proxy.png?branch=master
    :alt: Build Status
    :target: http://travis-ci.org/nk113/tastiypie-rpc-proxy

The concept of **tastypie-rpc-proxy**, an etension of `tastypie-queryset-client`_ - many kudos to the author, is to help coding `tastypie`_ based RPC in easy manner. You can handle remote `tastypie`_ resources as if operating over local `django`_ model objects. Now you don't need to code your business logics and unit tests for both central `django`_ models and API client to read the central data from remote boxes separately - in other word you can deploy the same application code for central API and remote client, **rpc-proxy** looks after everything for you. Don't you think it's convenient if you can code like below to control remote object behind `tastypie`_ API?

::

    title_ja = Track.objects.get(item__source_item_id__startswith='t-2').localize('ja').title

As you know, this code also works perfectly with local `django`_ model. The proxy class tries to access remote `tastypie`_ resources if *API_URL* settings is provided, and to read local model resources if it's not. All right, take a look once at how **rpc-proxy** works. The **rpc-proxy** also can be used as a simple tastypie client which has similar interfaces as `django`_ queryset API.

Features enhanced from `tastypie-queryset-client`_
--------------------------------------------------

* data proxy layer, which enables switching between local model access and RPC depending on *API_URL* settings
* API namespace
* remote API schema and foreing key caching
* remote API foreign key object operation
* supporting custom field type

etc.

Recommendation
==============

* setting up `django`_ cache backend is strongly recommended to reduce API requests
* 

Quick Start
===========

``apps/test`` application is good to start with. Following section goes through the application to describe what you can enjoy from **rpc-proxy**. See the ``apps/test`` application code for the implementation in detail. This test application has models that represent common music data scheme - Album, Track metadata and these localisations. The Item model associates them as parent and child relationship.

Coding `Tastypie`_ based RPC
----------------------------

Define models
^^^^^^^^^^^^^

Define `django`_ models as usual. The model methods will be implemented on *proxy* classes later instead of on the models so just define model fields here - ``apps/test/models.py``.

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
^^^^^^^^^^^^^^^^

Design `tastypie`_ resources carefully. Might need to have various filters, orderings and access controls - ``apps/test/resources.py``.

::

    (...)
    class Item(resources.ModelResource):

        class Meta(resources.SuperuserMeta):

            queryset = models.Item.objects.all()
            resource_name = 'item'
            (...)

        parents = fields.ToManyField('apps.test.resources.Item', 'parents', null=True)
        children = fields.ToManyField('apps.test.resources.Item', 'children', null=True)
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

Configure URLs, separate metadata resources from Item resource to demonstrate namespaces - ``apps/test/urls/url.py``

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
^^^^^^^^^^^^^^

Now it's time to code proxy, ``proxies.py`` is expected as script name for *proxy* classes by default. Write business logics usually we write on django models here. Proxies here are implementing some useful methods for localization - ``apps/test/proxies.py``.

::

    (...)
    from apps.test.models import ITEM_TYPES, META_TYPES

    (...)
    def get_default_language_code():
        return getattr(settings, 'LANGUAGE_CODE', 'en-US').split('-')[0].lower()

    (...)
    class Localizable(proxies.Proxy):

        class Meta:

            abstract = True

        def __init_proxy__(self):
            super(Localizable, self).__init_proxy__()

            class_name = self.__class__.__name__

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
                          eta:

            namespace = 'core'

        (...)
        @property
        def meta_type_display(self):
           es to the local models:

::

    TASTYPIE_RPC_PROXY = {
        'API_NAMESPACE': 'meta',
        'NON_DEFAULT_ID_FOREIGNKEYS': ('item',),
        'SUPERUSER_USERNAME': 'test',
        'SUPERUSER_PASSWORD': 'test',
    }

::

    >>> from apps.test.proxies import *
 albumlocalization"."ctime", "test_albumlocalization"."utime", "test_albumlocalization"."language_code", "test_albumlocalization"."title", "test_albumlocalization"."description", "test_albumlocalization"."artist", "test_albumlocalization"."label", "test_albumlocalization"."album_id" FROM "test_albumlocalization" WHERE ("LECT "test_track"."ctime", "test_track"."utime", "test_track"."item_id", "test_track"."release_date", "test_track"."isrc", "test_track"."length", "test_track"."trial_start_position", "test_track"."trial_duration" FROM "test_track" WHERE "test_track"."item_id" = 2 ; args=(2,)
    [DEBUG: django.db.backends: execute] (0.000) SELECT "test_item"."id", "test_item"."cti" = en ); args=(2, 'en')
    >>> t_en.title
    u'A Pop Song 1'
    >>> t_en.title = 'A Pop Song 1 revised title'
    >>> t_en.save()
    [DEBUG: django.db.backends: execute] (0.000) SELECT (1) AS "a" FROM "test_tracklocalization" WHERE "test_tracklocalization"."id" = 1  LIMIT 1; args=(1,)
    [DEBUG: djanTYPIE_RPC_PROXY = {
        'API_NAMESPACE': 'meta',
        'API_URL': 'http://127.0.0.1:8000/api',
        (_startswith='t-1').metadata.localize('en')
    [DEBUG: rpc_proxy.proxies: __getattr__] item: /api/v1/core/item/1/, need namespace schem1:8000/api/v1/core/)
    (...)
    [INFO: requests.packages.urllib3.connectionpool: _new_conn] Starting new HTTP connection (1): 127.0.0.1
    [DEBUG: requests.packages.urllib3.connectionpool: _make_request] "GET" 200 None
    [DEBUG: requests.packages.urllib3.connectionpool: _make_request] "GET /api/v1/meta/tracklocalization/?id__in=1&id__in=2&language_code=en HTTP/1.1" 200 None
    >>> t_en.title
    'A Pop Song 1'
    >>> t_en.title = 'A Pop Song 1 revised title'
    >>> t_en.save()
    [DEBUG: requests.packages.urllib3.connectionpool: _make_request] "PUT /api/v1/meta/tracklo------------------------------

You can also utilize **rpc-proxy** with no proxy definition - call remote tastypie API with queryset interface. In this case you can just only control remote resources with standard CRUD / REST manner `Tastyw().date()
    >>> album.save()
    >>> album.item.children.all()[0].parents.all()[0].album.release_date == datetime.now().date()
    True
    >>> str(album.item.children.all()[0].track) == str(track)
    True

.. note:: You have to uncomment following fields on the Item resource in *apps.test.resources.py* and to clear cache to work above expectedly though.

::

    (...)
    # album = fiego model in local.

auth
----

*Tuple* or *List*, optional, a convination of username and password to access the API e.g. ``(username, password,)``. SUPERUSER_USERNAME and SUPE 'API_URL': 'http://127.0.0.1:8000/api',
    cation, useful to allow all operations over all remote resources e.g. ``'test'``.

SUPERUSER_PASSWORD
------------------

String, optional, defines default password of superuser for API authentication, useful to allow all operations over all remote resources e.g. ``'test'``.

.. _tastypie-queryset-client: https://github.com/ikeikeikeike/tastypie-queryset-client
.. _tastypie: https://github.com/toastdriven/django-tastypie
.. _django: https://www.djangoproject.com
