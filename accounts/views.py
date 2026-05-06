from django.contrib.auth import logout
from rest_framework import viewsets, permissions, status, mixins
from rest_framework.response import Response
from rest_framework.decorators import action
from django.contrib.auth import authenticate, login
from .models import *
from accounts.serializers import *

class AuthViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
   queryset = User.objects.all()
   serializer_class = UserSerializer
   permission_classes = [permissions.AllowAny]
   
   def perform_create(self, serializer):
      """
      Overrides the default create behavior to use the custom
      create_user method (which handles password hashing).
      """
      User.objects.create_user(**serializer.validated_data)
   
   # def get_permissions(self):
   #    """
   #    Return the permissions according to actions triggered.
   #    """
   #    if self.action in ['login', 'create']:
   #       return [permissions.AllowAny()]
   #    return [permissions.IsAuthenticated()]
   
   @action(detail=False, methods=['post'])
   def login(self ,request) :
      """
      Custom action for user login.
      Return the user data after logging in.
      """
      email = request.data.get('email')
      password = request.data.get('password')
      
      user = authenticate(request, username=email, password=password)      
      if user is not None:
         login(request, user)
         self.is_logedin = True
         return Response ({"message": "Login successful", "user": UserSerializer(user).data}, status= status.HTTP_200_OK)
      return Response ({"message": "Invlaid credentials"}, status= status.HTTP_401_UNAUTHORIZED)


   @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
   def logout(self, request):
      """
      Custom action for user logout.
      """
      logout(request)
      return Response({"message": "Successfully logged out"}, status=status.HTTP_200_OK)