from django.db import models
from .base import BaseModel, BaseVariable, JinjaProcessorMixin
from ..utils import replace_jinga_tags
from ..fields import JSONTextField
from ..constants import JSON_KEY_VALUE_SCHEMA, JSON_INTERFACE_SCHEMA, JSON_KEY_ENV_VALUE_SCHEMA
import json


class ProxyApp(models.Model):
    name = models.CharField(max_length=20, unique=True)
    root_path = models.CharField(max_length=200, unique=True)
    debug = models.BooleanField(default=False)
    app_variables = JSONTextField(null=True, blank=True, json_schema=JSON_KEY_VALUE_SCHEMA,
                                  help_text='TODO: Make key and value required')

    def get_variables(self):
        temp_var = dict()
        for varialbe in self.app_variables:
            temp_var[varialbe['key']] = varialbe['value'] if not self.debug else varialbe['debug_value']
        return temp_var

    def __str__(self):
        return self.name


# TODO: Refactor To Environment or ProxyEnvinrment
class AccessPointEnvironment(BaseModel, JinjaProcessorMixin):
    name = models.CharField(max_length=20, unique=True)
    state_hash_id = models.CharField(max_length=50, null=True, blank=True,
                                     help_text='{{payload.entry.0.messaging.0.sender.id}}')
    interface = JSONTextField(null=True, blank=True, json_schema=JSON_INTERFACE_SCHEMA,
                                  help_text='TODO: Make key and value required')
    env_variables = JSONTextField(null=True, blank=True, json_schema=JSON_KEY_ENV_VALUE_SCHEMA,
                                  help_text='TODO: Make key and value required')

    def check_conditions(self):
        for condition in self.conditions.all():
            if not condition.check_condition(env=self.env):
                return False
        return True

    def get_value(self, **kwargs):
        env = {}
        for param in json.loads(self.interface):
            if param.get('required') and param.get('key') not in kwargs.keys():
                raise Exception("Missing Env Required Param")
            elif param.get('key') in kwargs.keys():
                env[param.get('key')] = replace_jinga_tags(kwargs[param.get('key')], kwargs)

        if self.env_variables:
            env_variables = json.loads(self.env_variables)
        else:
            env_variables = []

        for variable in env_variables:
            value = variable.get('value')  # TODO: Get also debug value
            env[variable.get('key')] = replace_jinga_tags(value, kwargs)

        self.env = env
        return self.env

    def is_debug(self):
        return True  #TODO: Implemtent

    def __str__(self):
        return self.name