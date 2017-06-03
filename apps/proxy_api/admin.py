from django.contrib import admin
from adminsortable.admin import NonSortableParentAdmin, SortableStackedInline, SortableTabularInline
from . import models
from django.core.urlresolvers import reverse
from django.contrib.contenttypes.models import ContentType
from django.core import urlresolvers

from django.forms import Textarea
from django.db.models import TextField


class AccessPointEnvConditionInline(admin.StackedInline):
    formfield_overrides = {TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 40})}, }
    model = models.AccessPointEnvCondition
    extra = 0


class EnvVariableInline(admin.TabularInline):
    formfield_overrides = {TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 40})}, }
    model = models.EnvVariable
    extra = 0


class AccessPointReusableRequestInline(SortableTabularInline):
    formfield_overrides = {TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 40})}, }
    model = models.AccessPointReusableRequest
    extra = 0
    exclude = ('log',)
    readonly_fields = ('is_valid', 'edit')

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


class AccessPointEnvParamValueInline(admin.TabularInline):
    formfield_overrides = {TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 40})}, }
    model = models.AccessPointEnvParamValue
    extra = 0


class AccessPointAdmin(NonSortableParentAdmin):
    formfield_overrides = {TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 40})}, }
    exclude = ('log',)
    readonly_fields = ['is_valid',]

    inlines = [AccessPointEnvParamValueInline, AccessPointReusableRequestInline]


class EnvInterfaceParameterInline(admin.TabularInline):
    formfield_overrides = {TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 40})}, }
    model = models.EnvInterfaceParameter
    extra = 0


class AccessPointEnvironmentAdmin(admin.ModelAdmin):
    formfield_overrides = {TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 40})}, }
    exclude = ('log',)
    inlines = [EnvVariableInline, EnvInterfaceParameterInline, AccessPointEnvConditionInline]

class BaseModelAdmin(admin.ModelAdmin):
    formfield_overrides = {TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 40})}, }

class IncommingRequestAdmin(BaseModelAdmin):
    list_display = ['pk', 'created_at']

    readonly_fields = ('replay',)

    def replay(self, obj):
        # return 'asdf'
        link = '<a href="%s">replay</a>'
        return link % reverse('replay_request', kwargs={'request_pk':obj.pk})
    replay.allow_tags = True


class RequestReusableInterfaceParameterInline(admin.TabularInline):
    model = models.RequestReusableInterfaceParameter
    extra = 0


class ReusableApiRequestAdmin(BaseModelAdmin):
    inlines = [RequestReusableInterfaceParameterInline]


class RequestReusableInterfaceParameterValueInline(admin.StackedInline):
    model = models.RequestReusableInterfaceParameterValue
    extra = 0

class AccessPointReusableRequestAdmin(BaseModelAdmin):
    inlines = [RequestReusableInterfaceParameterValueInline]


class AppVariableInline(admin.TabularInline):
    formfield_overrides = {TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 40})}, }
    model = models.AppVariable
    extra = 0

class ProxyAppAdmin(admin.ModelAdmin):
    inlines = [AppVariableInline,]

admin.site.register(models.AccessPoint, AccessPointAdmin)
admin.site.register(models.AccessPointEnvironment, AccessPointEnvironmentAdmin)
admin.site.register(models.ReusableApiRequest, ReusableApiRequestAdmin)
admin.site.register(models.AccessPointRequestExecution, BaseModelAdmin)
admin.site.register(models.ProxyApp, ProxyAppAdmin)
admin.site.register(models.AccessPointReusableRequest, AccessPointReusableRequestAdmin)
admin.site.register(models.IncommingRequest, IncommingRequestAdmin)
