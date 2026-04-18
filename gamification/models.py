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


class UserStats(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name='stats')
    total_xp = models.IntegerField(default=0)
    level = models.IntegerField(default=1)

    # (current - baseline) / (target - baseline)
    current_progress = models.FloatField(default=0.0)
    current_value = models.FloatField(null=True, blank=True)

    current_streak = models.IntegerField(default=0)
    max_streak = models.IntegerField(default=0)
    last_activity_date = models.DateField(null=True, blank=True)

    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Статистика {self.user.username}"


class Achievement(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    icon = models.CharField(max_length=10, default="🏆")

    def __str__(self):
        return self.name


class UserAchievement(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'achievement')  # Нельзя получить дважды