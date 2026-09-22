from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import Conversation, Message


@login_required
def inbox_view(request):
	# Get all conversations where the current user is a participant
	conversations = request.user.conversations.order_by('-updated_at')

	# Pre-fetch or structure the other participant for easy template rendering
	chat_list = []
	for conv in conversations:
		other_user = conv.participants.exclude(id=request.user.id).first()
		last_message = conv.messages.order_by('-timestamp').first()
		chat_list.append({
			'conversation': conv,
			'other_user': other_user,
			'last_message': last_message
		})

	context = {
		'chat_list': chat_list,
	}
	return render(request, 'messaging/inbox.html', context)


@login_required
def start_conversation_view(request, username):
	recipient = get_object_or_404(User, username=username)

	# Prevent users from messaging themselves
	if recipient == request.user:
		return redirect('housing')

	# Look for an existing conversation between these two users
	conversation = Conversation.objects.filter(participants=request.user).filter(participants=recipient).first()

	# If no conversation exists, create a new one
	if not conversation:
		conversation = Conversation.objects.create()
		conversation.participants.add(request.user, recipient)

	return redirect('chat-room', conversation_id=conversation.id)


@login_required
def chat_room_view(request, conversation_id):
	conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)

	if request.method == 'POST':
		body = request.POST.get('body')
		if body:
			Message.objects.create(
				conversation=conversation,
				sender=request.user,
				body=body
			)
			return redirect('chat-room', conversation_id=conversation.id)

	messages = conversation.messages.order_by('timestamp')
	# Get the other user in the conversation for the header display
	other_user = conversation.participants.exclude(id=request.user.id).first()

	context = {
		'conversation': conversation,
		'messages': messages,
		'other_user': other_user,
	}
	return render(request, 'messaging/chat_room.html', context)