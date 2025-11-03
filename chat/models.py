# chat/models.py

from django.db import models
from django.conf import settings
from courses.models import Course


class ChatRoom(models.Model):
    ROOM_TYPE_CHOICES = (
        ('course', 'Курс'),
        ('private', 'Приватен'),
        ('group', 'Групен'),
        ('general', 'Општ'),
    )

    name = models.CharField(max_length=100)
    room_type = models.CharField(max_length=20, choices=ROOM_TYPE_CHOICES)
    course = models.OneToOneField(
        Course,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='chat_room'
    )
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='chat_rooms'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_rooms'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_room_group_name(self):
        """WebSocket group name за оваа соба"""
        return f"chat_{self.id}"

    def get_latest_message(self):
        return self.messages.order_by('-timestamp').first()

    def get_unread_count(self, user):
        return self.messages.filter(
            timestamp__gt=user.last_seen.get(str(self.id), self.created_at)
        ).exclude(sender=user).count()

    def __str__(self):
        return f"{self.name} ({self.get_room_type_display()})"


class Message(models.Model):
    MESSAGE_TYPE_CHOICES = (
        ('text', 'Текст'),
        ('file', 'Фајл'),
        ('image', 'Слика'),
        ('system', 'Системска'),
    )

    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    content = models.TextField()
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPE_CHOICES, default='text')
    file_attachment = models.FileField(upload_to='chat_files/', blank=True, null=True)
    reply_to = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies'
    )
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.sender.username}: {self.content[:50]}..."


class MessageRead(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='reads')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    read_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['message', 'user']

    def __str__(self):
        return f"{self.user.username} прочита: {self.message.content[:30]}..."


class UserChatSettings(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='chat_settings'
    )
    notifications_enabled = models.BooleanField(default=True)
    sound_enabled = models.BooleanField(default=True)
    show_online_status = models.BooleanField(default=True)
    last_seen = models.JSONField(default=dict)  # {room_id: timestamp}

    def __str__(self):
        return f"Chat settings за {self.user.username}"