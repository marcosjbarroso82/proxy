from rest_framework import serializers


from .models import Poll, Item



class ItemSerializer(serializers.ModelSerializer):
    count = serializers.SerializerMethodField()

    def get_count(self, obj):
        return obj.get_vote_count()

    class Meta:
        model = Item
        fields = '__all__'


class PollSerializer(serializers.ModelSerializer):
    items = ItemSerializer(many=True)

    class Meta:
        model = Poll
        fields = '__all__'


