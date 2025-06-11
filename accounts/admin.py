from django.contrib import admin
from .models import Profile, Goal, Reward, RewardHistory, TaskTemplate, Challenge, ChallengeTask, Friend

admin.site.register(Profile)
admin.site.register(Goal)
admin.site.register(Reward)
admin.site.register(RewardHistory)
admin.site.register(TaskTemplate)
admin.site.register(Friend)

# Challenge içindeki görevleri inline olarak göstermek için
class ChallengeTaskInline(admin.TabularInline):
    model = ChallengeTask
    extra = 1

@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    list_display = ('title', 'start_date', 'end_date', 'is_active')
    inlines = [ChallengeTaskInline]



