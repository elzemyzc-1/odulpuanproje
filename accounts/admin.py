from django.contrib import admin
from .models import Profile, Goal, Reward, RewardHistory, TaskTemplate

admin.site.register(Profile)
admin.site.register(Goal)
admin.site.register(Reward)
admin.site.register(RewardHistory)
admin.site.register(TaskTemplate)
