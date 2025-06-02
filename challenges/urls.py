from django.urls import path
from . import views

urlpatterns = [
    path('haftalik-hedefler/', views.challenge_list, name='challenge_list'),
    path('katil/<int:challenge_id>/', views.join_challenge, name='join_challenge'),

]


