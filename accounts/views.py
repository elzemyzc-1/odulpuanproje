from collections import defaultdict
from datetime import date, timedelta
import random 
import string
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import LoginView
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django import forms
from django.views.decorators.http import require_POST
from django.db import models
from dateutil.relativedelta import relativedelta
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password

from .models import (
    Profile, Goal, Reward, TaskTemplate,
    DAY_CHOICES, GoalCompletion, RewardHistory, DailyBonusHistory, Challenge, ChallengeParticipation, Friend
)
from .forms import ProfileUpdateForm, CustomPasswordChangeForm


class GoalForm(forms.ModelForm):
    day_of_week = forms.MultipleChoiceField(
        choices=DAY_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Hedef Günleri"
    )

    class Meta:
        model = Goal
        fields = ['title', 'description', 'points', 'completed']


class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'


def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            Profile.objects.create(user=user)
            return redirect("login")
    else:
        form = UserCreationForm()
    return render(request, "accounts/register.html", {"form": form})


@login_required
def profile(request):
    user = request.user
    try:
        week_offset = int(request.GET.get('week_offset', 0))
    except ValueError:
        week_offset = 0

    today = timezone.now().date()
    current_date = today + timedelta(days=7 * week_offset)
    days_since_monday = current_date.weekday()
    week_start = current_date - timedelta(days=days_since_monday)
    week_end = week_start + timedelta(days=6)

    labels = []
    data = []

    for i in range(7):
        day = week_start + timedelta(days=i)
        count = GoalCompletion.objects.filter(
            user=user,
            date=day,
            completed=True
        ).count()
        labels.append(day.strftime("%d.%m"))
        data.append(count)

    prev_week = week_offset - 1
    next_week = week_offset + 1

    day_names = ['Pzt', 'Sal', 'Çar', 'Per', 'Cum', 'Cmt', 'Paz']
    today_day_name = day_names[today.weekday()] if week_offset == 0 else None

    user_goals = Goal.objects.filter(user=user)
    completed_this_week = GoalCompletion.objects.filter(
        user=user,
        date__range=[week_start, week_end],
        completed=True
    ).values_list('goal_id', flat=True)

    incomplete_goals = []
    for goal in user_goals:
        if goal.id not in completed_this_week and goal.day_of_week:
            day = goal.day_of_week
            if day in day_names:
                is_today = (day == today_day_name)
                incomplete_goals.append({
                    'id': goal.id,
                    'title': goal.title,
                    'day': day,
                    'points': goal.points,
                    'description': goal.description,
                    'is_today': is_today
                })

    return render(request, "accounts/profile.html", {
        "chart_labels": labels,
        "chart_data": data,
        "goals": Goal.objects.filter(user=user),
        "incomplete_goals": incomplete_goals,
        "week_start": week_start.strftime("%d.%m.%Y"),
        "week_end": week_end.strftime("%d.%m.%Y"),
        "prev_week": prev_week,
        "next_week": next_week,
        "today_day_name": today_day_name
    })


@login_required
def add_points(request):
    if request.method == "POST":
        user_profile, _ = Profile.objects.get_or_create(user=request.user)
        user_profile.points += 10
        user_profile.save()
        return redirect('profile')
    return render(request, 'accounts/add_points.html')


@login_required
def add_goal(request):
    if request.method == "POST":
        form = GoalForm(request.POST)
        if form.is_valid():
            days = request.POST.getlist('day_of_week')
            for day in days:
                goal = Goal(
                    user=request.user,
                    title=form.cleaned_data['title'],
                    description=form.cleaned_data['description'],
                    points=form.cleaned_data['points'],
                    completed=form.cleaned_data['completed'],
                    day_of_week=day
                )
                goal.save()
            return redirect('goal_list')
    else:
        form = GoalForm()
    return render(request, 'accounts/add_goal.html', {'form': form})


@login_required
def goal_list(request):
    user_goals = Goal.objects.filter(user=request.user)
    today = date.today()
    completed_today = GoalCompletion.objects.filter(
        user=request.user,
        date=today,
        completed=True
    ).values_list('goal_id', flat=True)

    grouped_goals = defaultdict(list)
    for goal in user_goals:
        for day in goal.get_day_list():
            grouped_goals[day].append(goal)

    day_order = ['Pzt', 'Sal', 'Çar', 'Per', 'Cum', 'Cmt', 'Paz']
    ordered_goals = [(day, grouped_goals.get(day, [])) for day in day_order]

    return render(request, 'accounts/goal_list.html', {
        'grouped_goals': ordered_goals,
        'completed_today': completed_today
    })


