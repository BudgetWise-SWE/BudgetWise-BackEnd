from django.contrib.auth import logout, authenticate, login
from rest_framework import viewsets, permissions, status, mixins
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers
from .models import User
from accounts.serializers import UserSerializer, UserUpdateSerializer


class AuthViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """ViewSet for authentication operations: register, login, logout, profile."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        """Register a new user using the custom user manager."""
        User.objects.create_user(**serializer.validated_data)

    @extend_schema(
        request=inline_serializer('LoginRequest', {'email': serializers.EmailField(), 'password': serializers.CharField()}),
        responses={200: inline_serializer('LoginResponse', {'message': serializers.CharField(), 'user': UserSerializer()})}
    )
    @action(detail=False, methods=['post'])
    def login(self, request):
        """Authenticate a user by email and password and start a session."""
        email = request.data.get('email')
        password = request.data.get('password')

        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            return Response(
                {'message': 'Login successful', 'user': UserSerializer(user).data},
                status=status.HTTP_200_OK,
            )
        return Response({'message': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

    @extend_schema(request=None, responses={200: inline_serializer('LogoutResponse', {'message': serializers.CharField()})})
    @action(detail=False, methods=['get', 'post'], permission_classes=[permissions.IsAuthenticated])
    def logout(self, request):
        """End the current user session."""
        logout(request)
        return Response({'message': 'Successfully logged out'}, status=status.HTTP_200_OK)

    @extend_schema(responses=UserSerializer)
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        """Return the profile data of the currently authenticated user."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @extend_schema(request=UserUpdateSerializer, responses=UserSerializer)
    @action(detail=False, methods=['patch'], permission_classes=[permissions.IsAuthenticated])
    def update_profile(self, request):
        """Partially update the authenticated user's profile (name, currency, language)."""
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(UserSerializer(request.user).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)