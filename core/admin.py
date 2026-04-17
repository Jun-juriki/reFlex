from django.contrib import admin
from .models import User, PatientProfile

# Регистрация кастомного пользователя
admin.site.register(User)

# Регистрация профиля пациента
@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    # Поля, которые мы выводим в список для удобства врача
    list_display = ('user', 'diagnosis', 'is_goal_valid', 'current_progress', 'strikes')
    # Поля, по которым можно кликнуть и перейти в редактирование
    list_display_links = ('user', 'diagnosis')