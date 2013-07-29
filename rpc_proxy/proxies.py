# -*- coding: utf-8 -*-
import logging
import re
import slumber

from datetime import datetime
from dateutil import parser as dateparser
from queryset_client import client
from urllib import urlencode
from urlparse import urlparse

try:

    # try to import django suite
    from django.conf import settings
    from django.core.cache import cache
    from django.db import models
    from django.core.exceptions import ObjectDoesNotExist
    from django.utils.importlib import import_module
    from django.utils.translation import ugettext as _

except Exception, e:

    class Cache(object):

        def __getattribute__(self, key):
            return lambda *args: None

    class ObjectDoesNotExist(Exception):

        pass

    def _(text):
        return text

    settings = object()
    cache = Cache()
    models = None
    import_module = __import__


from rpc_proxy import exceptions
from rpc_proxy.utils import logf


PK_ID = ('pk', 'id',)

logger = logging.getLogger(__name__)


def extend(instance, new_class, attrs={}):
    instance.__class__ = type(new_class.__name__,
                              (instance.__class__, new_class),
                              attrs)
    instance.__class__.__module__ = new_class.__module__
    instance.__module__ = new_class.__module__
    return instance

def mixin(cls, mixin):
    if mixin not in cls.__bases__:
        cls.__bases__ = (mixin,) + cls.__bases__

def get_setting(name, default=None):
    return getattr(settings, 'TASTYPIE_RPC_PROXY', {}).get(name, default)

def get_pk(obj):
    """
    This is a workaroud to seek non default ``id`` primary key value.
    Since queryset_client expects resources to have ``id`` fields as primary key
    by design, it's hard to support one-to-one like relationship.
    This method attempts to resolve such relation based on
    NON_DEFAULT_ID_FOREIGNKEYS settings value.
    """
    if isinstance(obj, int):
        return obj

    if isinstance(obj, str):
        # assumed to be a resource_uri
        return client.parse_id(obj)

    for key in get_setting('NON_DEFAULT_ID_FOREIGNKEYS', {}):
        if hasattr(obj, key):
            try:
                return get_pk(getattr(obj, key))
            except AttributeError, e:
                pass

    return obj.id


class QuerySet(client.QuerySet):

    def __init__(self, model, responses=None, query=None, **kwargs):
        super(QuerySet, self).__init__(model, responses, query, **kwargs)
        self._response_class = Response

    def __getitem__(self, index):
        try:
            return super(QuerySet, self).__getitem__(index)
        except IndexError, e:
            pass

    def _filter(self, *args, **kwargs):
        for key, value in kwargs.items():
            try:
                # convert resource_uri to numeric id
                id = client.parse_id('%s' % value)
                kwargs[key] = id
            except Exception, e:
                pass
        return super(QuerySet, self)._filter(*args, **kwargs)

    def _wrap_response(self, dictionary):
        return self._response_class(self.model,
                                    dictionary,
                                    _to_many_class=ManyToManyManager)

    def create(self, **kwargs):
        obj = super(QuerySet, self).create(**kwargs)
        return Response(model=self.model, url=obj.resource_uri)

    def get_or_create(self, **kwargs):
        obj, created = super(QuerySet, self).get_or_create(**kwargs)
        if not created:
            return obj, created
        return self.create(**kwargs), True


