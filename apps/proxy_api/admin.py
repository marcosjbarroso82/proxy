from django.contrib import admin
from adminsortable.admin import NonSortableParentAdmin, SortableStackedInline, SortableTabularInline
from . import models
from .widgets import ListTextWidget
from django.core.urlresolvers import reverse
from django.contrib.contenttypes.models import ContentType
from django.core import urlresolvers

from django.forms import Textarea
from django.db.models import TextField, CharField
from .fields import JSONTextField

from json_editor.admin import JSONEditorWidget
import json
from django import forms
from .constants import JSON_KEY_VALUE_SCHEMA


class BaseModelAdmin(admin.ModelAdmin):
    formfield_overrides = {TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 40})}, }

    # TODO: Meter esto en un Mixin
    def formfield_for_dbfield(self, db_field, **kwargs):
        if isinstance(db_field, JSONTextField):
            kwargs['widget'] = JSONEditorWidget(schema=db_field.json_schema)
        return super(BaseModelAdmin, self).formfield_for_dbfield(db_field, **kwargs)


class AccessPointEnvConditionInline(admin.StackedInline):
    formfield_overrides = {TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 40})}, }
    model = models.AccessPointEnvCondition
    extra = 0


class AccessPointActionModelForm(forms.ModelForm):
    class Meta(object):
        model = models.AccessPointAction
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(AccessPointActionModelForm, self).__init__(*args, **kwargs)

        if self.instance.type:
            self.fields['params'].widget = JSONEditorWidget(schema=self.instance.get_params_json_schema())


class AccessPointActionInline(admin.StackedInline):
# class AccessPointActionInline(SortableTabularInline):
    model = models.AccessPointAction
    form = AccessPointActionModelForm
    extra = 0
    exclude = ('log',)

    def formfield_for_dbfield(self, db_field, **kwargs):
        if isinstance(db_field, JSONTextField):
            kwargs['widget'] = JSONEditorWidget(schema=db_field.json_schema)
        return super(AccessPointActionInline, self).formfield_for_dbfield(db_field, **kwargs)


class AccessPointReusableRequestInline(SortableTabularInline):
    formfield_overrides = {TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 40})}, }
    model = models.AccessPointReusableRequest
    extra = 0
    fields = ['request_definition', 'is_valid', 'edit', 'todo']
    exclude = ('log',)
    readonly_fields = ('is_valid', 'edit', 'todo')

    def edit(self, obj):
        if obj.pk:
            content_type = ContentType.objects.get_for_model(obj.__class__)
            admin_url = urlresolvers.reverse("admin:%s_%s_change" % (content_type.app_label, content_type.model),
                                             args=(obj.pk,))
            link = '<a href="%s" target="popup" >edit</a>'
            # return link % reverse('replay_request', kwargs={'request_pk':obj.pk})
            return link % admin_url
        return ''
    edit.allow_tags = True

    def todo(self, obj):
        return 'mostrar las condiciones, inlines y readonly' \
               '<br/>Dejar editable el request definition solo en el create'
    todo.allow_tags = True


class AccessPointModelForm(forms.ModelForm):
    class Meta(object):
        model = models.AccessPoint
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(AccessPointModelForm, self).__init__(*args, **kwargs)

        # schema = JSON_KEY_VALUE_SCHEMA.copy()
        schema = {
            "type": "array",
            "format": "table",
            "items": {
                "type": "object",
                "properties": {
                    "key": {
                        "type": "string", "propertyOrder": 1
                    },
                    "value": {
                        "type": "string", "propertyOrder": 2
                    },
                    "debug_value": {
                        "type": "string", "propertyOrder": 3
                    }
                }
            }
        }
        if self.instance.env and self.instance.env.interface:
            interface = json.loads(self.instance.env.interface)
            keys = []

            for param in interface:
                keys.append(param.get('key'))
            schema['items']['properties']['key']['enum'] = keys
        self.fields['json_env_params'].widget = JSONEditorWidget(schema=schema)
        # TODO: revisar esto


class AccessPointAdmin(NonSortableParentAdmin):
    form = AccessPointModelForm
    exclude = ('log',)
    readonly_fields = ['is_valid',]
    inlines = [AccessPointReusableRequestInline, AccessPointActionInline]


class AccessPointEnvironmentAdmin(BaseModelAdmin):
    formfield_overrides = {TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 40})}, }
    exclude = ('log',)
    inlines = [AccessPointEnvConditionInline,]


class IncommingRequestAdmin(BaseModelAdmin):
    list_display = ['pk', 'created_at']

    readonly_fields = ('replay',)

    def replay(self, obj):
        # return 'asdf'
        link = '<a href="%s">replay</a>'
        return link % reverse('replay_request', kwargs={'request_pk':obj.pk})
    replay.allow_tags = True


class ReusableApiRequestAdmin(BaseModelAdmin):
    # self.fields['char_field_with_list'].widget = ListTextWidget(data_list=_country_list, name='country-list')
    formfield_overrides = {CharField: {'widget': ListTextWidget(data_list=['aaa', 'bbb'], name='country-list') }, }


class AccessPointReusableRequestForm(forms.ModelForm):
    class Meta(object):
        model = models.AccessPointReusableRequest
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(AccessPointReusableRequestForm, self).__init__(*args, **kwargs)

        # schema = JSON_KEY_VALUE_SCHEMA.copy()
        schema = {
            "type": "array",
            "format": "table",
            "items": {
                "type": "object",
                "properties": {
                    "key": {
                        "type": "string", "propertyOrder": 1
                    },
                    "value": {
                        "type": "string", "propertyOrder": 2
                    },
                    "debug_value": {
                        "type": "string", "propertyOrder": 3
                    }
                }
            }
        }
        if self.instance.request_definition and self.instance.request_definition.interface:
            interface = json.loads(self.instance.request_definition.interface)
            keys = []

            for param in interface:
                keys.append(param.get('key'))
            schema['items']['properties']['key']['enum'] = keys
        self.fields['json_request_params'].widget = JSONEditorWidget(schema=schema)

class AccessPointReusableRequestAdmin(BaseModelAdmin):
    form = AccessPointReusableRequestForm


class ProxyAppAdmin(BaseModelAdmin):

    def formfield_for_dbfield(self, db_field, **kwargs):
        if isinstance(db_field, JSONTextField):
            kwargs['widget'] = JSONEditorWidget(schema=db_field.json_schema)
        return super(ProxyAppAdmin, self).formfield_for_dbfield(db_field, **kwargs)


admin.site.register(models.AccessPoint, AccessPointAdmin)
admin.site.register(models.AccessPointEnvironment, AccessPointEnvironmentAdmin)
admin.site.register(models.ReusableApiRequest, ReusableApiRequestAdmin)
admin.site.register(models.AccessPointRequestExecution, BaseModelAdmin)
admin.site.register(models.ProxyApp, ProxyAppAdmin)
admin.site.register(models.AccessPointReusableRequest, AccessPointReusableRequestAdmin)
admin.site.register(models.IncommingRequest, IncommingRequestAdmin)
