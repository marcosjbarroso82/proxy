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
    aps = AccessPoint.objects.filter(slug=slug, env__root_path=root_path)
    payload = json.loads(request.body.decode('utf-8'))
    text = payload['entry'][0]['messaging'][0]['message']['text']

    # r'asdfkjdlsfk
    # TODO: Seems that this filter is the other way around
    # aps = ap.filter(path__iregex=text) # handler

    for ap in aps:
        reg_exp = ap.path
        pattern = re.compile(reg_exp)
        match = pattern.match(text)

        # try:
        #     request_payload = json.loads(request.body.decode('utf-8'))
        # except:
        #     request_payload = {}

        if match and ap.check_condition(request=request, url_path=extra_params):
            return ap.process(request=request, url_path=extra_params)
        else:
            import ipdb; ipdb.set_trace()
    # pattern = re.compile('^([0-9]+)+$')
    #import ipdb; ipdb.set_trace()
    #ap = aps[0]
    return JsonResponse({'message': 'No Access Point Found'})


def origina_proxy(request, slug=None, extra_params=None):
    ap = get_object_or_404(AccessPoint, slug=slug)
    response = ap.execute(request=request, url_path=extra_params)

    return response