class Response(client.Response):

    def __init__(self, model, response=None, url=None, **kwargs):
        # implement proxy mixin
        model_name = model._model_name.lower()
        if model_name in ProxyClient._proxies:
            proxy = ProxyClient._proxies[model_name].__class__
            extend(self, proxy, proxy.__dict__.copy())
            self.__init_proxy__()

        super(Response, self).__init__(model, response, url, **kwargs)

        # the magic
        dir(self)

    def __repr__(self):
        if hasattr(self, 'resource_uri'):
            return self.resource_uri
        return '<%s: None>' % self.model._model_name.title()

    def __getattr__(self, name):
        """
        Overrides to support api namespace and to_one class diversity.
        """
        try:
            if name not in self._response:
                raise AttributeError(name)

            elif 'related_type' not in self._schema['fields'][name]:
                return self.__getitem__(name)

        except AttributeError, e:
            if name in PK_ID:
                return get_pk(self)

            return getattr(self.model, name)

        # resolves foreign key references in another api namespace
        # expects to be called with detail url like /api/v1/<resource>/<id>|schema/
        #
        # CAVEAT: resource_uri of referred resource has to have the same version 
        base_client = self.model._base_client

        if name in self._schema['fields']:
            schema = self._schema['fields'][name]

            if ('related_type' in schema and
                schema['related_type'] in ('to_one', 'to_many',)):
                if schema.get('schema'):
                    schema_uri = schema.get('schema')
                else:
                    try:
                        schema_uri = self._response[name]
                        schema_uri = schema_uri[0] if (
                            isinstance(schema_uri, list)) else schema_uri
                        schema_uri = schema_uri['resource_uri'] if (
                            isinstance(schema_uri, dict)) else schema_uri

                        logger.debug(logf({
                            'message': 'Trying to guess schema info from '
                                       'schema_uri.',
                            'schema_uri': schema_uri,
                        }))
                    except Exception, e:
                        raise exceptions.ProxyException(_('Couldn\'t identify related '
                                                          'field schema (%s).') % name)
        else:
            raise exceptions.ProxyException(_('The field seems not to be defined '
                                              'in the schema (%s).') % name)

        api_url = base_client._api_url
        version = base_client._version
        paths   = filter(None, schema_uri.replace(
                      base_client._api_path, '').split('/'))

        # strip <id> or ``schema`` part and extract resource_name
        paths.pop()
        resource_name = paths.pop()

        if version in paths: paths.remove(version)
        namespace = '/'.join(paths)

        logger.debug(logf({
            'message': 'Need namespace schema.',
            'attribute': name,
            'resource_uri': self._response[name],
            'client_key': ProxyClient.build_client_key(base_client._api_url, **{
                'version': base_client._version,
                'namespace': namespace,
                'auth': base_client._auth,
            }),
        }))

        proxy_client = ProxyClient.get(base_client._api_url,
                                       version=base_client._version,
                                       namespace=namespace,
                                       auth=base_client._auth)
        proxy_client.schema()

        model = proxy_client._model_gen(resource_name)

        # set manager alias
        if name is not resource_name:
            setattr(self.model, resource_name, getattr(self.model, name))

        if schema['related_type'] == 'to_many':
            resource_uris = [resource_uri['resource_uri'] if isinstance(resource_uri, dict) else resource_uri for resource_uri in self._response[name]]
            return ManyToManyManager(
                       model=model,
                       instance=self.model,
                       field_name=name,
                       query={'id__in': [client.parse_id(resource_uri) for resource_uri in resource_uris]})

        elif schema['related_type'] == 'to_one':
            return Response(model=model, url=self._response[name])

    @property
    def _response(self):
        if self.__response:
            return self.__response

        serializer = slumber.serialize.Serializer(default=self.model._main_client._store['format'])

        if self._url is not None:
            logger.debug(logf({
                'message': 'Getting cache...',
                'key': self._url,
            }))

            cached = cache.get(self._url)
            if cached:
                logger.debug(logf({
                    'message': 'Found in cache.',
                    'key': self._url,
                    'value': cached,
                }))

                self.refresh(serializer.loads(cached))
                return self.__response

        response = super(Response, self)._response

        if self._url is not None:
            if 'model' in response:
                del(response['model'])

            content = serializer.dumps(response)

            logger.debug(logf({
                'message': 'Setting cache...',
                'key': self._url,
                'value': content,
            }))

            cache.set(self._url, content)

        return response

    def refresh(self, data):
        self.__response = data
        try:
            self.model = self.model(**self.__response)
        except:
            self.model = self.model.__class__(**self.__response)

    def invalidate(self):
        resource = getattr(self.model._main_client, self.model._model_name)
        self.refresh(resource(client.parse_id(self.resource_uri)).get())


class Manager(client.Manager):

    def __init__(self, model):
        self.model = model

    def get_query_set(self):
        return QuerySet(self.model,
                        response_class=Response)


