from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    email = models.EmailField(unique=True, verbose_name="Email")
    full_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="ФИО")
    age = models.PositiveIntegerField(blank=True, null=True, verbose_name="Возраст")

    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
    ]
    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES,
        blank=True,
        null=True,
        verbose_name="Пол"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    # Указываем, что email будет использоваться для входа вместо username
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email


class PatientProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='patient_profile',
        primary_key=True  # Делает id профиля равным id пользователя
    )
    diagnosis = models.TextField(
        null=True, blank=True,
        verbose_name="Диагноз (ввод врача)"
    )
    diagnosis_detail = models.TextField(
        blank=True,
        null=True,
        verbose_name="Уточнение/Анамнез"
    )
    limitation_type = models.TextField(
        null=True, blank=True,
        verbose_name="Тип ограничения (ввод врача)"
    )
    baseline_value = models.FloatField(null=True, blank=True)
    baseline_unit = models.CharField(
        null=True, blank=True,
        max_length=50,
        default='m',
        verbose_name="Единицы измерения"
    )
    baseline_condition = models.TextField(
        blank=True,
        null=True,
        verbose_name="Условия замера (например, с опорой)"
    )

    # Параметры, которые будут установлены или скорректированы ИИ
    target_value = models.FloatField(blank=True, null=True)
    target_unit = models.CharField(max_length=50, default='m')
    target_days = models.IntegerField(default=28)

    # Итоговая SMART-цель и программа
    goal_text = models.TextField(blank=True, null=True)
    goal_created_at = models.DateTimeField(auto_now_add=True)

    # JSON-хранилище для программы тренировок
    # Формат: [{"type": "...", "description": "...", "frequency": "..."}]
    training_program = models.JSONField(default=list, blank=True)

    # Статистика прогресса
    strikes = models.IntegerField(default=0)
    max_strikes = models.IntegerField(default=3)  # Порог, после которого цель сгорает
    is_goal_valid = models.BooleanField(default=True)  # Валидна ли цель сейчас
    current_progress = models.FloatField(default=0.0)
    is_achieved = models.BooleanField(default=False)
    achieved_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Профиль {self.user.username} - {self.diagnosis[:30]}..."
