from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.ChatListView.as_view(), name='list'),
    path('room/<int:room_id>/', views.ChatRoomView.as_view(), name='room'),
    path('room/<int:room_id>/messages/', views.MessageListView.as_view(), name='messages'),
    path('create-room/', views.CreateChatRoomView.as_view(), name='create_room'),
    path('join-room/<int:room_id>/', views.JoinChatRoomView.as_view(), name='join_room'),
]