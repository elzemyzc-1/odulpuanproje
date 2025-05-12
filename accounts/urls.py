from django.urls import path
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from . import views

urlpatterns = [
    # Şifre sıfırlama işlemleri
    path('password_reset/', PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', PasswordResetCompleteView.as_view(), name='password_reset_complete'),

    # Kullanıcı işlemleri
    path('profile/', views.profile, name='profile'),
    path('profile_edit/', views.edit_profile, name='edit_profile'),

    # Hedefler
    path('add_goal/', views.add_goal, name='add_goal'),
    path('goal_list/', views.goal_list, name='goal_list'),
    path('complete_goal/<int:goal_id>/', views.complete_goal, name='complete_goal'),

    # Ödüller
    path('rewards/', views.reward_list, name='reward_list'),
    path('redeem_reward/<int:reward_id>/', views.redeem_reward, name='redeem_reward'),

    # Görev havuzu
    path('tasks/', views.task_pool, name='task_pool'),
    path('tasks/add/<int:task_id>/', views.add_task_as_goal, name='add_task_as_goal'),

    # Ekstra puan kazanma
    path('add_points/', views.add_points, name='add_points'),

    path('', views.home, name='home'),

    path('goal/delete/<int:goal_id>/', views.delete_goal, name='delete_goal'),

    path('add_goal_from_task/<int:task_id>/', views.add_goal_from_task, name='add_goal_from_task'),
]
