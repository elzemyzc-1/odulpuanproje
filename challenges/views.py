from django.shortcuts import render, get_object_or_404, redirect
from accounts.models import Challenge, ChallengeParticipation, ChallengeTask  # Challenge modelin accounts içindeyse
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from accounts.models import Goal

def challenge_list(request):
    today = timezone.now().date()
    challenges = Challenge.objects.filter(start_date__lte=today, end_date__gte=today, is_active=True)
    return render(request, 'challenges/challenge_list.html', {'challenges': challenges})


@login_required
def join_challenge(request, challenge_id):
    challenge = get_object_or_404(Challenge, id=challenge_id)

    # Katılım daha önce yoksa oluştur
    participation, created = ChallengeParticipation.objects.get_or_create(
        user=request.user,
        challenge=challenge
    )

    if created:
        for task in challenge.tasks.all():
            Goal.objects.create(
                user=request.user,
                title=task.title,
                description=task.description,
                points=task.points,
                completed=False,
                day_of_week=""  # veya istersen 'Pzt' gibi bir sabit
            )

    return redirect('challenge_list')
