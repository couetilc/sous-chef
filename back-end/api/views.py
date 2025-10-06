from django.shortcuts import render
from django.http import HttpResponse
from rest_framework import generics, permissions
from django.contrib.auth.models import User, Group
from .serializers import UserSerializer, GroupSerializer

# Create your views here.
def index(request):
    return HttpResponse("<h1>Hello, World!</h1>")

class UserList(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = User.objects.all()
    serializer_class = UserSerializer

class UserDetails(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = User.objects.all()
    serializer_class = UserSerializer

class GroupList(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