@login_required
def complete_goal(request, goal_id):
    goal = get_object_or_404(Goal, id=goal_id, user=request.user)
    today = date.today()

    completion, created = GoalCompletion.objects.get_or_create(
        user=request.user,
        goal=goal,
        date=today
    )

    if not completion.completed:
        completion.completed = True
        completion.save()
        user_profile, _ = Profile.objects.get_or_create(user=request.user)
        user_profile.points += goal.points
        user_profile.save()

    return redirect('goal_list')


@login_required
def reward_list(request):
    rewards = Reward.objects.all()
    return render(request, 'accounts/reward_list.html', {'rewards': rewards})


@login_required
def redeem_reward(request, reward_id):
    reward = get_object_or_404(Reward, id=reward_id)
    profile = request.user.profile

    if RewardHistory.objects.filter(user=request.user, reward=reward).exists():
        messages.warning(request, "Bu ödülü zaten aldınız.")
        return redirect('reward_list')

    if profile.points >= reward.points_required:
        profile.points -= reward.points_required
        profile.save()

        unique_code = generate_coupon_code()
        RewardHistory.objects.create(user=request.user, reward=reward, coupon_code=unique_code)

        messages.success(request, f"{reward.name} ödülünü başarıyla aldınız!")
    else:
        messages.error(request, "Yeterli puanınız yok.")

    return redirect('reward_list')




@login_required
def task_pool(request):
    tasks = TaskTemplate.objects.all()
    from .models import DAY_CHOICES  # gün seçeneklerini ekliyoruz
    return render(request, 'accounts/task_pool.html', {
        'tasks': tasks,
        'DAY_CHOICES': DAY_CHOICES
    })


@login_required
def add_task_as_goal(request, task_id):
    task = get_object_or_404(TaskTemplate, id=task_id)

    if request.method == "POST":
        selected_days = request.POST.getlist("day_of_week")

        if not selected_days:
            messages.error(request, "Lütfen en az bir gün seçin.")
            return redirect('task_pool')

        for day in selected_days:
            Goal.objects.create(
                user=request.user,
                title=task.title,
                description=task.description,
                points=task.points,
                completed=False,
                day_of_week=day
            )

        messages.success(request, "Görev başarıyla seçtiğiniz günlere eklendi.")
        return redirect('task_pool')

    return redirect('task_pool')



@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=request.user)
        password_form = CustomPasswordChangeForm(user=request.user, data=request.POST)

        if form.is_valid() and password_form.is_valid():
            form.save()
            password_form.save()
            update_session_auth_hash(request, password_form.user)
            return redirect('profile')
    else:
        form = ProfileUpdateForm(instance=request.user)
        password_form = CustomPasswordChangeForm(user=request.user)

    return render(request, 'accounts/edit_profile.html', {
        'form': form,
        'password_form': password_form
    })


@login_required
def home(request):
    profile = Profile.objects.get(user=request.user)
    today = timezone.now().date()

    # Giriş bonusu sadece giriş için geçerli
    if profile.last_login_bonus != today:
        profile.points += 5
        profile.last_login_bonus = today
        profile.save()
        messages.success(request, "Bugünkü giriş bonusun (5 puan) hesabına eklendi!")

    return render(request, "accounts/home.html")



@login_required
def delete_goal(request, goal_id):
    goal = get_object_or_404(Goal, id=goal_id, user=request.user)
    if request.method == "POST":
        goal.delete()
    return redirect('goal_list')


@login_required
def add_goal_from_task(request, task_id):
    task = get_object_or_404(TaskTemplate, id=task_id)

    if request.method == "POST":
        form = GoalForm(request.POST)
        if form.is_valid():
            goal = form.save(commit=False)
            goal.user = request.user
            goal.title = task.title
            goal.description = task.description
            goal.points = task.points
            goal.save()
            return redirect('goal_list')    
    else:
        form = GoalForm()

    return render(request, 'accounts/add_goal_from_task.html', {
        'form': form,
        'task': task
    })


