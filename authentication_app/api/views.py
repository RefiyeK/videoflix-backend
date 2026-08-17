import django_rq
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.tokens import default_token_generator

from authentication_app.utils import send_activation_email
from .serializers import RegistrationSerializer


class RegisterView(APIView):
    """Register a new (inactive) user and queue the activation email."""

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        queue = django_rq.get_queue("default")
        queue.enqueue(send_activation_email, user.id)

        token = default_token_generator.make_token(user)
        return Response(
            {
                "user": {"id": user.id, "email": user.email},
                "token": token,
            },
            status=status.HTTP_201_CREATED,
        )
