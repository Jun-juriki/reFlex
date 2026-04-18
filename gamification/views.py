from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from .models import ActivityLog, UserStats, Achievement, UserAchievement
from django.contrib import messages
import random

MOTIVATION_QUOTES = [
    "Ошибки — это доказательство того, что ты пытаешься. Не сдавайся!",
    "Один шаг назад не отменяет твоего прогресса. Завтра будет лучше!",
    "Главное — не скорость, а то, что ты не останавливаешься.",
    "Твое тело учится адаптироваться. Дай ему немного времени.",
    "Страйк — это просто сигнал, что сегодня нужно отдохнуть и восстановиться."
]

def check_achievements_and_quests(user):
    stats = user.stats
    profile = user.patient_profile

    # Проверка ачивок
    # У самурая есть путь
    if profile.goal_text:
        ach, _ = Achievement.objects.get_or_create(
            slug='start',
            defaults={
                'name': 'Начало пути',
                'icon': '🎯',
                'description': 'Вы сформулировали свою первую SMART-цель и встали на путь выздоровления.'
            }
        )
        UserAchievement.objects.get_or_create(user=user, achievement=ach)

    # Понедельник начинается в субботу
    success_count = ActivityLog.objects.filter(user=user, status='success').count()
    if success_count >= 1:
        ach, _ = Achievement.objects.get_or_create(
            slug='first_step',
            defaults={
                'name': 'Понедельник начинается в субботу',
                'icon': '👣',
                'description': 'Первая тренировка завершена! Главное — не останавливаться.'
            }
        )
        UserAchievement.objects.get_or_create(user=user, achievement=ach)

    # Мастер дисциплины
    if stats.current_streak >= 7:
        ach, _ = Achievement.objects.get_or_create(
            slug='streak_7',
            defaults={
                'name': 'Мастер дисциплины',
                'icon': '📅',
                'description': '7 дней тренировок подряд. Вашей дисциплине можно позавидовать!'
            }
        )
        UserAchievement.objects.get_or_create(user=user, achievement=ach)

def get_quests_progress(user):
    stats = user.stats
    success_count = ActivityLog.objects.filter(user=user, status='success').count()

    # Формируем список квестов с их прогрессом
    quests = [
        {
            "name": "Проведи 10 тренировок",
            "current": success_count,
            "goal": 10,
            "progress": min(int((success_count / 10) * 100), 100),
            "icon": "🏋️"
        },
        {
            "name": "Тренируйся 5 дней подряд",
            "current": stats.current_streak,
            "goal": 5,
            "progress": min(int((stats.current_streak / 5) * 100), 100),
            "icon": "🔥"
        },
        {
            "name": "Заработай первый уровень",
            "current": stats.total_xp,
            "goal": 1000,
            "progress": min(int((stats.total_xp / 1000) * 100), 100),
            "icon": "⭐"
        }
    ]
    return quests

@login_required
def profile_view(request):
    profile = request.user.patient_profile
    stats, _ = UserStats.objects.get_or_create(user=request.user)
    now = timezone.now()

    updated_program = []
    # Проверка наличия программы
    program_data = profile.training_program or []

    for idx, ex in enumerate(program_data):
        last_activity = ActivityLog.objects.filter(
            user=request.user,
            exercise_name=ex.get('name') or ex.get('type', 'Упражнение'),
            status='success'
        ).order_by('-completed_at').first()

        is_locked = False
        if last_activity and last_activity.next_available_at > now:
            is_locked = True

        ex_copy = ex.copy()
        ex_copy['is_locked'] = is_locked
        ex_copy['idx'] = idx
        updated_program.append(ex_copy)

    check_achievements_and_quests(request.user)
    return render(request, 'gamification/profile.html', {
        'profile': profile,
        'stats': stats,
        'program': updated_program,
        'achievements': UserAchievement.objects.filter(user=request.user),
        'quests': get_quests_progress(request.user)
    })


@login_required
def exercise_detail_view(request, exercise_idx):
    profile = request.user.patient_profile
    try:
        exercise = profile.training_program[int(exercise_idx)]
    except (IndexError, ValueError, TypeError):
        return redirect('profile')

    return render(request, 'gamification/exercise_detail.html', {
        'exercise': exercise,
        'idx': exercise_idx
    })


def update_user_gamification(user, is_success):
    stats, _ = UserStats.objects.get_or_create(user=user)
    profile = user.patient_profile
    today = timezone.now().date()

    if is_success:
        # 1. Начисляем XP
        stats.total_xp += 100

        # 2. Логика Стриков (дней подряд)
        if stats.last_activity_date == today - timezone.timedelta(days=1):
            stats.current_streak += 1
        elif stats.last_activity_date != today:
            stats.current_streak = 1

        if stats.current_streak > stats.max_streak:
            stats.max_streak = stats.current_streak

        stats.last_activity_date = today

        # 3. Расчет уровня
        stats.level = (stats.total_xp // 1000) + 1

        # 4. Расчет прогресса по формуле
        if profile.target_value and profile.baseline_value:
            baseline = profile.baseline_value
            target = profile.target_value
            stats.current_value = (stats.current_value or baseline) + 0.05

            # Формула: (текущее - старт) / (цель - старт)
            progress = (stats.current_value - baseline) / (target - baseline)
            stats.current_progress = min(max(progress, 0.0), 1.0)

    check_achievements_and_quests(user)
    stats.save()


@login_required
def complete_exercise_view(request, exercise_idx):
    """Обработчик нажатия кнопок Выполнил/Не справился"""
    if request.method == 'POST':
        profile = request.user.patient_profile

        try:
            exercise = profile.training_program[int(exercise_idx)]
        except (IndexError, ValueError, TypeError):
            return redirect('profile')

        status = request.POST.get('status')
        is_success = (status == 'success')

        if status == 'failed':
            profile.strikes += 1
            profile.save()
            update_user_gamification(request.user, is_success=False)
            messages.warning(request, random.choice(MOTIVATION_QUOTES))

        elif status == 'success':
            # Обновляем глобальные статы
            update_user_gamification(request.user, is_success=True)

            # Логируем время для блокировки кнопки (на 24 часа)
            ActivityLog.objects.create(
                user=request.user,
                exercise_name=exercise.get('name') or exercise.get('type'),
                status='success',
                next_available_at=timezone.now() + timezone.timedelta(hours=24)
            )

        return redirect('profile')
    return redirect('profile')