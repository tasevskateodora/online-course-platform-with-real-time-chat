# accounts/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import User, Profile
from chat.models import UserChatSettings


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Автоматски креирај профил и чет поставки за нов корисник"""
    if created:

        Profile.objects.create(user=instance)


        UserChatSettings.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Зачувај го профилот кога се зачувува корисникот"""
    if hasattr(instance, 'profile'):
        instance.profile.save()

    if hasattr(instance, 'chat_settings'):
        instance.chat_settings.save()