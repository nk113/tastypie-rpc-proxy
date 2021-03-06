# -*- coding: utf-8 -*-
import json
import logging

from django.conf import settings
from tastypie import fields
from tastypie.resources import ModelResource as TastypieModelResource

from rpc_proxy.utils import logf


ALL_METHODS = ('get', 'post', 'put', 'patch', 'delete',)

logger = logging.getLogger(__name__)


class ModelResource(TastypieModelResource):

    def __init__(self):
        # support to_many related field filtering and ordering
        self._meta.filtering.update({
            'id': ('exact', 'in',),
        })

        super(ModelResource, self).__init__()

    def _handle_500(self, request, exception):
        response = super(ModelResource, self)._handle_500(request, exception)
        self.debug(request, response, logger.exception)
        return response

    def debug(self, request, response, log=logger.debug):
        info = log if log == logger.exception else logger.info

        data = {
            'message': 'API called.',
            'user': request.user,
            'method': request.method,
            'status_code': response.status_code,
            'path_info': request.META.get('PATH_INFO'),
            'query_string': request.META.get('QUERY_STRING'),
        }

        info(logf(data))

        if len(request.raw_post_data):
            data['post_data'] = request.raw_post_data.decode('utf-8')

        if len(response.content):
            data['response'] = response.content.decode('utf-8')

        log(logf(data))

    def dispatch(self, request_type, request, **kwargs):
        # this needs to be called before method check
        try:
            self.is_authenticated(request)

            response = super(ModelResource, self).dispatch(request_type,
                                                           request,
                                                           **kwargs)
        except Exception, e:
            logger.exception(logf({
                'message': 'A fatal error has occurred during processing dispatch',
                'exception': e,
            }))
            raise e

        self.debug(request, response)

        return response

    def is_authenticated(self, request):
        super(ModelResource, self).is_authenticated(request)

        # allow superuser all operations dynamically
        if request.user.is_superuser:

            logger.debug(logf({
                'message': 'Hello superuser you can do anything with this resource.',
                'resource': request.META['PATH_INFO'],
            }))

            self._meta.list_allowed_methods = ALL_METHODS
            self._meta.detail_allowed_methods = ALL_METHODS

            for field in self._meta.excludes:
                self.fields[field] = fields.CharField(attribute=field,
                                                      blank=True,
                                                      null=True,
                                                      readonly=True)

            self._meta.excludes = []

    def build_schema(self):
        schema = super(ModelResource, self).build_schema()

        # add schema url of to_class to the field schema
        for field_name, field_object in self.fields.items():
            if isinstance(field_object, fields.RelatedField):
                schema['fields'][field_name]['schema'] = field_object.to_class().get_resource_uri(url_name='api_get_schema')

        return schema
