from django.shortcuts import render, redirect
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import RegisterSerializer, PatientProfileSerializer
from django.contrib.auth import authenticate, login
from django.contrib import messages
from .models import User, PatientProfile

# --- ПОЛИНА ЭТО ЗАГЛУШКА ТВОЕЙ ЧАСТИ ---

def generate_mock_smart_goal(profile):
    """Генерация программы с вшитыми уровнями прогрессии"""

    profile.target_value = (profile.baseline_value or 0) * 1.5
    profile.goal_text = (
        f"Цель: Увеличение дистанции ({profile.limitation_type}) "
        f"до {profile.target_value} {profile.baseline_unit} за 4 недели."
    )

    # Структура программы теперь содержит уровни внутри каждого упражнения
    profile.training_program = [
        {
            "name": "Разминка (суставная)",
            "description": "Подготовка целевых групп мышц",
            "progression": {
                "level_1": "10 мин (1-7 день)",
                "level_2": "12 мин (8-14 день)",
                "level_3": "15 мин (15-28 день)",
                "upgrade_every": "7 дней"
            }
        },
        {
            "name": f"Тренировка: {profile.limitation_type}",
            "description": f"Специальные упражнения для коррекции {profile.limitation_type}",
            "progression": {
                "level_1": "15 мин (1-10 день)",
                "level_2": "25 мин (11-20 день)",
                "level_3": "35 мин (21-28 день)",
                "upgrade_every": "10 дней"
            }
        },
        {
            "name": "Силовая выносливость",
            "description": "Удержание позы / статика",
            "progression": {
                "level_1": "3 повтора (1-14 день)",
                "level_2": "5 повторов (15-21 день)",
                "level_3": "8 повторов (22-28 день)",
                "upgrade_every": "7-10 дней"
            }
        }
    ]

    profile.save()

class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]  # Регистрация открыта для всех

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Регистрация прошла успешно"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SubmitAnketaView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request):
        profile = request.user.patient_profile
        serializer = PatientProfileSerializer(profile, data=request.data)
        if serializer.is_valid():
            serializer.save()
            # Вызов заглушки ИИ
            generate_mock_smart_goal(profile)
            return Response({
                "message": "Цель сформирована",
                "goal": profile.goal_text
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#---заглушка для отображения простых html и проверки логики бд---
def home_view(request):
    """Главная страница"""
    return render(request, 'core/home.html')


def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)
            return redirect('profile')
        else:
            messages.error(request, "Неверная почта или пароль")

    return render(request, 'core/login.html')

def register_view(request):
    """Страница регистрации [cite: 15-18]"""
    if request.method == 'POST':
        # Собираем данные из формы
        email = request.POST.get('email')
        password = request.POST.get('password')
        full_name = request.POST.get('full_name')
        age = request.POST.get('age')
        gender = request.POST.get('gender')

        # Создаем пользователя [cite: 137-143]
        user = User.objects.create_user(
            username=email, email=email, password=password,
            full_name=full_name, age=age, gender=gender
        )
        # Создаем профиль и логиним пользователя
        PatientProfile.objects.create(user=user)
        login(request, user)

        # После регистрации — сразу на анкету [cite: 192-195]
        return redirect('anketa')

    return render(request, 'core/register.html')


def anketa_view(request):
    """Страница заполнения анкеты [cite: 20-24, 178]"""
    if not request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        profile = request.user.patient_profile
        profile.diagnosis = request.POST.get('diagnosis')
        profile.diagnosis_detail = request.POST.get('diagnosis_detail')
        profile.limitation_type = request.POST.get('limitation_type')
        profile.baseline_value = float(request.POST.get('baseline_value'))
        profile.baseline_condition = request.POST.get('baseline_condition')
        profile.save()

        # Тут вызываем нашу заглушку ИИ
        generate_mock_smart_goal(profile)

        return render(request, 'core/anketa.html', {
            'profile': profile,
            'success': True
        })

    return render(request, 'core/anketa.html')

