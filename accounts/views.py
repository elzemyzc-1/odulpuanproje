from collections import defaultdict
from datetime import date, timedelta
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import LoginView
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django import forms

from .models import (
    Profile, Goal, Reward, TaskTemplate,
    DAY_CHOICES, GoalCompletion, RewardHistory
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
        fields = ['title', 'description', 'points', 'completed', 'day_of_week']

    def clean_day_of_week(self):
        days = self.cleaned_data['day_of_week']
        return ",".join(days)


class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'


@login_required
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
    return render(request, "accounts/profile.html")


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
            goal = form.save(commit=False)
            goal.user = request.user
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
    reward = Reward.objects.get(id=reward_id)
    user_profile = Profile.objects.get(user=request.user)

    if request.method == "POST":
        if user_profile.points >= reward.points_required:
            user_profile.points -= reward.points_required
            user_profile.save()
            RewardHistory.objects.create(user=request.user, reward=reward)
            messages.success(request, "Ödülü başarıyla aldın!")
        else:
            messages.error(request, "Yetersiz puan!")
        return redirect('reward_list')

    return render(request, 'accounts/confirm_redeem.html', {'reward': reward})


@login_required
def task_pool(request):
    tasks = TaskTemplate.objects.all()
    return render(request, 'accounts/task_pool.html', {'tasks': tasks})


@login_required
def add_task_as_goal(request, task_id):
    task = TaskTemplate.objects.get(id=task_id)
    Goal.objects.create(
        user=request.user,
        title=task.title,
        description=task.description,
        points=task.points,
        completed=False,
        day_of_week="Pzt,Sal,Çar,Per,Cum"
    )
    return redirect('goal_list')


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
    return render(request, "accounts/home.html")


@login_required
def profile_view(request):
    user = request.user
    today = timezone.now().date()

    labels = []
    data = []

    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        count = GoalCompletion.objects.filter(
            user=user,
            date=day,
            completed=True
        ).count()
        labels.append(day.strftime("%d.%m"))
        data.append(count)

    goals = Goal.objects.filter(user=user)

    return render(request, "profile.html", {
        "chart_labels": labels,
        "chart_data": data,
        "goals": goals
    })


@login_required
def delete_goal(request, goal_id):
    goal = get_object_or_404(Goal, id=goal_id, user=request.user)
    if request.method == "POST":
        goal.delete()
        return redirect('goal_list')
    return render(request, 'accounts/confirm_delete_goal.html', {'goal': goal})

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