@require_POST
@login_required
def daily_bonus_view(request):
    import json
    today = date.today()
    profile = Profile.objects.get(user=request.user)

    if profile.daily_bonus_claimed == today:
        return JsonResponse({'success': False, 'message': '⏳ Bugün zaten çark bonusunu aldınız!'})

    # Gelen veriyi oku
    try:
        data = json.loads(request.body)
        points = data.get('points', 0)
        if points not in [100, 200, 300, 400, 500]:
            points = random.choice([100, 200, 300, 400, 500])
    except:
        points = random.choice([100, 200, 300, 400, 500])

    profile.points += points
    profile.daily_bonus_claimed = today
    profile.save()
    DailyBonusHistory.objects.create(user=request.user, points_earned=points)

    # Açılar — çarkın görsel sırasına göre:
    angle_map = {
        500: 0,
        100: 72,
        200: 144,
        300: 216,
        400: 288
    }

    return JsonResponse({'success': True, 'reward': points, 'angle': angle_map[points]})



@login_required
def check_daily_bonus_status(request):
    today = date.today()
    profile = Profile.objects.get(user=request.user)
    
    if profile.daily_bonus_claimed == today:
        # Bugün kazanılan puanı bul
        try:
            bonus_history = DailyBonusHistory.objects.filter(
                user=request.user, 
                created_at__date=today
            ).latest('created_at')
            points_earned = bonus_history.points_earned
        except DailyBonusHistory.DoesNotExist:
            points_earned = 0
            
        return JsonResponse({
            'already_claimed': True,
            'points_earned': points_earned
        })
    else:
        return JsonResponse({'already_claimed': False})

def challenge_list(request):
    today = timezone.now().date()
    # Debug: Tüm challenge'ları getir ve filtrele
    all_challenges = Challenge.objects.all()
    active_challenges = Challenge.objects.filter(is_active=True)
    date_filtered_challenges = Challenge.objects.filter(start_date__lte=today, end_date__gte=today, is_active=True)
    
    # Debug bilgileri için
    context = {
        'challenges': date_filtered_challenges,
        'total_challenges': all_challenges.count(),
        'active_challenges': active_challenges.count(),
        'date_filtered_count': date_filtered_challenges.count(),
        'today': today,
    }
    
    return render(request, 'challenges/challenge_list.html', context)

@login_required
def join_challenge(request, challenge_id):
    challenge = get_object_or_404(Challenge, id=challenge_id)

    # Katılım daha önce yoksa oluştur
    participation, created = ChallengeParticipation.objects.get_or_create(
        user=request.user,
        challenge=challenge
    )

    if created:
        # Challenge'ın görevlerini kullanıcının hedeflerine ekle
        for task in challenge.tasks.all():
            # Günleri Türkçe karşılıklarına çevir
            day_mapping = {
                'MON': 'Pzt',
                'TUE': 'Sal',
                'WED': 'Çar',
                'THU': 'Per',
                'FRI': 'Cum',
                'SAT': 'Cmt',
                'SUN': 'Paz'
            }
            
            Goal.objects.create(
                user=request.user,
                title=f"[{challenge.title}] {task.description}",  # Challenge adını başına ekle
                description=f"Challenge: {challenge.title} - {task.description}",
                points=task.points,
                completed=False,
                day_of_week=day_mapping.get(task.day, 'Pzt'),  # Günü Türkçe karşılığıyla kaydet
                start_date=challenge.start_date,
                end_date=challenge.end_date
            )
        
        messages.success(request, f"'{challenge.title}' hedef paketine başarıyla katıldınız! Hedefleriniz listeye eklendi.")
    else:
        messages.info(request, f"'{challenge.title}' hedef paketine zaten katılmışsınız.")

    return redirect('home')  # Ana sayfaya yönlendir

