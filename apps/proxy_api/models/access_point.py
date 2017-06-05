from django.db import models

from .base import BaseRequest, BaseRequestExecution, BaseModel
from .app import ProxyApp
from ..utils import replace_jinga_tags_in_dict, replace_jinga_tags
from jinja2 import Environment, Template
from jsonfield import JSONField
import re
import json
from ..constants import JSON_KEY_VALUE_SCHEMA
from ..fields import JSONTextField


class RequestState(BaseModel):
    hash_id = models.CharField(max_length=50)
    value = JSONField(null=True, blank=True, default=dict, help_text='jinja. Available vars: ')


class AccessPoint(BaseRequest):
    active = models.BooleanField(default=False)
    app = models.ForeignKey(ProxyApp)
    env = models.ForeignKey('AccessPointEnvironment')
    slug = models.CharField(max_length=500, null=False, blank=False)
    path = models.CharField(max_length=200, default='.*', help_text='Ex: ".*"')
    state_condition = models.CharField(max_length=100, null=True, blank=True,
                                       help_text='state.counter >= 13 # avalidation that returns True')
    response_type = models.CharField(max_length=20, choices=(('text', 'text'), ('json', 'json')), default='text')
    response = models.TextField(null=True, blank=True)
    json_env_params = JSONTextField(null=True, blank=True, json_schema=JSON_KEY_VALUE_SCHEMA,
                                  help_text='TODO: Make key and value required')

    @property
    def is_valid(self):
        # Check all Required Env params are being provided
        if self.env and self.env.interface:
            try:
                param_values = json.loads(self.json_env_params)
            except:
                param_values = []
            env_interface = json.loads(self.env.interface)
            for param in env_interface:
                # param = env_interface[0]
                if param.get('required'):
                    found_required_param = False
                    for value in param_values:
                        value = param_values[0]
                        if value.get('key') == param.get('key'):
                            if value.get('value'):
                                found_required_param = True
                                break
                    if not found_required_param:
                        return False

        for reusable_request in self.reusable_requests.all():
            if not reusable_request.is_valid():
                return False
        return True

    def __str__(self):
        return '%s' % str(self.name)

    def get_state_hash_id(self):
        return self.env.state_hash_id

    def get_state(self, params):
        hash = self.get_state_hash_id()
        if hash:
            template = Template(hash)
            state_hash_id = template.render(**params)
            try:
                state = RequestState.objects.get(hash_id=state_hash_id)
            except RequestState.DoesNotExist:
                state = None
            return state
        return None  # TODO: None ???

    def get_env(self, **kwargs):
        params = kwargs.copy()

        env_param_value = json.loads(self.json_env_params)
        for param in env_param_value:
            params[param.get('key')] = param.get('value') if not self.app.debug else param.get('debug_value')

        return self.env.get_value(**params)

    def check_condition(self, request, url_path):
        request_dict = dict()
        request_dict['path'] = url_path
        request_dict['url_params'] = self.parse(request, url_path)
        request_dict['request_definition'] = self  # TODO: Try to remove
        try:
            request_payload = request['body']
        except:
            request_payload = {}
        request_dict['payload'] = request_payload

        env_params = dict()
        env_params['request_payload'] = request_payload

        state_params = {
            'request': request_dict,
            'env': self.get_env(request_payload=request_payload)
        }

        # Check Env Condition
        if not self.env.check_conditions():
            return False

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
            'url_query_params': request['GET']
        }
        return params

    def process(self, request, url_path):
        request_dict = dict()
        request_dict['path'] = url_path
        request_dict['url_params'] = self.parse(request, url_path)
        request_dict['request_definition'] = self  # TODO: Try to remove
        request_payload = request['body']
        request_dict['payload'] = request_payload

        execute_params = {
            'request': request_dict,
            'context': {},
            'env': self.get_env(request_payload=request_payload)
        }
        ap_request = AccessPointRequestExecution.objects.create(request_definition=self)
        ap_request.save()

        return ap_request.execute(execute_params)


class AccessPointEnvCondition(models.Model):
    type = models.CharField(max_length=20, choices=(('reg_exp', 'reg_exp'), ('jinja', 'jinja(no implementado)')))
    condition = models.TextField(help_text='{"re": "{{ env.re_msg_cond }}", "text": "{{ env.received_message }}" }')
    env = models.ForeignKey('AccessPointEnvironment', related_name='conditions')

    def check_condition(self, env):
        # TODO: Implement Jinja Condition
        if self.type == 'reg_exp':
            params = replace_jinga_tags(self.condition, {"env": env}).replace("\n", "")  # TODO: Better sanitize
            params = json.loads(params)
            pattern = re.compile(params['re'])
            match = pattern.match(params['text'])
            if match:
                return True

        return False


class AccessPointEnvParamValue(models.Model):
    key = models.ForeignKey('EnvInterfaceParameter')
    value = models.CharField(max_length=100)
    access_point = models.ForeignKey('AccessPoint', related_name='env_param_values')


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
        for req in self.request_definition.reusable_requests.all():  # TODO: make sure to orden this query
            params = req.execute(access_point_request=self, params=params)
        return params

    def execute(self, execute_params):
        try:
            execute_params['state'] = self.get_state(execute_params).value
        except:
            # PATCH: if no state is tracked...
            execute_params['state'] = {}

        # Execute Operations and requests
        execute_params = self.request_definition.env.execute_pre_request_operation(execute_params)
        execute_params = self.request_definition.execute_pre_request_operation(execute_params)
        execute_params = self.execute_reusable_requests(execute_params)
        execute_params = self.request_definition.execute_post_request_operation(execute_params)
        execute_params = self.request_definition.env.execute_post_request_operation(execute_params)

        # PATCH: Don't save state if none is tracked
        if self.request_definition.get_state_hash_id():
            self.state.value = execute_params['state']
            self.state.save()

        if self.request_definition.response_type == 'json':
            return replace_jinga_tags_in_dict(json.loads(self.request_definition.response), execute_params)
        elif self.request_definition.response_type == 'text':
            return replace_jinga_tags(self.request_definition.response, execute_params)


