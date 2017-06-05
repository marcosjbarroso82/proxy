from django.db import models
from .base import BaseModel, BaseVariable, JinjaProcessorMixin
from ..utils import replace_jinga_tags
from ..fields import JSONTextField
from ..constants import JSON_KEY_VALUE_SCHEMA, JSON_INTERFACE_SCHEMA


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

import json
# TODO: Refactor To Environment or ProxyEnvinrment
class AccessPointEnvironment(BaseModel, JinjaProcessorMixin):
    name = models.CharField(max_length=20, unique=True)
    state_hash_id = models.CharField(max_length=50, null=True, blank=True,
                                     help_text='{{payload.entry.0.messaging.0.sender.id}}')
    interface = JSONTextField(null=True, blank=True, json_schema=JSON_INTERFACE_SCHEMA,
                                  help_text='TODO: Make key and value required')

    def check_conditions(self):
        for condition in self.conditions.all():
            if not condition.check_condition(env=self.env):
                return False
        return True

    def get_value(self, **kwargs):
        env = {}
        # params = json.loads(self.interface)
        # import ipdb; ipdb.set_trace()
        for param in json.loads(self.interface):
        # for param in self.interface_params.all():
            if param.get('required') and param.get('key') not in kwargs.keys():
                raise Exception("Missing Env Required Param")
            elif param.get('key') in kwargs.keys():
                env[param.get('key')] = replace_jinga_tags(kwargs[param.get('key')], kwargs)

        for variable in self.variables.all():
            env[variable.key] = replace_jinga_tags(variable.get_value(), kwargs)

        self.env = env
        return self.env

    def is_debug(self):
        return True  #TODO: Implemtent

    def __str__(self):
        return self.name




class EnvVariable(BaseVariable):
    env = models.ForeignKey('AccessPointEnvironment', related_name='variables')

    def get_value(self):
        if self.env.is_debug() and self.debug_value:
            return self.debug_value
        return self.value

    def __str__(self):
        return '%s-%s' % (self.env.name, self.key)


