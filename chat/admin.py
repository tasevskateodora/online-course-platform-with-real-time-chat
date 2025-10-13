from django.contrib import admin
from .models import ChatRoom, Message, MessageRead, UserChatSettings

@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'room_type', 'created_by', 'is_active', 'created_at')
    list_filter = ('room_type', 'is_active', 'created_at')
    search_fields = ('name', 'created_by__username')
    filter_horizontal = ('participants',)

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'room', 'message_type', 'timestamp', 'is_edited')
    list_filter = ('message_type', 'is_edited', 'timestamp')
    search_fields = ('sender__username', 'content', 'room__name')
    readonly_fields = ('timestamp',)

@admin.register(MessageRead)
class MessageReadAdmin(admin.ModelAdmin):
    list_display = ('user', 'message', 'read_at')
    list_filter = ('read_at',)

@admin.register(UserChatSettings)
class UserChatSettingsAdmin(admin.ModelAdmin):
    list_display = ('user', 'notifications_enabled', 'sound_enabled', 'show_online_status')
    list_filter = ('notifications_enabled', 'sound_enabled', 'show_online_status')