from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from .models import ActivityLog, UserStats, Achievement, UserAchievement
from django.contrib import messages
import random
import json
from core.ai_service import ai_service  # Импорт ИИ-модуля

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

    # 25% цели
    if stats.current_progress >= 0.25:
        ach, _ = Achievement.objects.get_or_create(
            slug='quarter',
            defaults={
                'name': 'Первая четверть',
                'icon': '🎯',
                'description': '25% пути к цели пройдено!'
            }
        )
        UserAchievement.objects.get_or_create(user=user, achievement=ach)

    # 50% цели
    if stats.current_progress >= 0.5:
        ach, _ = Achievement.objects.get_or_create(
            slug='halfway',
            defaults={
                'name': 'Полпути',
                'icon': '💪',
                'description': '50% цели достигнуто! Ты на верном пути!'
            }
        )
        UserAchievement.objects.get_or_create(user=user, achievement=ach)

    # 100% цели
    if stats.current_progress >= 0.99:
        ach, _ = Achievement.objects.get_or_create(
            slug='complete',
            defaults={
                'name': 'Цель достигнута!',
                'icon': '🏆',
                'description': 'Поздравляем! Ты достиг своей цели!'
            }
        )
        UserAchievement.objects.get_or_create(user=user, achievement=ach)


def get_quests_progress(user):
    stats = user.stats
    success_count = ActivityLog.objects.filter(user=user, status='success').count()

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
            "name": "Заработай 1000 XP",
            "current": stats.total_xp,
            "goal": 1000,
            "progress": min(int((stats.total_xp / 1000) * 100), 100),
            "icon": "⭐"
        }
    ]
    return quests


def get_ai_advice(user):
    """Получение AI-совета на основе прогресса"""
    profile = user.patient_profile
    stats = user.stats
    
    # Рассчитываем метрики для совета
    progress_percent = stats.current_progress * 100
    
    if profile.goal_created_at and profile.target_days:
        days_elapsed = max(1, (timezone.now().date() - profile.goal_created_at.date()).days)
        expected_progress = (days_elapsed / profile.target_days) * 100 if profile.target_days > 0 else 0
        days_diff = expected_progress - progress_percent
    else:
        days_diff = 0
    
    # Генерируем совет через ИИ
    try:
        advice = ai_service.generate_advice(
            progress_percent=progress_percent,
            days_diff=days_diff,
            streak=stats.current_streak,
            level=stats.level
        )
    except Exception as e:
        print(f"Ошибка генерации AI-совета: {e}")
        advice = random.choice(MOTIVATION_QUOTES)
    
    return advice


def get_forecast(user):
    """Рассчитывает прогноз достижения цели"""
    profile = user.patient_profile
    stats = user.stats
    
    if not profile.baseline_value or not profile.target_value:
        return {
            "status": "📊 Заполните анкету для прогноза",
            "days_left": profile.target_days or 28,
            "probability": "medium"
        }
    
    baseline = profile.baseline_value
    target = profile.target_value
    current = baseline + (target - baseline) * stats.current_progress
    
    last_log = ActivityLog.objects.filter(
        user=user,
        status='success'
    ).order_by('-completed_at').first()
    
    if last_log and profile.goal_created_at:
        days_elapsed = max(1, (timezone.now().date() - profile.goal_created_at.date()).days)
        daily_rate = (current - baseline) / days_elapsed
        
        if daily_rate > 0:
            remaining = (target - current) / daily_rate
            days_left = int(remaining)
            
            # Определяем вероятность
            planned_rate = (target - baseline) / profile.target_days if profile.target_days > 0 else 0
            ratio = daily_rate / planned_rate if planned_rate > 0 else 0
            
            if ratio >= 0.9:
                probability = "high"
                prob_text = "Высокая 🎯"
            elif ratio >= 0.7:
                probability = "medium"
                prob_text = "Средняя 📈"
            else:
                probability = "low"
                prob_text = "Низкая ⚠️"
            
            if days_left < profile.target_days:
                status = f"🚀 Опережаешь график! Осталось ~{days_left} дней. Вероятность: {prob_text}"
            elif days_left > profile.target_days:
                status = f"⚠️ Нужно ускориться! Осталось ~{days_left} дней. Вероятность: {prob_text}"
            else:
                status = f"📊 Идёшь по плану! Осталось ~{days_left} дней. Вероятность: {prob_text}"
            
            return {
                "status": status,
                "days_left": days_left,
                "probability": probability
            }
    
    return {
        "status": "📊 Начинаем путь к цели! Выполняй упражнения ежедневно.",
        "days_left": profile.target_days or 28,
        "probability": "medium"
    }


