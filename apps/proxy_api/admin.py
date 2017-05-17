from django.contrib import admin
from adminsortable.admin import NonSortableParentAdmin, SortableStackedInline
from . import models



class AccessPointReusableRequestInline(SortableStackedInline):
    model = models.AccessPointReusableRequest
    extra = 0
    exclude = ('log',)


class AccessPointAdmin(NonSortableParentAdmin):
    exclude = ('log',)
    inlines = [AccessPointReusableRequestInline]


admin.site.register(models.AccessPoint, AccessPointAdmin)
admin.site.register(models.AccessPointEnvironment, admin.ModelAdmin)
admin.site.register(models.ReusableApiRequest, admin.ModelAdmin)
