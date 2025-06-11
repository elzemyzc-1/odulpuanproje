from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone 
from django.utils.translation import gettext_lazy as _


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    points = models.IntegerField(default=0)
    last_login_bonus = models.DateField(null=True, blank=True)
    daily_bonus_claimed = models.DateField(null=True, blank=True)  

    def __str__(self):
        return f"{self.user.username} - {self.points} Puan"


DAY_CHOICES = [
    ('Pzt', 'Pazartesi'),
    ('Sal', 'Salı'),
    ('Çar', 'Çarşamba'),
    ('Per', 'Perşembe'),
    ('Cum', 'Cuma'),
    ('Cmt', 'Cumartesi'),
    ('Paz', 'Pazar'),
]

class Goal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    points = models.IntegerField(default=10)
    completed = models.BooleanField(default=False)
    day_of_week = models.CharField(max_length=255, blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    is_shared = models.BooleanField(default=False)


    def get_day_list(self):
        # Artık her hedef tek bir gün tutuyor, listeye çevirip döndür
        return [self.day_of_week] if self.day_of_week else []

    def __str__(self):
        return f"{self.user.username} - {self.title}"

class Reward(models.Model):
    name = models.CharField(max_length=255)  # Ödülün adı
    description = models.TextField(blank=True, null=True)  # Ödül açıklaması
    points_required = models.IntegerField()  # Ödülü almak için gereken puan

    def __str__(self):
        return f"{self.name} - {self.points_required} Puan"

class TaskTemplate(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    points = models.IntegerField(default=10)

    def __str__(self):
        return f"{self.title} ({self.points} Puan)"

class GoalCompletion(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    goal = models.ForeignKey(Goal, on_delete=models.CASCADE)
    date = models.DateField()  # Hangi gün tamamlandı
    completed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.goal.title} - {self.date} - {'Tamamlandı' if self.completed else 'Tamamlanmadı'}"


class RewardHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reward = models.ForeignKey(Reward, on_delete=models.CASCADE)
    redeemed_at = models.DateTimeField(auto_now_add=True)
    coupon_code = models.CharField(max_length=20, blank=True, null=True)  # 🎟️ Kişiye özel kupon

    class Meta:
        unique_together = ('user', 'reward')

    def __str__(self):
        return f"{self.user.username} - {self.reward.name} - {self.redeemed_at.strftime('%Y-%m-%d %H:%M')}"




class DailyBonusHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    points_earned = models.IntegerField()

    def __str__(self):
        return f"{self.user.username} - {self.points_earned} puan - {self.date}"


class Weekday(models.TextChoices):
    MONDAY = 'MON', _('Pazartesi')
    TUESDAY = 'TUE', _('Salı')
    WEDNESDAY = 'WED', _('Çarşamba')
    THURSDAY = 'THU', _('Perşembe')
    FRIDAY = 'FRI', _('Cuma')
    SATURDAY = 'SAT', _('Cumartesi')
    SUNDAY = 'SUN', _('Pazar')

class Challenge(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class ChallengeTask(models.Model):
    challenge = models.ForeignKey(Challenge, related_name='tasks', on_delete=models.CASCADE)
    day = models.CharField(max_length=3, choices=Weekday.choices)
    description = models.CharField(max_length=255)
    points = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.challenge.title} - {self.get_day_display()}: {self.description}"


class ChallengeParticipation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    challenge = models.ForeignKey('Challenge', on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'challenge')



class Friend(models.Model):
    user = models.ForeignKey(User, related_name='owner', on_delete=models.CASCADE)
    friend = models.ForeignKey(User, related_name='friend_of', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'friend')  # Aynı kişiyi birden çok kez ekleyemesin

    def __str__(self):
        return f"{self.user.username} -> {self.friend.username}"
