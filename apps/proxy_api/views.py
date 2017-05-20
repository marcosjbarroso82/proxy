from django.shortcuts import render, HttpResponse
from django.http import JsonResponse
from .models import AccessPoint
from django.shortcuts import get_object_or_404
import json
import re


def proxy(request, root_path, slug=None, extra_params=None):
    """
    Ensayo para facebook
    """
    aps = AccessPoint.objects.filter(active=True, method=request.method.lower(), slug=slug, app__root_path=root_path)

    # if request.method == 'GET':
    #     response = request.GET['hub.challenge']
    #     return HttpResponse(response)
    payload = json.loads(request.body.decode('utf-8'))


    for ap in aps:
        if ap.is_valid and ap.check_condition(request=request, url_path=extra_params):
            return ap.process(request=request, url_path=extra_params)
    return JsonResponse({'message': 'No Access Point Found'})


def origina_proxy(request, slug=None, extra_params=None):
    ap = get_object_or_404(AccessPoint, slug=slug)
    response = ap.execute(request=request, url_path=extra_params)

    return response
