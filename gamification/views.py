from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from datetime import timedelta
from .models import ActivityLog


@login_required  # Доступ только авторизованным
def profile_view(request):
    profile = request.user.patient_profile
    now = timezone.now()

    updated_program = []
    for idx, ex in enumerate(profile.training_program):
        last_activity = ActivityLog.objects.filter(
            user=request.user,
            exercise_name=ex['name'],
            status='success'
        ).order_by('-completed_at').first()

        is_locked = False
        wait_time = None
        if last_activity and last_activity.next_available_at > now:
            is_locked = True
            wait_time = last_activity.next_available_at - now

        ex['is_locked'] = is_locked
        ex['idx'] = idx
        updated_program.append(ex)

    return render(request, 'gamification/profile.html', {
        'profile': profile,
        'program': updated_program
    })


def exercise_detail_view(request, exercise_idx):
    profile = request.user.patient_profile
    # Достаем упражнение по индексу из нашего JSON списка
    try:
        exercise = profile.training_program[int(exercise_idx)]
    except (IndexError, ValueError):
        return redirect('profile')

    return render(request, 'gamification/exercise_detail.html', {
        'exercise': exercise,
        'idx': exercise_idx
    })


def complete_exercise_view(request, exercise_idx):
    if request.method == 'POST':
        profile = request.user.patient_profile
        exercise = profile.training_program[int(exercise_idx)]
        status = request.POST.get('status')

        now = timezone.now()

        interval_hours = 24 if "Разминка" in exercise['name'] else 48
        next_time = now + timedelta(hours=interval_hours)

        if status == 'failed':
            profile.strikes += 1
            profile.save()
        elif status == 'success':
            profile.current_progress += 0.05
            profile.save()

            ActivityLog.objects.create(
                user=request.user,
                exercise_name=exercise['name'],
                status='success',
                next_available_at=next_time
            )

        return redirect('profile')