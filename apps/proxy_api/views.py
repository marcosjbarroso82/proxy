from django.shortcuts import render, HttpResponse, HttpResponseRedirect
from django.http import JsonResponse
from django.contrib.contenttypes.models import ContentType
from .models import AccessPoint,IncommingRequest
from django.shortcuts import get_object_or_404
from django.core import urlresolvers
import json
import re


def proxy(request, root_path, slug=None, extra_params=None):
    """
    Ensayo para facebook
    """
    incommint_request = IncommingRequest()

    incommint_request.parse(request, root_path, slug, extra_params)
    return incommint_request.process()


def origina_proxy(request, slug=None, extra_params=None):
    ap = get_object_or_404(AccessPoint, slug=slug)
    response = ap.execute(request=request, url_path=extra_params)

    return response


def replay_request(request, request_pk):
    req = IncommingRequest.objects.get(pk=request_pk)
    req.pk = None
    req.process()

    content_type = ContentType.objects.get_for_model(req.__class__)
    admin_url = urlresolvers.reverse("admin:%s_%s_change" % (content_type.app_label, content_type.model), args=(req.pk,))
    return HttpResponseRedirect(admin_url)
