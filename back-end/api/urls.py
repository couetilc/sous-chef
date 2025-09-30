from django.urls import path, include
from django.contrib import admin
from . import views
from oauth2_provider import urls as oauth2_urls
from oauth2_provider.contrib.rest_framework import TokenHasReadWriteScope, TokenHasScope

urlpatterns = [
    path('', views.index, name="index"),
    path('admin/', admin.site.urls),
    path('o/', include(oauth2_urls)),
    path('users/', views.UserList.as_view()),
    path('users/<pk>/', views.UserDetails.as_view()),
    path('groups/', views.GroupList.as_view()),
]