class ManyToManyManager(client.ManyToManyManager):

    def __init__(self, query=None, instance=None, field_name=None, **kwargs): 
        self._field_name = field_name
        super(ManyToManyManager, self).__init__(query, instance, **kwargs)

        # FIXME: work around a bug on handling empty to_many manager
        #        in tastypie_queryset_client
        if 'id__in' in self._query and len(self._query['id__in']) < 1:
            self._query.update({'id__in': 0})

    def get_query_set(self):
        return QuerySet(self.model,
                        query=self._query,
                        response_class=Response).filter()

    def filter(self, *args, **kwargs):
        if 'id__in' in kwargs:
            raise exceptions.ProxyException(_('"id__in" is not supported '
                                              'in ManyToManyManager.'))
        return QuerySet(self.model,
                        query=self._query,
                        response_class=Response).filter(*args, **kwargs)

    def clear(self):
        # work around a bug in tastypie_queryset_client
        self._query.update({"id__in": list(set([]))})
        setattr(self._instance, self._field_name, list(set([])))


class ProxyClient(client.Client):

    _clients = {}
    _proxies = {}
    _models = {}
    _schemas = {}

    def __new__(cls, url, **kwargs):
        key = ProxyClient.build_client_key(url, **kwargs)

        if key not in cls._clients:
            cls._clients[key] = super(ProxyClient,
                                      cls).__new__(cls)

        proxy = kwargs.get('proxy')
        if proxy:
            cls._proxies[proxy.__class__.__name__.replace('Proxy', '').lower()] = proxy

        return cls._clients[key]

    def __init__(self, base_url, auth=None, strict_field=True, client=None, **kwargs):

        self._api_url   = base_url

        parsed = urlparse(self._api_url)

        self._api_path  = parsed.path
        self._auth      = kwargs.get('auth', auth)
        self._namespace = kwargs.get('namespace', None)
        self._version   = kwargs.get('version', None)
 
        super(ProxyClient, self).__init__(ProxyClient.build_base_url(base_url,
                                                                     **kwargs),
                                          self._auth,
                                          strict_field,
                                          client)

    def _model_gen(self, model_name, strict_field=True, base_client=None):
        return self.extend_model(super(ProxyClient, self)._model_gen(model_name,
                                                                     strict_field,
                                                                     self))

    def extend_model(self, model):
        # overwrite manager and model members
        model.objects = Manager(model)

        model._setfield_original = model._setfield
        model._getfield_original = model._get_field
        model.save_original = model.save
        model.delete_original = model.delete

        def _setfield(obj, name, value):
            try:
                obj._setfield_original(name, value)
            except client.FieldTypeError, e:
                self.to_python(obj, name, value)
                super(obj.__class__, obj).__setattr__(name,
                                                      obj._fields[name])

        def _getfield(obj, name):
            try:
                return self.to_serializable(obj, name)
            except exceptions.ProxyException, e:
                return obj._getfield_original(name)

        def break_cache(obj):
            cache.delete(getattr(obj,
                                 'resource_uri',
                                 '%s%s/' % (obj._base_client._api_path,
                                            obj._client._store['base_url'].replace(
                                                obj._base_client._api_url,
                                                ''))))

        def save(obj):
            break_cache(obj)
            model.save_original(obj)                

        def delete(obj):
            break_cache(obj)
            try:
                model.delete_original(obj)
            except KeyError, e:
                try:
                    obj._client(get_pk(obj)).delete()
                    obj._clear_fields()
                except Exception, e:
                    raise exceptions.ProxyException(_('Failed to delete an object (%s): %s' % (obj, e,)))

        model._setfield = _setfield
        model._get_field = _getfield
        model.save = save
        model.delete = delete

        return model

    def to_python(self, obj, name, value):
        field_type = obj._schema_store['fields'][name]['type']
        new_value = value

        if type(value) in (str,):
            if field_type == 'datetime':
                new_value = dateparser.parse(value)
            elif field_type == 'date':
                new_value = dateparser.parse(value).date()
            elif field_type in ('list', 'json',):
                new_value = value

        if value != new_value:
            logger.debug(logf({
                'message': 'Converting to python...',
                'field': name,
                'type': field_type,
                'from': value.__repr__(),
                'to': new_value.__repr__(),
            }))

        obj._fields[name] = new_value

    def to_serializable(self, obj, name):
        field_type = obj._schema_store['fields'][name]['type']
        value = new_value = obj._fields[name]

        if field_type == 'date' and type(value) not in (str,):
            new_value = value.isoformat()

        if value != new_value:
            logger.debug(logf({
                'message': 'Serializing from python...',
                'field': name,
                'type': field_type,
                'from': value.__repr__(),
                'to': new_value.__repr__()
            }))
            return new_value

        raise exceptions.ProxyException(_('Raise to call super.'))

    def schema(self, model_name=None):
        path = '.'.join(self._base_url.replace(self._api_url,
                                               '').split('/')[:-1])

        if model_name is None:
            model_name = path
            url = self._base_url
        else:
            url = self._url_gen('%s/schema/' % model_name)

        if model_name not in ProxyClient._schemas:
            try:
                self._schema_store[model_name] = self.request(url)
                ProxyClient._schemas[model_name] = self._schema_store[model_name]
            except Exception, e:
                logger.debug(logf({
                    'message': 'Couldn\'t fetch the schema definition for some reason.',
                    'schema': model_name,
                }))

        # try to import namespaced proxies
        try:
            module = '%s.proxies' % self._namespace.replace('/', '.')
            import_module(module)
        except ImportError, e:
            try:
                # guess top level module from proxy class
                proxy = ProxyClient._proxies[ProxyClient._proxies.keys()[0]]
                module = '%s.%s' % (proxy.__class__.__module__.split('.')[0],
                                    module,)
                import_module(module)
            except ImportError, e:
                logger.debug(logf({
                    'message': 'Proxies module not found, '
                               'the namespace might not be structured based on '
                               'actual class path.',
                    'module': module,
                }))

            except Exception, e:
                pass

        return ProxyClient._schemas.get(model_name, {})

    def request(self, url, method='GET'):
        nocache = False

        if method != 'GET':
            logger.debug(logf({
                'message': 'Deleting cache...',
                'key': url,
            }))

            cache.delete(url)
            nocache = True
        else:
            logger.debug(logf({
                'message': 'Getting cache...',
                'key': url,
            }))

            result = cache.get(url)

            if result is not None:
                logger.debug(logf({
                    'message': 'Found in cache.',
                    'key': url,
                    'value': result,
                }))

                return result

        # override super to handle HTTP response error
        client = self._main_client._store
        url = self._url_gen(url)
        response = client['session'].request(method, url)

        if response.status_code >= 300:
            raise exceptions.ProxyException('Failed to fetch resource (%s, %s %s)' % (url,
                                                                                      method,
                                                                                      response.status_code,))

        serializer = slumber.serialize.Serializer(default=client['format'])
        result = serializer.loads(response.content)

        if not nocache:
            logger.debug(logf({
                'message': 'Setting cache...',
                'url': url,
                'value': result,
            }))

            cache.set(url, result)

        return result

    @property
    def proxies(self):
        if len(self._proxies.keys()) > 0:
            return self._proxies
        else:
            resources = {}
            for resource in self._schemas.keys():
                try:
                    resources[resource] = getattr(self, resource)
                except AttributeError, e:
                    # we don't need api endpoints here 
                    pass
            return resources

    @classmethod
    def get(cls, url, **kwargs):
        key = cls.build_client_key(url, **kwargs)
        return cls._clients.get(key,
                                ProxyClient(url,
                                            **kwargs))

    @classmethod
    def get_by_schema(cls, schema):
        for client in cls._clients.values():
            if schema in client._schema_store:
                return client
        return None

    @classmethod
    def build_base_url(cls, url, **kwargs):
        version = '%s/' % kwargs.get('version') if kwargs.get('version') else ''
        namespace = '%s/' % kwargs.get('namespace') if kwargs.get('namespace') else ''

        return '%s%s' % ('%s%s' % (url, '/' if not url.endswith('/') else ''),
                         re.sub('//+', '/', '%s/%s' % (version, namespace,)),)

    @classmethod
    def build_client_key(cls, url, **kwargs):
        auth = kwargs.get('auth', None)
        base_url = cls.build_base_url(url, **kwargs).rpartition('://')
        return '%s%s%s%s' % (base_url[0],
                             base_url[1],
                             '%s:%s@' % auth if auth else '',
                             base_url[2])


