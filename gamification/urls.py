from django.urls import path
from .views import profile_view, exercise_detail_view, complete_exercise_view

urlpatterns = [
    path('profile/', profile_view, name='profile'),
    path('exercise/<int:exercise_idx>/', exercise_detail_view, name='exercise_detail'),
    path('exercise/<int:exercise_idx>/complete/', complete_exercise_view, name='complete_exercise'),
]