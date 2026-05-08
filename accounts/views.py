"""
Views for handling user authentication and profile management.

This module provides the AuthViewSet which consolidates registration,
login, logout, and profile operations into a single endpoint set.
"""
from django.contrib.auth import logout, authenticate, login
from django.middleware.csrf import get_token
from rest_framework import viewsets, permissions, status, mixins
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers
from .models import User
from accounts.serializers import UserSerializer, UserUpdateSerializer


class AuthViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """
    ViewSet for authentication operations: register, login, logout, and profile management.
    
    This viewset handles:
    - User registration (POST /auth/)
    - Login (POST /auth/login/)
    - Logout (GET/POST /auth/logout/)
    - Current User Profile (GET /auth/me/)
    - Profile Update (PATCH /auth/update_profile/)
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="User Registration",
        description="Register a new user and return user data with a CSRF token.",
        responses={201: inline_serializer('RegisterResponse', {'user': UserSerializer(), 'csrf_token': serializers.CharField()})}
    )
    def create(self, request, *args, **kwargs):
        """
        Register a new user and return their data with a CSRF token.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.create_user(**serializer.validated_data)
        
        # Optionally auto-login the user here or just return the token
        return Response({
            'user': UserSerializer(user).data,
            'csrf_token': get_token(request)
        }, status=status.HTTP_201_CREATED)

    @extend_schema(
        summary="User Login",
        description="Authenticates a user by email and password and establishes a session.",
        request=inline_serializer('LoginRequest', {'email': serializers.EmailField(), 'password': serializers.CharField()}),
        responses={200: inline_serializer('LoginResponse', {'message': serializers.CharField(), 'user': UserSerializer(), 'csrf_token': serializers.CharField()})}
    )
    @action(detail=False, methods=['post'])
    def login(self, request):
        """
        Authenticate a user by email and password and start a session.
        
        Expected Data:
            email (str): The user's email.
            password (str): The user's password.
            
        Returns:
            Response: Success message, user data, and CSRF token.
        """
        email = request.data.get('email')
        password = request.data.get('password')

        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            return Response(
                {
                    'message': 'Login successful', 
                    'user': UserSerializer(user).data,
                    'csrf_token': get_token(request)
                },
                status=status.HTTP_200_OK,
            )
        return Response({'message': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

    @extend_schema(
        summary="User Logout",
        description="Terminates the current authenticated user's session.",
        request=None, 
        responses={200: inline_serializer('LogoutResponse', {'message': serializers.CharField()})}
    )
    @action(detail=False, methods=['get', 'post'], permission_classes=[permissions.IsAuthenticated])
    def logout(self, request):
        """
        End the current user session.
        
        Requires Authentication.
        
        Returns:
            Response: Successfully logged out message.
        """
        logout(request)
        return Response({'message': 'Successfully logged out'}, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Get Current Profile",
        description="Returns the profile data of the currently authenticated user including CSRF token.",
        responses={200: inline_serializer('ProfileResponse', {'id': serializers.IntegerField(), 'email': serializers.EmailField(), 'first_name': serializers.CharField(), 'last_name': serializers.CharField(), 'currency': serializers.CharField(), 'language': serializers.CharField(), 'csrf_token': serializers.CharField()})}
    )
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        """
        Return the profile data and current CSRF token.
        
        Requires Authentication.
        """
        serializer = self.get_serializer(request.user)
        return Response({
            **serializer.data,
            'csrf_token': get_token(request)
        })

    @extend_schema(
        summary="Update Profile",
        description="Allows partial updates to the authenticated user's profile (name, currency, language).",
        request=UserUpdateSerializer, 
        responses=UserSerializer
    )
    @action(detail=False, methods=['patch'], permission_classes=[permissions.IsAuthenticated])
    def update_profile(self, request):
        """
        Partially update the authenticated user's profile.
        
        Allows changing first_name, last_name, currency, and language.
        
        Returns:
            Response: Updated profile data or validation errors.
        """
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(UserSerializer(request.user).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)