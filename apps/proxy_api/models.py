from django.db import models
from adminsortable.fields import SortableForeignKey
from adminsortable.models import SortableMixin
from .constants import REQUEST_METHODS
# from django.shortcuts import HttpResponse
from django.http import JsonResponse, HttpResponse
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


class ProxyApp(models.Model):
    name = models.CharField(max_length=20, unique=True)
    root_path = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.name


class AccessPointEnvParamValue(models.Model):
    key = models.ForeignKey('EnvInterfaceParameter')
    value = models.CharField(max_length=100)
    access_point = models.ForeignKey('AccessPoint', related_name='env_param_values')

class EnvInterfaceParameter(models.Model):
    type = models.CharField(max_length=20, choices=[('jinja', 'jinja'),])
    required = models.BooleanField(default=False)
    key = models.CharField(max_length=20)
    env = models.ForeignKey('AccessPointEnvironment', related_name='interface_params')

    def __str__(self):
        return '%s-%s' %(self.env.name, self.key)

class EnvVariable(models.Model):
    type = models.CharField(max_length=20, choices=[('jinja', 'jinja'), ])
    required = models.BooleanField(default=False) # Use it in check condition
    key = models.CharField(max_length=20)
    value = models.TextField()
    env = models.ForeignKey('AccessPointEnvironment', related_name='variables')

    def __str__(self):
        return '%s-%s' % (self.env.name, self.key)


class AccessPointEnvCondition(models.Model):
    type = models.CharField(max_length=20, choices=(('reg_exp', 'reg_exp'), ('jinja', 'jinja')))
    condition = models.TextField(help_text='{"re": "{{ env.re_msg_cond }}", "text": "{{ env.received_message }}" }')
    env = models.ForeignKey('AccessPointEnvironment', related_name='conditions')

    def check_condition(self, env):
        # TODO: Implement Jinja Condition
        if self.type == 'reg_exp':
            params = replace_jinga_tags(self.condition, {"env": env}).replace("\n", "") # TODO: Better sanitize
            params = json.loads(params)
            pattern = re.compile(params['re'])
            match = pattern.match(params['text'])
            if match:
                return True

        return False

class AccessPointEnvironment(BaseModel, JinjaProcessorMixin):
    name = models.CharField(max_length=20, unique=True)
    state_hash_id = models.CharField(max_length=50, null=True, blank=True,
                                     help_text='{{payload.entry.0.messaging.0.sender.id}}')

    def check_conditions(self):
        for condition in self.conditions.all():
            if not condition.check_condition(env=self.env):
                return False
        return True


    def get_value(self, **kwargs):
        env = {}
        for param in self.interface_params.all():
            if param.required and param.key not in kwargs.keys():
                raise Exception("Missing Env Required Param")
            elif param.key in kwargs.keys():
                env[param.key] = replace_jinga_tags(kwargs[param.key], kwargs)

        for variable in self.variables.all():
            env[variable.key] = replace_jinga_tags(variable.value, kwargs)

        self.env = env
        return self.env

    def __str__(self):
        return self.name


class BaseRequest(BaseModel, JinjaProcessorMixin):
    name = models.CharField(max_length=20, unique=True)
    method = models.CharField(choices=REQUEST_METHODS, max_length=10)

    class Meta:
        abstract = True


class AccessPoint(BaseRequest):
    active = models.BooleanField(default=False)
    app = models.ForeignKey(ProxyApp)
    env = models.ForeignKey(AccessPointEnvironment)
    slug = models.CharField(max_length=500, null=False, blank=False)
    path = models.CharField(max_length=200,default='.*', help_text='Ex: ".*"')
    state_condition = models.CharField(max_length=100, null=True, blank=True,
                                       help_text='state.counter >= 13 # avalidation that returns True')

    response_type = models.CharField(max_length=20, choices=(('text', 'text'), ('json', 'json')), default='text')
    response = models.TextField(null=True, blank=True)

    @property
    def is_valid(self):
        # Check all Required Env params are being provided
        if self.env:
            params_key_ids = self.env_param_values.all().values_list('key__id', flat=True)
            if self.env.interface_params.filter(required=True).exclude(id__in=params_key_ids):
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
        return None # TODO: None ???

    def get_env(self, **kwargs):
        params = kwargs.copy()
        for param in self.env_param_values.all():
            params[param.key.key] = param.value
        return self.env.get_value(**params)

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

        env_params = {}
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
            return JsonResponse(replace_jinga_tags_in_dict(json.loads(self.request_definition.response), execute_params))
        elif self.request_definition.response_type == 'text':
            return HttpResponse(replace_jinga_tags(self.request_definition.response, execute_params))


def replace_jinga_tags(text, params):
    try:
        env = Environment(extensions=['jinja2.ext.with_', 'jinja2.ext.do'])
        return env.from_string(text).render(**params)
    except:
        import ipdb; ipdb.set_trace()


def replace_jinga_tags_in_dict(payload, params):
    text = json.dumps(payload)
    result = replace_jinga_tags(text, params)
    return json.loads(result)


class ReusableApiRequest(BaseRequest):
    url = models.CharField(max_length=500)
    payload = JSONField(null=True, blank=True, default=dict)

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
    request_definition = models.ForeignKey(ReusableApiRequest, related_name='request_executions')
    access_point_request = models.ForeignKey(AccessPointRequestExecution, related_name='reusable_request_executions')

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
            payload = replace_jinga_tags_in_dict(self.request_definition.payload, params)
            req = requests.post(url, json=payload)
        params['response'] = json.loads(req.content.decode('utf-8'))
        print('response')
        print(req.status_code)
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


# class IncommingHttpHeader(models.Model):
#     key = models.CharField(max_length=50, blank=True, null=True)
#     value = models.CharField(max_length=300, blank=True, null=True)
#     incomming_request = models.ForeignKey('GralRequestLog', related_name='headers')

#
# class IncommingRequest(BaseModel):
#     url = models.CharField(max_length=300, null=True, blank=True)
#     path = models.CharField(max_length=300, null=True, blank=True)
#     method = models.CharField(max_length=10, null=True, blank=True)
#     body = models.TextField()
#     headers = models.TextField()
#     response_headers = models.TextField()
#     response_body = models.TextField()
