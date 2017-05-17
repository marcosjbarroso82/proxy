from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import AllowAny
from rest_framework.decorators import detail_route
from rest_framework.response import Response

from .models import Poll
from .serializers import PollSerializer
from .exceptions import PollVoteException


class PollModelViewSet(ModelViewSet):
    queryset = Poll.published.all()
    serializer_class = PollSerializer
    permission_classes = (AllowAny,)
    http_method_names = ['get', 'post']

    @detail_route(methods=['post'])
    def vote(self, request, *args, **kwargs):
        poll = self.get_object()
        value = request.data.get('value')
        vote = {
            'value': value,
            'ip': request.META.get('HTTP_X_FORWARDED_FOR',
                             request.META.get('HTTP_X_REAL_IP',
                                              request.META.get('REMOTE_ADDR', ''))),
            'user': request.user if request.user.is_authenticated() else None
        }
        try:
            poll.set_vote(**vote)
            return Response(PollSerializer(instance=poll).data, status=200)
        except PollVoteException as e:
            return Response({'value': e.to_dict() }, status=400)
