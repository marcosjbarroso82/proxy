from django.db import models
from adminsortable.fields import SortableForeignKey
from adminsortable.models import SortableMixin
from .constants import REQUEST_METHODS
# from django.shortcuts import HttpResponse
from django.http import JsonResponse
from jsonfield import JSONField
from jinja2 import Template, Environment

import re
import json
import requests


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    log = models.TextField(null=True, blank=True, default='')

    def logger(self, data):
        self.log += '%s: %s %s' % (str(self.__class__.__name__), data, '<br/>')

    class Meta:
        abstract = True


class JinjaProcessorMixin(models.Model):
    class Meta:
        abstract = True

    pre_request_operation = models.TextField(null=True, blank=True)
    post_request_operation = models.TextField(null=True, blank=True, help_text='available variables: request, '
                                                                               'context, state, response')
    def execute_pre_request_operation(self, params):
        return self.execute_operation(self.pre_request_operation, params)

    def execute_post_request_operation(self, params):
        return self.execute_operation(self.post_request_operation, params)

    @staticmethod
    def execute_operation(operation, params):
        result = params.copy()
        if operation:
            replace_jinga_tags(operation, params)
        return result


class BaseRequestExecution(BaseModel):
    # TODO: Try to abstract execute method
    class Meta:
        abstract = True


class RequestState(BaseModel):
    hash_id = models.CharField(max_length=50)
    value = JSONField(null=True, blank=True, default=dict, help_text='jinja. Available vars: ')


class AccessPointEnvironment(BaseModel, JinjaProcessorMixin):
    name = models.CharField(max_length=20, unique=True)
    root_path = models.CharField(max_length=200, unique=True)
    state_hash_id = models.CharField(max_length=50, null=True, blank=True,
                                     help_text='{{payload.entry.0.messaging.0.sender.id}}')
    value = JSONField(null=True, blank=True, default=dict)

    def get_value(self, **kwargs):
        return replace_jinga_tags_in_dict(self.value, kwargs)

    def __str__(self):
        return self.name


class BaseRequest(BaseModel, JinjaProcessorMixin):
    name = models.CharField(max_length=20, unique=True)
    method = models.CharField(choices=REQUEST_METHODS, max_length=10)

    class Meta:
        abstract = True


class AccessPoint(BaseRequest):
    slug = models.CharField(max_length=500, null=False, blank=False)
    path = models.CharField(max_length=200,help_text='Ex: ".*"')
    state_condition = models.CharField(max_length=100, null=True, blank=True,
                                       help_text='state.counter >= 13 # avalidation that returns True')

    env = models.ForeignKey(AccessPointEnvironment)
    response = JSONField(null=True, blank=True, default=dict)

    def __str__(self):
        return '%s' % str(self.name)

    def get_state_hash_id(self):
        return self.env.state_hash_id

    def get_state(self, params):
        # TODO: this code is almost replicated
        hash = self.get_state_hash_id()
        if hash:
            template = Template(hash)
            state_hash_id = template.render(**params)
            state = RequestState.objects.get(hash_id=state_hash_id)
            # state = RequestState.objects.filter(hash_id=state_hash_id).first()
            return state
        return None # TODO: None ???

    def get_env(self, **kwargs):
        return self.env.get_value(**kwargs)

    def check_condition(self, request, url_path):
        request_dict = {}
        request_dict['path'] = url_path
        request_dict['url_params'] = self.parse(request, url_path)
        request_dict['request_definition'] = self  # TODO: Try to remove
        try:
            request_payload = json.loads(request.body.decode('utf-8'))
        except:
            request_payload = {}
        request_dict['payload'] = request_payload

        state_params = {
            'request': request_dict,
            'env': self.get_env(request_payload=request_payload)
        }
        state = self.get_state(params=state_params)

        if not self.state_condition:
            return True
        elif not state and self.state_condition:
            return False
        else:
            env = Environment()
            expr = env.compile_expression(self.state_condition)
            result = expr(state=state.value)

            if result:
                return True
        return False

    def parse(self, request, url_path):
        pattern = re.compile(self.path)
        match = pattern.match(url_path)
        params = {
            'url_path_params': match.groupdict() if match else None,
            'url_query_params': request.GET
        }
        return params

    def process(self, request, url_path):
        request_dict = {}
        request_dict['path'] = url_path
        request_dict['url_params'] = self.parse(request, url_path)
        request_dict['request_definition'] = self # TODO: Try to remove
        try:
            request_payload = json.loads(request.body.decode('utf-8'))
        except:
            request_payload = {}
        request_dict['payload'] = request_payload

        execute_params = {
            'request': request_dict,
            'context': {},
            'env': self.get_env(request_payload=request_payload)
        }
        ap_request = AccessPointRequestExecution.objects.create(request_definition=self)
        ap_request.save()

        return ap_request.execute(execute_params)


