from rest_framework import serializers
from .models import Ad, ExchangeProposal
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'password']
        extra_kwargs = {
            'password': {'write_only': True},
            'username': {'required': True}
        }

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password']
        )
        Token.objects.create(user=user)
        return user


class AdSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')
    can_edit = serializers.SerializerMethodField()

    class Meta:
        model = Ad
        fields = [
            'id', 'user', 'title', 'description',
            'image_url', 'category', 'condition',
            'created_at', 'can_edit'
        ]
        read_only_fields = ['created_at', 'user']

    def get_can_edit(self, obj):
        request = self.context.get('request')
        return request and request.user == obj.user


class ExchangeProposalSerializer(serializers.ModelSerializer):
    ad_sender = serializers.PrimaryKeyRelatedField(queryset=Ad.objects.all())
    ad_receiver = serializers.PrimaryKeyRelatedField(queryset=Ad.objects.all())
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )

    class Meta:
        model = ExchangeProposal
        fields = [
            'id', 'ad_sender', 'ad_receiver',
            'comment', 'status', 'status_display',
            'created_at'
        ]
        read_only_fields = ['created_at']

    def validate(self, data):
        if data['ad_sender'].user == data['ad_receiver'].user:
            raise serializers.ValidationError(
                "Нельзя создавать предложения на свои же объявления"
            )
        return data