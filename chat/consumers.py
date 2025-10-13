# chat/consumers.py

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import ChatRoom, Message, MessageRead

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'
        self.user = self.scope['user']

        # Провери дали корисникот е автентициран
        if not self.user.is_authenticated:
            await self.close()
            return

        # Провери дали корисникот има пристап до собата
        if not await self.user_has_access():
            await self.close()
            return

        # Приклучи се во group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        # Извести дека корисникот се приклучил
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_joined',
                'username': self.user.username,
                'user_id': self.user.id
            }
        )

    async def disconnect(self, close_code):
        # Извести дека корисникот си заминал
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_left',
                'username': self.user.username,
                'user_id': self.user.id
            }
        )

        # Отстрани од group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type', 'message')

            if message_type == 'message':
                await self.handle_message(text_data_json)
            elif message_type == 'typing':
                await self.handle_typing(text_data_json)
            elif message_type == 'message_read':
                await self.handle_message_read(text_data_json)

        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'error': 'Невалиден JSON формат'
            }))

    async def handle_message(self, data):
        content = data.get('message', '').strip()
        reply_to_id = data.get('reply_to')

        if not content:
            return

        # Зачувај ја пораката во базата
        message = await self.save_message(content, reply_to_id)

        # Испрати ја пораката до сите во групата
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': {
                    'id': message.id,
                    'content': message.content,
                    'sender': message.sender.username,
                    'sender_id': message.sender.id,
                    'timestamp': message.timestamp.isoformat(),
                    'reply_to': message.reply_to.id if message.reply_to else None,
                    'message_type': message.message_type
                }
            }
        )

    async def handle_typing(self, data):
        is_typing = data.get('is_typing', False)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'typing_indicator',
                'username': self.user.username,
                'user_id': self.user.id,
                'is_typing': is_typing
            }
        )

    async def handle_message_read(self, data):
        message_id = data.get('message_id')
        if message_id:
            await self.mark_message_as_read(message_id)

    async def chat_message(self, event):
        message = event['message']

        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': message
        }))

    async def user_joined(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_joined',
            'username': event['username'],
            'user_id': event['user_id']
        }))

    async def user_left(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_left',
            'username': event['username'],
            'user_id': event['user_id']
        }))

    async def typing_indicator(self, event):
        # Не испраќај typing indicator назад до истиот корисник
        if event['user_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'typing',
                'username': event['username'],
                'is_typing': event['is_typing']
            }))

    @database_sync_to_async
    def user_has_access(self):
        """Провери дали корисникот има пристап до собата"""
        try:
            room = ChatRoom.objects.get(id=self.room_id)
            return room.participants.filter(id=self.user.id).exists()
        except ChatRoom.DoesNotExist:
            return False

    @database_sync_to_async
    def save_message(self, content, reply_to_id=None):
        """Зачувај порака во базата"""
        room = ChatRoom.objects.get(id=self.room_id)
        reply_to = None

        if reply_to_id:
            try:
                reply_to = Message.objects.get(id=reply_to_id, room=room)
            except Message.DoesNotExist:
                pass

        message = Message.objects.create(
            room=room,
            sender=self.user,
            content=content,
            reply_to=reply_to
        )
        return message

    @database_sync_to_async
    def mark_message_as_read(self, message_id):
        """Означи порака како прочитана"""
        try:
            message = Message.objects.get(id=message_id)
            MessageRead.objects.get_or_create(
                message=message,
                user=self.user
            )
        except Message.DoesNotExist:
            pass