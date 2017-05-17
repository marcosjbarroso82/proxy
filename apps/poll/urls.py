from django.conf.urls import url

from .views import vote, poll, result

urlpatterns = [
    url(r'^vote/(?P<poll_pk>\d+)/$', vote, name='poll_ajax_vote'),
    url(r'^poll/(?P<poll_pk>\d+)/$', poll, name='poll'),
    url(r'^result/(?P<poll_pk>\d+)/$', result, name='poll_result'),
]
