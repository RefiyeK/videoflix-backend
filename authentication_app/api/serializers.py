from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class RegistrationSerializer(serializers.ModelSerializer):
    """Validate registration data and create an inactive user."""

    confirmed_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'password', 'confirmed_password')
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def validate(self, data):
        """Ensure the password and its confirmation match."""
        if data['password'] != data['confirmed_password']:
            raise serializers.ValidationError(
                {'password': 'Passwords do not match.'}
            )
        return data

    def create(self, validated_data):
        """Create an inactive user; activation is done via email link."""
        validated_data.pop('confirmed_password')
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            is_active=False,
        )
        return user
