from django.db import models
from apps.proxy_api.models import AccessPoint, ProxyApp, AccessPointEnvironment



class FacebookChat(AccessPoint):
    class Meta:
        proxy = True

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.method = 'post'
        self.slug = 'fb'
        self.app = ProxyApp.objects.get(id=1)
        self.env = AccessPointEnvironment.objects.get(id=1)
        super().save(force_insert, force_update, using, update_fields)

