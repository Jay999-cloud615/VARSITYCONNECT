from django.urls import path
from . import views

urlpatterns = [
    # Add name='messaging' to your inbox or main messaging route
    path('', views.inbox_view, name='messaging'), # or whatever your view is called
    path('start/<str:username>/', views.start_conversation_view, name='start_conversation'),
    path('chat/<int:conversation_id>/', views.chat_room_view, name='chat-room'),
]