def get_chart_data(user):
    profile = user.patient_profile
    stats = user.stats

    baseline = float(profile.baseline_value or 10.0)
    # Цель: либо из профиля, либо +50% от базы (для наглядности)
    target = float(profile.target_value or baseline * 1.5)
    days_target = profile.target_days or 30

    # 1. ПЛАН: Рассчитываем точки для КАЖДОГО дня (чтобы линия была сплошной)
    plan_points = []
    daily_step = (target - baseline) / days_target
    for day in range(days_target + 1):
        val = baseline + (daily_step * day)
        plan_points.append({"day": day, "value": round(val, 1)})

    # 2. ФАКТ: Распределяем прогресс по реальным датам тренировок
    actual_points = [{"day": 0, "value": baseline}]

    if profile.goal_created_at:
        start_date = profile.goal_created_at.date()
        logs = ActivityLog.objects.filter(user=user, status='success').order_by('completed_at')

        # Моделируем рост: каждая тренировка — это шаг вперед
        # В твоем update_user_gamification это +2% от разницы (target - baseline)
        current_val = baseline
        step_val = (target - baseline) * 0.02

        for log in logs:
            day_num = (log.completed_at.date() - start_date).days
            if 0 <= day_num <= days_target:
                current_val += step_val
                actual_points.append({
                    "day": day_num,
                    "value": round(min(current_val, target), 1)
                })

    return {
        "plan": plan_points,
        "actual": actual_points,
        "baseline": baseline,
        "target": round(target, 1),
        "unit": profile.baseline_unit or "ед."
    }


@login_required
def profile_view(request):
    profile = request.user.patient_profile
    stats, _ = UserStats.objects.get_or_create(user=request.user)
    now = timezone.now()
    xp_per_level = 1000  # Допустим, 1 уровень = 100 XP
    # Находим сколько XP набрано именно на текущем уровне
    xp_in_current_level = stats.total_xp % xp_per_level
    # Считаем процент заполнения шкалы для текущего уровня
    level_progress = (xp_in_current_level / xp_per_level) * 100

    updated_program = []
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
    
    # Получаем AI-совет
    ai_advice = get_ai_advice(request.user)
    
    # Получаем прогноз
    forecast = get_forecast(request.user)
    
    # Получаем данные для графика
    chart_data = get_chart_data(request.user)

    return render(request, 'gamification/profile.html', {
        'profile': profile,
        'stats': stats,
        'level_progress': level_progress,
        'program': updated_program,
        'achievements': UserAchievement.objects.filter(user=request.user),
        'quests': get_quests_progress(request.user),
        'ai_advice': ai_advice,
        'forecast': forecast,
        'chart_data': json.dumps(get_chart_data(request.user)),
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
        stats.total_xp += 10  # Изменил с 100 на 10 для баланса

        # 2. Логика Стриков (дней подряд)
        if stats.last_activity_date == today - timezone.timedelta(days=1):
            stats.current_streak += 1
        elif stats.last_activity_date != today:
            stats.current_streak = 1

        if stats.current_streak > stats.max_streak:
            stats.max_streak = stats.current_streak

        stats.last_activity_date = today

        # 3. Расчет уровня (каждые 100 XP)
        stats.level = (stats.total_xp // 100) + 1

        # 4. Расчет прогресса по формуле
        if profile.target_value and profile.baseline_value:
            baseline = profile.baseline_value
            target = profile.target_value
            stats.current_value = (stats.current_value or baseline) + (target - baseline) * 0.02  # +2% за тренировку

            # Формула: (текущее - старт) / (цель - старт)
            progress = (stats.current_value - baseline) / (target - baseline)
            stats.current_progress = min(max(progress, 0.0), 1.0)
            profile.current_progress = stats.current_progress * 100
            profile.save()

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
                exercise_name=exercise.get('name') or exercise.get('type', 'Упражнение'),
                status='success',
                next_available_at=timezone.now() + timezone.timedelta(hours=24)
            )
            
            messages.success(request, "🎉 Отлично! Ты получил +10 XP и продвинулся к цели!")

        return redirect('profile')
    return redirect('profile')