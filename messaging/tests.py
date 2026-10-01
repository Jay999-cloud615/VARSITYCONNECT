from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Conversation


class MessagingFlowTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='buyer', password='secret123')
        self.seller = get_user_model().objects.create_user(username='seller', password='secret123')
        self.client.force_login(self.user)

    def test_contact_seller_redirects_to_chat_room(self):
        response = self.client.get(reverse('start_conversation', args=[self.seller.username]))

        self.assertEqual(response.status_code, 302)
        conversation = Conversation.objects.filter(participants=self.user).filter(participants=self.seller).first()
        self.assertIsNotNone(conversation)
        self.assertRedirects(response, reverse('chat-room', args=[conversation.id]))

    def test_self_message_redirects_to_inbox(self):
        response = self.client.get(reverse('start_conversation', args=[self.user.username]))

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('messaging'))

    def test_notification_bell_links_to_messages(self):
        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'href="/messaging/"')