@login_required
def leaderboard(request):
    """Leaderboard sayfası - kullanıcıları puanlarına göre sıralar"""
    friend_ids = Friend.objects.filter(user=request.user).values_list('friend_id', flat=True)
    visible_user_ids = list(friend_ids) + [request.user.id]


    top_users = Profile.objects.select_related('user') \
    .filter(user__id__in=visible_user_ids) \
    .order_by('-points')

    
    # Mevcut kullanıcının sıralamasını bul
    user_profile = Profile.objects.get(user=request.user)
    user_rank = Profile.objects.filter(points__gt=user_profile.points).count() + 1
    
    # Haftalık en aktif kullanıcılar (bu hafta en çok hedef tamamlayanlar)
    today = timezone.now().date()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    
    weekly_completions = GoalCompletion.objects.filter(
        date__range=[week_start, week_end],
        completed=True,
        user__id__in=visible_user_ids  # SADECE arkadaşlar ve kendin
    ).values('user__username', 'user__profile__points').annotate(
        completions=models.Count('id')
    ).order_by('-completions')[:10]

    
    # Aylık istatistikler
    month_start = today.replace(day=1)
    month_end = month_start + relativedelta(months=1) - timedelta(days=1)

    monthly_completions = GoalCompletion.objects.filter(
        date__range=[month_start, month_end],
        completed=True,
        user__id__in=visible_user_ids  # SADECE arkadaşlar ve kendin
    ).values('user__username', 'user__profile__points').annotate(
        completions=models.Count('id')
    ).order_by('-completions')[:10]

    
    context = {
        'top_users': top_users,
        'user_rank': user_rank,
        'user_points': user_profile.points,
        'weekly_leaders': weekly_completions,
        'monthly_leaders': monthly_completions,
        'total_users': Profile.objects.count(),
    }
    
    return render(request, 'accounts/leaderboard.html', context)

from .models import Goal

@login_required
def shared_goals(request):
    print("✅ shared_goals VIEW çalıştı!")
    goals = Goal.objects.filter(is_shared=True).exclude(user=request.user)
    return render(request, 'accounts/shared_goals.html', {'goals': goals})


@require_POST
def copy_goal(request, goal_id):
    original_goal = get_object_or_404(Goal, id=goal_id, is_shared=True)

    # Yeni kullanıcıya özel kopyasını oluştur
    Goal.objects.create(
        user=request.user,
        title=original_goal.title,
        description=original_goal.description,
        points=original_goal.points,
        completed=False,
        is_shared=False  # kopya paylaşılan olarak gelmesin
    )

    messages.success(request, "Hedef listenize eklendi.")
    return redirect('shared_goals')

def password_reset_view(request):
    context = {}

    if request.method == "POST":
        username = request.POST.get("username")
        new_password = request.POST.get("new_password")

        try:
            user = User.objects.get(username=username)
            user.password = make_password(new_password)
            user.save()
            context["success"] = "Şifre başarıyla güncellendi."
        except User.DoesNotExist:
            context["error"] = "Kullanıcı bulunamadı."

    return render(request, "accounts/password_reset.html", context)


def redeem_reward(request, reward_id):
    reward = get_object_or_404(Reward, id=reward_id)
    profile = request.user.profile  # Kullanıcı profiline erişim

    # Ödül daha önce alındı mı?
    if RewardHistory.objects.filter(user=request.user, reward=reward).exists():
        messages.warning(request, "Bu ödülü zaten aldınız.")
        return redirect('reward_list')  # Ödül sayfasının URL adı

    if profile.points >= reward.points_required:
        # Puanı düşür
        profile.points -= reward.points_required
        profile.save()

        # Ödül geçmişine kaydet
        RewardHistory.objects.create(user=request.user, reward=reward)
        messages.success(request, f"{reward.name} ödülünü başarıyla aldınız!")
    else:
        messages.error(request, "Yeterli puanınız yok.")

    return redirect('reward_list')


@login_required
def my_rewards(request):
    user_rewards = RewardHistory.objects.filter(user=request.user).select_related('reward')
    return render(request, 'accounts/my_rewards.html', {'user_rewards': user_rewards})


@login_required
def users_list(request):
    all_users = User.objects.exclude(id=request.user.id)
    existing_friends = Friend.objects.filter(user=request.user).values_list('friend_id', flat=True)
    return render(request, 'accounts/users_list.html', {
        'all_users': all_users,
        'existing_friends': existing_friends,
    })


@login_required
def add_friend(request, user_id):
    friend = get_object_or_404(User, id=user_id)
    if friend != request.user:
        Friend.objects.get_or_create(user=request.user, friend=friend)
    return redirect('users_list') 

@login_required
def friend_list(request):
    friend_ids = Friend.objects.filter(user=request.user).values_list('friend_id', flat=True)
    friends = User.objects.filter(id__in=friend_ids)
    return render(request, 'accounts/friend_list.html', {'friends': friends})

