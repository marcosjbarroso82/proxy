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



class AccessPointAction(BaseModel, SortableMixin):
    access_point = models.ForeignKey('AccessPoint', related_name='actions')
    type = models.CharField(max_length=20, choices=(('update_state', 'update_state'), ('reusable_request', 'reusable_request')))
    request_definition = models.ForeignKey('ReusableApiRequest', null=True, blank=True)
    params = JSONTextField(null=True, blank=True, json_schema={})

    # ordering field
    access_point_order = models.PositiveIntegerField(default=0, editable=False, db_index=True)

    def get_params_json_schema(self):
        schema = {}
        if self.type == 'update_state':
            # schema = JSON_OBJ_KEY_VALUE_SCHEMA
            schema = {
                "type": "object",
                "format": "grid",
                    "properties": {
                        "key": {
                            "type": "string", "propertyOrder": 1, "required": True
                        },
                        "value": {
                            "type": "string", "propertyOrder": 2, "required": True
                        },
                        "debug_value": {
                            "type": "string", "propertyOrder": 3, "required": True
                        }
                    },
                "required": ["key", "value", "debug_value"],
                "defaultProperties": ["key", "value", "debug_value"]
            }
        elif self.type == 'reusable_request' and self.request_definition:
            # schema = JSON_KEY_VALUE_SCHEMA.copy()

            if self.request_definition.interface:
                interface = json.loads(self.request_definition.interface)
            else:
                interface = []


            schema = {
                "type": "object",
                "format": "grid",
                "properties": {
                    # "type": "object",
                    # "properties": {
                        # "key": {
                        #     "type": "string", "propertyOrder": 1
                        # },
                        # "value": {
                        #     "type": "string", "propertyOrder": 2
                        # },
                        # "debug_value": {
                        #     "type": "string", "propertyOrder": 3
                        # }
                    # }
                }
            }
            keys = []
            for param in interface:
                # keys.append(param.get('key'))
                key_value_sub_schema = {
                    "type": "object",
                    "format": "grid",
                    "properties": {
                        "value": {"type": "string"},
                        "debug_value": {"type": "string"}
                    }
                }
                schema['properties'][param.get('key')] = key_value_sub_schema
            # schema['items']['properties']['key']['enum'] = keys
            # import ipdb; ipdb.set_trace()
        return schema

    class Meta:
        ordering = ['access_point_order']

    def is_valid(self):
        if self.type == 'update_state':
            params = json.loads(self.params)
            if params.get('key') and params.get('value'):
                return True
        elif self.type == 'reusable_request' and self.request_definition:
            if self.params and self.params != 'null':  # TODO: Better handle null
                params = json.loads(self.params)
            else:
                params = dict()

            # Check all Required params are being provided
            if self.request_definition.interface:
                interface = json.loads(self.request_definition.interface)
            else:
                interface = []

            for interface_param in interface:
                if interface_param.get('required', None):
                    try:
                        key = interface_param.get('key')

                        if key not in params.keys() or not params[key].get('value', None):
                            return False
                    except:
                        import ipdb; ipdb.set_trace()
            return True

        # TODO: Implement
        return False

    def is_debug(self):
        if self.access_point.app.debug:
            return True
        return False

    def execute(self, access_point_request, params):
        params = params.copy()  # TODO: Is it neccessary ??
        if not self.is_valid():
            return params
        unprocessed_params = json.loads(self.params)


        if self.type == 'update_state':
            # {{state.update(chat_state='answering')}}
            key = unprocessed_params.get('key')

            if self.is_debug() and unprocessed_params.get('debug_value', None):
                value = unprocessed_params.get('debug_value')
            else:
                value = unprocessed_params.get('value')
            value = replace_jinga_tags(value, params)
            operation = "{{state.update(%s='%s')}}" % (key, value)
            try:
                replace_jinga_tags(operation, params)
            except:
                # "{{state.update(state.chat_state='answering')}}"
                # "{{state.update(chat_state='answering')}}"
                import ipdb; ipdb.set_trace()
        elif self.type == 'reusable_request':
            operation_params = dict()
            for key in unprocessed_params.keys():
                # import ipdb; ipdb.set_trace()
                if self.is_debug() and unprocessed_params.get('debug_value', None):
                    operation_params[key] = unprocessed_params[key]['debug_value']
                else:
                    operation_params[key] = unprocessed_params[key]['value']

                try:
                    operation_params[key] = replace_jinga_tags(operation_params[key], params)
                except:
                    import ipdb;
                    ipdb.set_trace()


            params['self_param'] = operation_params


            # for key in operation_params.keys():
            #     params['self_param'][operation_params.get('key')] = replace_jinga_tags(operation_params.get('value'),
            #                                                                 params)  # TODO: get debug value also

            # params = self.execute_pre_request_operation(params)
            params = self.request_definition.execute(access_point_request, params)
            # params = self.execute_post_request_operation(params)
        return params


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


