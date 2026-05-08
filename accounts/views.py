"""
Views for handling user authentication and profile management.

This module provides the AuthViewSet for user registration and profile operations.
Authentication is handled via Token-based Auth for maximum simplicity.
"""
from django.contrib.auth import authenticate
from rest_framework import viewsets, permissions, status, mixins
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.authtoken.models import Token
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers
from .models import User
from accounts.serializers import UserSerializer, UserUpdateSerializer


class AuthViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """
    ViewSet for authentication operations: registration, login, and profile management.
    
    Authentication: Token Auth (Header: Authorization: Token <token>).
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['create', 'login']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    @extend_schema(
        summary="User Registration",
        description="Register a new user and return user data with an authentication token.",
        responses={201: inline_serializer('RegisterResponse', {'user': UserSerializer(), 'token': serializers.CharField()})}
    )
    def create(self, request, *args, **kwargs):
        """
        Register a new user and issue a token.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.create_user(**serializer.validated_data)
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            'user': UserSerializer(user).data,
            'token': token.key
        }, status=status.HTTP_201_CREATED)

    @extend_schema(
        summary="User Login",
        description="Authenticates a user and returns a persistent authentication token.",
        request=inline_serializer('LoginRequest', {'email': serializers.EmailField(), 'password': serializers.CharField()}),
        responses={200: inline_serializer('LoginResponse', {'token': serializers.CharField(), 'user': UserSerializer()})}
    )
    @action(detail=False, methods=['post'])
    def login(self, request):
        """
        Authenticate user and return their token.
        """
        email = request.data.get('email')
        password = request.data.get('password')

        user = authenticate(username=email, password=password)
        if user:
            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user': UserSerializer(user).data
            }, status=status.HTTP_200_OK)
        return Response({'error': 'Invalid Credentials'}, status=status.HTTP_401_UNAUTHORIZED)

    @extend_schema(
        summary="Get Current Profile",
        description="Returns the profile data of the currently authenticated user.",
        responses=UserSerializer
    )
    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        Return the profile data of the currently authenticated user.
        """
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @extend_schema(
        summary="Update Profile",
        description="Allows partial updates to the authenticated user's profile.",
        request=UserUpdateSerializer, 
        responses=UserSerializer
    )
    @action(detail=False, methods=['patch'])
    def update_profile(self, request):
        """
        Partially update the authenticated user's profile.
        """
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(UserSerializer(request.user).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)