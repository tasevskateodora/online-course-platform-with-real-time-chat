# accounts/models.py

from django.contrib.auth.models import AbstractUser
from django.db import models
from PIL import Image
import os


class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('student', 'Студент'),
        ('instructor', 'Инструктор'),
        ('admin', 'Администратор'),
    )

    user_type = models.CharField(
        max_length=20,
        choices=USER_TYPE_CHOICES,
        default='student'
    )
    bio = models.TextField(max_length=500, blank=True)
    profile_picture = models.ImageField(
        upload_to='profile_pics/',
        blank=True,
        null=True
    )
    birth_date = models.DateField(null=True, blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)


        if self.profile_picture and hasattr(self.profile_picture, 'path'):
            try:
                if os.path.exists(self.profile_picture.path):
                    img = Image.open(self.profile_picture.path)
                    if img.height > 300 or img.width > 300:
                        output_size = (300, 300)
                        img.thumbnail(output_size)
                        img.save(self.profile_picture.path)
            except Exception as e:
                pass

    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    location = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)
    linkedin = models.URLField(blank=True)
    github = models.URLField(blank=True)
    skills = models.TextField(blank=True, help_text="Одвоете ги вештините со запирка")

    def __str__(self):
        return f"Профил на {self.user.username}"