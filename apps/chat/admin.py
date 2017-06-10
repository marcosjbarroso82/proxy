from django.contrib import admin

from apps.proxy_api.admin import AccessPointAdmin
from . import models


class ChatAccessPointAdmin(AccessPointAdmin):
    exclude = ('method', 'pre_request_operation', 'post_request_operation', 'path', 'slug', 'app', 'env',
               'response_type', 'response')


admin.site.register(models.FacebookChat, ChatAccessPointAdmin)
