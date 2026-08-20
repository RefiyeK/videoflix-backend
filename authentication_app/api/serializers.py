from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

GENERIC_REGISTRATION_ERROR = 'Please check your entries and try again.'


class RegistrationSerializer(serializers.ModelSerializer):
    """Validate registration data and create an inactive user."""

    confirmed_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'password', 'confirmed_password')
        extra_kwargs = {
            'password': {'write_only': True},
            # DRF auto-adds a UniqueValidator for the unique email
            # field; its message would reveal which addresses are
            # registered, turning this endpoint into an enumeration
            # oracle. Existence is checked silently in validate().
            'email': {'validators': []},
        }

    def validate(self, data):
        """Reject taken emails and mismatches with one shared message."""
        passwords_match = data['password'] == data['confirmed_password']
        email_is_free = not User.objects.filter(
            email__iexact=data['email']
        ).exists()
        if not (passwords_match and email_is_free):
            raise serializers.ValidationError(GENERIC_REGISTRATION_ERROR)
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


class PasswordResetSerializer(serializers.Serializer):
    """Validate the email address submitted for a password reset."""

    email = serializers.EmailField()


class PasswordConfirmSerializer(serializers.Serializer):
    """Validate the new password and its confirmation."""

    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        """Ensure the new password and its confirmation match."""
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError(
                {'new_password': 'Passwords do not match.'}
            )
        return data
