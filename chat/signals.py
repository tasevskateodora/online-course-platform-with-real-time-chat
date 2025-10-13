from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Message, MessageRead

@receiver(post_save, sender=Message)
def create_message_read_for_sender(sender, instance, created, **kwargs):
    """Автоматски означи ја пораката како прочитана за испраќачот"""
    if created:
        MessageRead.objects.create(
            message=instance,
            user=instance.sender
        )