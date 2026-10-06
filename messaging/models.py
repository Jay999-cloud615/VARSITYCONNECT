from django.db import models
from django.contrib.auth.models import User

class Conversation(models.Model):
    participants = models.ManyToManyField(User, related_name='conversations')
    hidden_for = models.ManyToManyField(User, blank=True, related_name='hidden_conversations')
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        usernames = [user.username for user in self.participants.all()]
        return f"Conversation between {', '.join(usernames)}"

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    hidden_for = models.ManyToManyField(User, blank=True, related_name='hidden_messages')
    body = models.TextField()
    is_read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"From {self.sender.username} at {self.timestamp}"