class AccessPointRequestExecution(BaseRequestExecution):
    request_definition = models.ForeignKey(AccessPoint)
    state = models.ForeignKey(RequestState, null=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_state(self, params):
        # TODO: this code is almost replicated
        hash = self.request_definition.get_state_hash_id()
        if hash:
            template = Template(hash)
            state_hash_id = template.render(**params)
            self.state, created = RequestState.objects.get_or_create(hash_id=state_hash_id)

            # PATCH
            if created:
                self.state.value = {}
                self.state.save()

        return self.state

    def execute_reusable_requests(self, params):
        for req in self.request_definition.reusable_requests.all(): # TODO: make sure to orden this query
            params = req.execute(access_point_request=self, params=params)
        return params

    def execute(self, execute_params):
        execute_params['state'] = self.get_state(execute_params).value

        # Execute Operations and requests
        execute_params = self.request_definition.env.execute_pre_request_operation(execute_params)
        execute_params = self.request_definition.execute_pre_request_operation(execute_params)
        execute_params = self.execute_reusable_requests(execute_params)
        execute_params = self.request_definition.execute_post_request_operation(execute_params)
        execute_params = self.request_definition.env.execute_post_request_operation(execute_params)

        self.state.value = execute_params['state']
        self.state.save()
        return JsonResponse(replace_jinga_tags_in_dict(self.request_definition.response, execute_params))



def replace_jinga_tags(text, params):
    env = Environment(extensions=['jinja2.ext.with_', 'jinja2.ext.do'])
    return env.from_string(text).render(**params)


def replace_jinga_tags_in_dict(payload, params):
    text = json.dumps(payload)
    result = replace_jinga_tags(text, params)
    return json.loads(result)


class ReusableApiRequest(BaseRequest):
    url = models.CharField(max_length=500)
    payload = JSONField(null=True, blank=True, default=dict)

    def execute(self, access_point_request, params):
        # TODO: Replicated code
        req_exec_params = {
            'request_definition': self,
            'access_point_request': access_point_request
        }
        req_execution = ReusableApiRequestExecution.objects.create(**req_exec_params)
        return req_execution.execute(params)

    def __str__(self):
        return str(self.name)


# TODO: Highly Replicated Code
class ReusableApiRequestExecution(BaseRequestExecution):
    request_definition = models.ForeignKey(ReusableApiRequest, related_name='request_executions')
    access_point_request = models.ForeignKey(AccessPointRequestExecution, related_name='reusable_request_executions')

    def execute(self, params):
        # Execute Operations and requests
        params = self.request_definition.execute_pre_request_operation(params)
        url = replace_jinga_tags(self.request_definition.url, params)

        if self.request_definition.method == 'get':
            req = requests.get(url)
        elif self.request_definition.method == 'post':
            payload = replace_jinga_tags_in_dict(self.request_definition.payload, params)
            req = requests.post(url, json=payload)
        params['response'] = json.loads(req.content.decode('utf-8'))
        params = self.request_definition.execute_post_request_operation(params)

        return params


class AccessPointReusableRequest(BaseModel, JinjaProcessorMixin, SortableMixin):
    condition = models.TextField(blank=True, default='')
    # params = models.TextField(blank=True, default='')
    params = JSONField(null=True, blank=True, default=dict)
    access_point = models.ForeignKey(AccessPoint, related_name='reusable_requests')
    request_definition = models.ForeignKey(ReusableApiRequest)

    # ordering field
    access_point_order = models.PositiveIntegerField(default=0, editable=False, db_index=True)

    class Meta:
        ordering = ['access_point_order']

    def execute(self, access_point_request, params):
        if self.check_condition(params):
#            params['self_param'] = self.params
            params['self_param'] = replace_jinga_tags_in_dict(self.params, params)
            params = self.execute_pre_request_operation(params)
            params = self.request_definition.execute(access_point_request, params)
            params = self.execute_post_request_operation(params)
        return params

    def check_condition(self, params):
        if not self.condition:
            return True
        env = Environment()
        expr = env.compile_expression(self.condition)
        result = expr(**params)

        if result:
            return True
        return False

