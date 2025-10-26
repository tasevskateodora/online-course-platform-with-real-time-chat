from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, View
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.db.models import Q, Count
from .models import ChatRoom, Message, UserChatSettings
from .forms import ChatRoomForm, MessageForm
from courses.models import Course


class ChatListView(LoginRequiredMixin, ListView):
    model = ChatRoom
    template_name = 'chat/list.html'
    context_object_name = 'chat_rooms'

    def get_queryset(self):
        user = self.request.user
        return ChatRoom.objects.filter(
            participants=user,
            is_active=True
        ).annotate(
            message_count=Count('messages')
        ).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Креирај или земи кориснички поставки за чет
        chat_settings, created = UserChatSettings.objects.get_or_create(user=user)
        context['chat_settings'] = chat_settings

        # Достапни курсеви за кои може да се креира чет
        if user.user_type == 'instructor':
            context['available_courses'] = Course.objects.filter(
                instructor=user,
                status='published'
            ).exclude(
                chat_room__isnull=False
            )

        return context


class ChatRoomView(LoginRequiredMixin, DetailView):
    model = ChatRoom
    template_name = 'chat/room.html'
    context_object_name = 'room'
    pk_url_kwarg = 'room_id'

    def get_object(self):
        room = get_object_or_404(ChatRoom, id=self.kwargs['room_id'])

        # Провери дали корисникот има пристап до собата
        if not room.participants.filter(id=self.request.user.id).exists():
            # Ако е соба за курс, провери дали корисникот е запишан
            if room.room_type == 'course' and room.course:
                if (self.request.user == room.course.instructor or
                        room.course.enrollments.filter(
                            student=self.request.user,
                            is_active=True
                        ).exists()):
                    room.participants.add(self.request.user)
                else:
                    raise PermissionError("Немате пристап до оваа чет соба.")
            else:
                raise PermissionError("Немате пристап до оваа чет соба.")

        return room

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        room = self.object

        # Последни пораки
        context['messages'] = Message.objects.filter(
            room=room
        ).select_related('sender').order_by('-timestamp')[:50][::-1]

        # Учесници во собата
        context['participants'] = room.participants.all()

        # Форма за пораки
        context['message_form'] = MessageForm()

        # WebSocket URL
        context['room_group_name'] = room.get_room_group_name()

        return context


class MessageListView(LoginRequiredMixin, View):
    """API за зимање на пораки (за AJAX)"""

    def get(self, request, room_id):
        room = get_object_or_404(ChatRoom, id=room_id)

        # Провери пристап
        if not room.participants.filter(id=request.user.id).exists():
            return JsonResponse({'error': 'Немате пристап'}, status=403)

        page = int(request.GET.get('page', 1))
        limit = 20
        offset = (page - 1) * limit

        messages = Message.objects.filter(
            room=room
        ).select_related('sender').order_by('-timestamp')[offset:offset + limit]

        messages_data = []
        for message in reversed(messages):
            messages_data.append({
                'id': message.id,
                'content': message.content,
                'sender': message.sender.username,
                'sender_name': message.sender.get_full_name() or message.sender.username,
                'timestamp': message.timestamp.isoformat(),
                'message_type': message.message_type,
                'is_own': message.sender == request.user
            })

        return JsonResponse({'messages': messages_data})


class CreateChatRoomView(LoginRequiredMixin, CreateView):
    model = ChatRoom
    form_class = ChatRoomForm
    template_name = 'chat/create_room.html'
    success_url = reverse_lazy('chat:list')

    def dispatch(self, request, *args, **kwargs):
        # Само инструктори можат да креираат соби
        if request.user.user_type != 'instructor':
            messages.error(request, 'Само инструкторите можат да креираат чет соби.')
            return redirect('chat:list')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)

        # Додај го креаторот како учесник
        self.object.participants.add(self.request.user)

        # Додај ги избраните корисници
        selected_participants = form.cleaned_data.get('participants')
        if selected_participants:
            self.object.participants.add(*selected_participants)
            print(f"DEBUG: Додадени {selected_participants.count()} корисници")

        # Ако е соба за курс, додај ги сите запишани студенти
        if self.object.room_type == 'course' and self.object.course:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            enrolled_students = User.objects.filter(
                enrollments__course=self.object.course,
                enrollments__is_active=True
            )
            self.object.participants.add(*enrolled_students)
            print(f"DEBUG: Додадени {enrolled_students.count()} студенти од курсот")

        messages.success(
            self.request,
            f'Чет собата "{self.object.name}" е успешно креирана со {self.object.participants.count()} учесници!'
        )
        return response

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs


class JoinChatRoomView(LoginRequiredMixin, View):
    """Приклучување во чет соба"""

    def post(self, request, room_id):
        room = get_object_or_404(ChatRoom, id=room_id)

        # Провери дали може да се приклучи
        if room.room_type == 'private':
            messages.error(request, 'Не можете да се приклучите во приватна соба.')
            return redirect('chat:list')

        # Провери за курс соби
        if room.room_type == 'course' and room.course:
            if not (request.user == room.course.instructor or
                    room.course.enrollments.filter(
                        student=request.user,
                        is_active=True
                    ).exists()):
                messages.error(request, 'Немате пристап до оваа соба.')
                return redirect('chat:list')

        # Додај го корисникот
        room.participants.add(request.user)
        messages.success(request, f'Успешно се приклучивте во "{room.name}"!')

        return redirect('chat:room', room_id=room.id)