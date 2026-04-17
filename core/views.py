from django.shortcuts import render, redirect
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import RegisterSerializer, PatientProfileSerializer
from django.contrib.auth import login
from .models import User, PatientProfile

# --- ПОЛИНА ЭТО ЗАГЛУШКА ТВОЕЙ ЧАСТИ ---

def generate_mock_smart_goal(profile):
    """Имитация работы ИИ"""
    # Используем значения, которые ввел врач
    profile.target_value = (profile.baseline_value or 0) * 1.5
    profile.target_days = 28
    profile.goal_text = (
        f"SMART-цель: Увеличить показатель ({profile.limitation_type}) "
        f"с {profile.baseline_value} до {profile.target_value} {profile.baseline_unit} за 28 дней."
    )

    # Генерируем тестовую программу (именно этот список ищет цикл {% for %})
    profile.training_program = [
        {"type": "Разминка", "description": "Плавные движения 5 мин", "frequency": "Ежедневно"},
        {"type": "Основное", "description": f"Упражнения на {profile.limitation_type}", "frequency": "3 раза в неделю"},
        {"type": "Растяжка", "description": "Глубокое дыхание и статика", "frequency": "После тренировки"}
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