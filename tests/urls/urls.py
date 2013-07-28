#-*- coding: utf-8 -*-
from django.conf.urls import include, patterns, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from tastypie.api import Api

from apps.test import resources

# namespaced resources
core_api = Api(api_name='core')
core_api.register(resources.Item())

meta_api = Api(api_name='meta')
meta_api.register(resources.Album())
meta_api.register(resources.AlbumLocalization())
meta_api.register(resources.Track())
meta_api.register(resources.TrackLocalization())

urlpatterns = patterns('',
    # v1
    url(r'^api/v1/', include(core_api.urls)),
    url(r'^api/v1/', include(meta_api.urls)),
    # v2
    # ...
)
