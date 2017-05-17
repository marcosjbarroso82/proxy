from django.conf.urls import url
from django.views.decorators.csrf import csrf_exempt
from . import views

urlpatterns = [
    url(r'^(?P<root_path>[a-zA-Z0-9_-]*)/(?P<slug>\w+)/(?P<extra_params>.*)$',
        csrf_exempt(views.proxy), name='proxy'),
    ]

