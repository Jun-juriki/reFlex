from django.urls import path
from .views import home_view, register_view, anketa_view, login_view

urlpatterns = [
    path('', home_view, name='home'),
    path('register/', register_view, name='register'),
    path('anketa/', anketa_view, name='anketa'),
    path('login/', login_view, name='login'),
]