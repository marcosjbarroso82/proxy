from django.db import models
from django.http import HttpResponse
from django.http import JsonResponse

from apps.proxy_api.models.access_point import AccessPoint
from .base import BaseRequest, BaseRequestExecution, BaseModel, JinjaProcessorMixin
from adminsortable.models import SortableMixin
from jsonfield import JSONField
from ..fields import JSONTextField
from ..constants import JSON_INTERFACE_SCHEMA, JSON_KEY_VALUE_SCHEMA, JSON_OBJ_KEY_VALUE_SCHEMA

from ..utils import replace_jinga_tags, replace_jinga_tags_in_dict
import json
import requests
from jinja2 import Environment


class ReusableApiRequest(BaseRequest):
    url = models.CharField(max_length=500)
    interface = JSONTextField(null=True, blank=True, json_schema=JSON_INTERFACE_SCHEMA,
                              help_text='TODO: Make key and value required')
    # payload = JSONField(null=True, blank=True, default=dict)
    payload = JSONTextField(null=True, blank=True, json_schema={})

    def execute(self, access_point_request, params):
        req_exec_params = {
            'request_definition': self,
            'access_point_request': access_point_request
        }
        req_execution = ReusableApiRequestExecution.objects.create(**req_exec_params)
        return req_execution.execute(params)

    def __str__(self):
        return str(self.name)


class ReusableApiRequestExecution(BaseRequestExecution):
    request_definition = models.ForeignKey('ReusableApiRequest', related_name='request_executions')
    access_point_request = models.ForeignKey('AccessPointRequestExecution', related_name='reusable_request_executions')

    def execute(self, params):
        # Execute Operations and requests
        params = self.request_definition.execute_pre_request_operation(params)
        url = replace_jinga_tags(self.request_definition.url, params)

        print("about to make a request")
        print(url)
        print(params)
        if self.request_definition.method == 'get':
            req = requests.get(url)
        elif self.request_definition.method == 'post':
            payload = replace_jinga_tags_in_dict(json.loads(self.request_definition.payload), params)
            req = requests.post(url, json=payload)
        # TODO: implement rest of request methods
        params['response'] = json.loads(req.content.decode('utf-8'))
        print('response')
        print(req.status_code)
        params = self.request_definition.execute_post_request_operation(params)

        return params


class AccessPointReusableRequest(BaseModel, JinjaProcessorMixin, SortableMixin):
    condition = models.TextField(blank=True, default='')
    access_point = models.ForeignKey('AccessPoint', related_name='reusable_requests')
    request_definition = models.ForeignKey(ReusableApiRequest)
    json_request_params = JSONTextField(null=True, blank=True, json_schema=JSON_KEY_VALUE_SCHEMA,
                                    help_text='TODO: Make key and value required')

    # ordering field
    access_point_order = models.PositiveIntegerField(default=0, editable=False, db_index=True)

    class Meta:
        ordering = ['access_point_order']

    def execute(self, access_point_request, params):
        if self.check_condition(params):
            params['self_param'] = {}
            if self.json_request_params:
                params_values = json.loads(self.json_request_params)
            else:
                params_values = []
            for param in params_values:
                params['self_param'][param.get('key')] = replace_jinga_tags(param.get('value'), params)  # TODO: get debug value also

            params = self.execute_pre_request_operation(params)
            params = self.request_definition.execute(access_point_request, params)
            params = self.execute_post_request_operation(params)
        return params

    def check_condition(self, params):
        if not self.is_valid():
            return False
        if not self.condition:
            return True
        env = Environment()
        expr = env.compile_expression(self.condition)
        result = expr(**params)

        if result:
            return True
        return False

    def is_valid(self):
        # Check all Required params are being provided
        if self.request_definition:
            if self.request_definition.interface:
                interface = json.loads(self.request_definition.interface)
            else:
                interface = []

            for param in interface:
                if param.get('required'):
                    found = False
                    if self.json_request_params:
                        params_values = json.loads(self.json_request_params)
                    else:
                        params_values = []
                    for value in params_values:
                        if value.get('key') == param.get('key') and value.get('value'):  # TODO: get debug value also
                            found = True
                            break
                    if not found:
                        return False
        return True


class AccessPointAction(BaseModel, SortableMixin):
    access_point = models.ForeignKey('AccessPoint', related_name='actions')
    type = models.CharField(max_length=20, choices=(('update_var', 'update_var'), ('reusable_request', 'reusable_request')))
    request_definition = models.ForeignKey('ReusableApiRequest', null=True, blank=True)
    params = JSONTextField(null=True, blank=True, json_schema={})

    # ordering field
    access_point_order = models.PositiveIntegerField(default=0, editable=False, db_index=True)

    def get_params_json_schema(self):
        schema = {}
        if self.type == 'update_var':
            schema = JSON_OBJ_KEY_VALUE_SCHEMA
        elif self.type == 'reusable_request' and self.request_definition:
            schema = JSON_KEY_VALUE_SCHEMA.copy()
            interface = json.loads(self.request_definition.interface)
            keys = []
            for param in interface:
                keys.append(param.get('key'))
            schema['items']['properties']['key']['enum'] = keys
            # import ipdb; ipdb.set_trace()
        return schema

    class Meta:
        ordering = ['access_point_order']


class IncommingRequest(BaseModel):
    root_path = models.CharField(max_length=20, null=True, blank=True)
    slug = models.CharField(max_length=20, null=True, blank=True)
    extra_params = models.CharField(max_length=200, null=True, blank=True)
    response_type = models.CharField(max_length=20, null=True, blank=True, choices=(('text', 'text'), ('json', 'json')))
    response = models.TextField(null=True, blank=True)
    request = JSONField(null=True)

    def __str__(self):
        return str(self.pk)

    def parse(self, request, root_path, slug=None, extra_params=None):
        try:
            payload = json.loads(request.body.decode('utf-8'))
        except:
            raise
            # payload = {}

        # TODO: Remove replicated data
        req = dict()
        req['method'] = request.method
        req['GET'] = dict(request.GET)
        # req['POST'] = payload
        req['body'] = payload
        req['payload'] = payload
        req['request_payload'] = payload

        self.request = req

        self.root_path = root_path
        self.slug = slug

        self.extra_params = extra_params

    def process(self):
        aps = AccessPoint.objects.filter(active=True, method=self.request['method'].lower(), slug=self.slug, app__root_path=self.root_path)

        response = None
        for ap in aps:
            if ap.is_valid and ap.check_condition(request=self.request, url_path=self.extra_params):
                response = ap.process(request=self.request, url_path=self.extra_params)

        if not response:
            response = {'message': 'No Access Point Found'}

        if response.__class__ == dict:
            self.response_type = 'json'
            self.response = json.dumps(response)
            self.save()
            return JsonResponse(response)
        else:
            self.response_type = 'text'
            self.response = response
            self.save()
            return HttpResponse(response)


