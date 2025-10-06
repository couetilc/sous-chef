from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name="index"),
    # Authentication endpoints
    path('register/', views.UserRegistrationView.as_view(), name='user-register'),
    path('login/', views.LoginView.as_view(), name='user-login'),
    path('logout/', views.LogoutView.as_view(), name='user-logout'),
    path('user/', views.CurrentUserView.as_view(), name='current-user'),
    path('csrf/', views.CSRFTokenView.as_view(), name='csrf-token'),
    # User and group management
    path('users/', views.UserList.as_view()),
    path('users/<pk>/', views.UserDetails.as_view()),
    path('groups/', views.GroupList.as_view()),
]
