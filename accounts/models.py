from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    points = models.IntegerField(default=0)  # Kullanıcının ödül puanı

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

    def get_day_list(self):
        return self.day_of_week.split(',') if self.day_of_week else []

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

    def __str__(self):
        return f"{self.user.username} - {self.reward.name} - {self.redeemed_at.strftime('%Y-%m-%d %H:%M')}"