class ProxyOptions(object):

    abstract = False
    api_url = get_setting('API_URL', None)
    auth = (get_setting('SUPERUSER_USERNAME', None),
            get_setting('SUPERUSER_PASSWORD', None))
    client = ProxyClient
    model = None
    namespace = get_setting('API_NAMESPACE', None)
    resource_name = None
    version = get_setting('API_VERSION', 'v1')

    def __new__(cls, meta=None):
        overrides = {}

        # handle overrides
        if meta:
            for override_name in dir(meta):
                # no internals please
                if not override_name.startswith('_'):
                    overrides[override_name] = getattr(meta, override_name)

        return object.__new__(type('ProxyOptions', (cls,), overrides))


class ProxyMeta(type):

    def __new__(cls, name, bases, attrs):

        declarative = Response not in bases

        if declarative and name in ProxyClient._proxies:
            # returns existing proxy object
            return ProxyClient._proxies[name]

        meta = attrs.pop('Meta', attrs.pop('_meta', None))
        abstract = getattr(meta, 'abstract', False)

        # create new proxy class
        proxy = super(ProxyMeta, cls).__new__(cls, name, bases, attrs)
        proxy._meta = ProxyOptions(meta)
        proxy._meta.abstract = abstract

        if abstract:
            return proxy

        if not proxy._meta.model:
            try:
                proxy._meta.model = getattr(import_module('%s.models' % proxy.__module__.rpartition('.')[0]), name)
            except Exception, e:
                pass

        if proxy._meta.api_url:
            # return proxy class or object
            return proxy() if declarative else proxy
        else:
            # return model class which implements proxy interfaces
            if name not in ProxyClient._models.keys():
                model = proxy._meta.model

                if not model:
                    raise exceptions.ProxyException(_('Module seems not to be imported '
                                                      'within django application context '
                                                      '("%s" model not found). Specify '
                                                      'proper model in Meta class.') % name)

                # implement proxy mixin
                def __init__(obj, *args, **kwargs):
                    obj.__init__original(*args, **kwargs)
                    mixin(obj.__class__, proxy)
                    obj.__module__ = proxy.__module__
                    obj.__init_proxy__()

                model.__init__original = model.__init__
                model.__init__ = __init__

                ProxyClient._models[name] = model

        return ProxyClient._models[name]


