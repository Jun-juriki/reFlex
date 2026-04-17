from django.shortcuts import render, redirect
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import RegisterSerializer, PatientProfileSerializer
from django.contrib.auth import authenticate, login
from django.contrib import messages
from .models import User, PatientProfile
from .ai_service import ai_service
from django.utils import timezone

# --- ПОЛИНА ЭТО ЗАГЛУШКА ТВОЕЙ ЧАСТИ ---

def generate_smart_goal(profile):
    """Генерация SMART-цели через ИИ-сервис"""
    print("🚀 Генерация SMART-цели...")

    goal_text = ai_service.generate_smart_goal(profile)

    # Рассчитываем целевое значение
    if not profile.target_value and profile.baseline_value:
        profile.target_value = profile.baseline_value * 1.5

    profile.goal_text = goal_text
    profile.goal_created_at = timezone.now()
    profile.is_goal_valid = True
    profile.is_achieved = False
    profile.current_progress = 0.0
    profile.strikes = 0
    profile.save()

    # Генерация программы тренировок
    generate_training_program(profile)

    return goal_text


def generate_training_program(profile):
    """Генерация программы тренировок через ИИ-сервис"""
    print("🏋️ Генерация программы тренировок...")
    program = ai_service.generate_exercise_program(profile)
    profile.training_program = program
    profile.save()
    return program


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
    
    if not request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        print("🔍 POST запрос получен!")  # И эту
        
        profile = request.user.patient_profile
    """Страница заполнения анкеты"""
    if not request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        profile = request.user.patient_profile

        # Сохраняем данные из формы
        profile.diagnosis = request.POST.get('diagnosis')
        profile.diagnosis_detail = request.POST.get('diagnosis_detail')
        profile.limitation_type = request.POST.get('limitation_type')
        profile.baseline_value = float(request.POST.get('baseline_value'))
        profile.baseline_condition = request.POST.get('baseline_condition')
        profile.target_days = int(request.POST.get('target_days', 28))
        profile.baseline_unit = request.POST.get('baseline_unit', 'м')
        profile.save()

        # Генерируем SMART-цель через ИИ
        generate_smart_goal(profile)

        return render(request, 'core/anketa.html', {
            'profile': profile,
            'success': True
        })

    return render(request, 'core/anketa.html')

