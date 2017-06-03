from django.db import models
from .base import BaseModel, BaseVariable, JinjaProcessorMixin, BaseRequest, BaseRequestExecution
from .request import RequestState
from ..utils import replace_jinga_tags, replace_jinga_tags_in_dict
from jinja2 import Template, Environment

import re
import json


class ProxyApp(models.Model):
    name = models.CharField(max_length=20, unique=True)
    root_path = models.CharField(max_length=200, unique=True)
    debug = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class AppVariable(BaseVariable):
    app = models.ForeignKey('ProxyApp', related_name='variables')

    def get_values(self):
        return dict((Item['key'], Item['value']) for Item in self.variables.all())

    def __str__(self):
        return '%s-%s' % (self.app.name, self.key)


# TODO: Refactor To Environment or ProxyEnvinrment
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
            env[variable.key] = replace_jinga_tags(variable.get_value, kwargs)

        self.env = env
        return self.env

    def __str__(self):
        return self.name


class EnvInterfaceParameter(models.Model):
    type = models.CharField(max_length=20, choices=[('jinja', 'jinja')])
    required = models.BooleanField(default=False)
    key = models.CharField(max_length=20)
    env = models.ForeignKey('AccessPointEnvironment', related_name='interface_params')

    def __str__(self):
        return '%s-%s' % (self.env.name, self.key)


class EnvVariable(BaseVariable):
    env = models.ForeignKey('AccessPointEnvironment', related_name='variables')

    def get_value(self):
        if self.env.is_debug() and self.debug_value:
            return self.debug_value
        return self.value

    def __str__(self):
        return '%s-%s' % (self.env.name, self.key)


