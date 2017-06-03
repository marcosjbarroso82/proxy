from django.db import models
from adminsortable.fields import SortableForeignKey
from adminsortable.models import SortableMixin
from ..constants import REQUEST_METHODS
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


class BaseVariable(models.Model):
    type = models.CharField(max_length=20, choices=[('jinja', 'jinja'), ])
    key = models.CharField(max_length=20)
    value = models.TextField()
    debug_value = models.TextField(null=True, blank=True)

    class Meta:
        abstract = True


class BaseRequest(BaseModel, JinjaProcessorMixin):
    name = models.CharField(max_length=20, unique=True)
    method = models.CharField(choices=REQUEST_METHODS, max_length=10)

    class Meta:
        abstract = True