class Proxy(object):

    __metaclass__ = ProxyMeta

    class Meta:

        abstract = True

    def __init__(self, *args, **kwargs):

        if (self._meta.abstract or
            (models and isinstance(self, models.Model))):
            super(Proxy, self).__init__(*args, **kwargs)
            return

        if not self._meta.api_url:
            raise exceptions.ProxyException(_('"API_URL" not found in settings or '
                                              '"api_url" not found in kwargs.'))

        self._client = self._meta.client.get(self._meta.api_url,
                                             version=self._meta.version,
                                             namespace=self._meta.namespace or '/'.join(self.__module__.split('.')[1:-1]),
                                             auth=self._meta.auth if self._meta.auth[0] is not None else None,
                                             proxy=self)

        try:
            class_name = self.__class__.__name__
            self._resource = getattr(self._client,
                                     self._meta.resource_name or class_name,
                                     getattr(self._client,
                                             self._meta.resource_name or class_name.lower(), None))
        except AttributeError, e:
            logger.debug(logf({
                'message': 'API seems not to have endpoint for the resource.',
                'resource': class_name,
            }))

    def __init_proxy__(self):
        pass

    def __getattr__(self, name):
        if name in PK_ID:
            return get_pk(self)

        if not models or (models and not isinstance(self, models.Model)):
            if name is not '_resource':
                return getattr(self._resource, name)

        raise AttributeError(_('There is no "%s" attribute on this proxy.' % (name,)))

    def invalidate(self):
        if models and isinstance(self, models.Model):
            pass
        else:
            super(Proxy, self).invalidate()

    @property
    def model_name(self):
        if models and isinstance(self, models.Model):
            return self.__class__.__name__.lower()
        else:
            return self.model._model_name

    @property
    def data(self):
        if models and isinstance(self, models.Model):
            dictionary = self.__dict__
            for key, value in dictionary.items():
                if key.startswith('_'):
                    del(dictionary[key])
            return dictionary
        else:
            dictionary = dict()
            for field in self.model._fields:
                dictionary[field] = getattr(self.model, field)
            return dictionary

