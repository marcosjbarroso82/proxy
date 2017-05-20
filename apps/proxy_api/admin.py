from django.contrib import admin
from adminsortable.admin import NonSortableParentAdmin, SortableStackedInline, SortableTabularInline
from . import models


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


admin.site.register(models.AccessPoint, AccessPointAdmin)
admin.site.register(models.AccessPointEnvironment, AccessPointEnvironmentAdmin)
admin.site.register(models.ReusableApiRequest, BaseModelAdmin)
admin.site.register(models.AccessPointRequestExecution, BaseModelAdmin)
admin.site.register(models.ProxyApp, BaseModelAdmin)
