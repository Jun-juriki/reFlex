from django.db import models
from django.utils import timezone
from core.models import User

class ActivityLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    exercise_name = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=[('success', 'Выполнил'), ('failed', 'Не справился')])
    completed_at = models.DateTimeField(auto_now_add=True)
    next_available_at = models.DateTimeField() # Когда можно будет сделать снова

    def __str__(self):
        return f"{self.user.username} - {self.exercise_name} ({self.status})"