from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Conversation, Message


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

    def test_user_can_delete_message_from_their_view_only(self):
        conversation = Conversation.objects.create()
        conversation.participants.add(self.user, self.seller)
        message = Message.objects.create(
            conversation=conversation,
            sender=self.user,
            body='Please delete this',
        )

        response = self.client.post(reverse(
            'delete-message',
            args=[conversation.pk, message.pk],
        ))

        self.assertRedirects(response, reverse('chat-room', args=[conversation.pk]))
        self.assertTrue(Message.objects.filter(pk=message.pk).exists())
        self.assertTrue(message.hidden_for.filter(pk=self.user.pk).exists())
        self.assertFalse(message.hidden_for.filter(pk=self.seller.pk).exists())

    def test_user_can_hide_received_message_from_their_view_only(self):
        conversation = Conversation.objects.create()
        conversation.participants.add(self.user, self.seller)
        message = Message.objects.create(
            conversation=conversation,
            sender=self.seller,
            body='Keep this message',
        )

        response = self.client.post(reverse(
            'delete-message',
            args=[conversation.pk, message.pk],
        ))

        self.assertRedirects(response, reverse('chat-room', args=[conversation.pk]))
        self.assertTrue(Message.objects.filter(pk=message.pk).exists())
        self.assertTrue(message.hidden_for.filter(pk=self.user.pk).exists())
        self.assertFalse(message.hidden_for.filter(pk=self.seller.pk).exists())

    def test_hidden_message_disappears_only_for_the_user_who_deleted_it(self):
        conversation = Conversation.objects.create()
        conversation.participants.add(self.user, self.seller)
        message = Message.objects.create(
            conversation=conversation,
            sender=self.seller,
            body='Keep this for the other person',
        )
        message.hidden_for.add(self.user)

        response = self.client.get(reverse('chat-room', args=[conversation.pk]))
        self.assertNotContains(response, 'Keep this for the other person')

        self.client.force_login(self.seller)
        response = self.client.get(reverse('chat-room', args=[conversation.pk]))
        self.assertContains(response, 'Keep this for the other person')

    def test_user_can_delete_conversation_from_their_inbox_only(self):
        conversation = Conversation.objects.create()
        conversation.participants.add(self.user, self.seller)
        Message.objects.create(
            conversation=conversation,
            sender=self.seller,
            body='Still visible to seller',
        )

        response = self.client.post(reverse('delete-conversation', args=[conversation.pk]))

        self.assertRedirects(response, reverse('messaging'))
        self.assertTrue(Conversation.objects.filter(pk=conversation.pk).exists())
        self.assertTrue(conversation.hidden_for.filter(pk=self.user.pk).exists())
        self.assertFalse(conversation.hidden_for.filter(pk=self.seller.pk).exists())
        self.assertNotContains(self.client.get(reverse('messaging')), 'seller')

        self.client.force_login(self.seller)
        self.assertContains(self.client.get(reverse('messaging')), 'buyer')
        self.assertContains(
            self.client.get(reverse('chat-room', args=[conversation.pk])),
            'Still visible to seller',
        )

    def test_new_message_makes_deleted_conversation_reappear_to_recipient(self):
        conversation = Conversation.objects.create()
        conversation.participants.add(self.user, self.seller)
        conversation.hidden_for.add(self.user)
        self.client.force_login(self.seller)

        response = self.client.post(
            reverse('chat-room', args=[conversation.pk]),
            {'body': 'A new message'},
        )

        self.assertRedirects(response, reverse('chat-room', args=[conversation.pk]))
        self.assertFalse(conversation.hidden_for.filter(pk=self.user.pk).exists())
        self.assertContains(self.client.get(reverse('messaging')), 'buyer')

    def test_starting_chat_again_restores_deleted_conversation_for_current_user(self):
        conversation = Conversation.objects.create()
        conversation.participants.add(self.user, self.seller)
        conversation.hidden_for.add(self.user)

        response = self.client.get(
            reverse('start_conversation', args=[self.seller.username]),
        )

        self.assertRedirects(response, reverse('chat-room', args=[conversation.pk]))
        self.assertFalse(conversation.hidden_for.filter(pk=self.user.pk).exists())

    def test_conversation_delete_requires_post(self):
        conversation = Conversation.objects.create()
        conversation.participants.add(self.user, self.seller)

        response = self.client.get(reverse('delete-conversation', args=[conversation.pk]))

        self.assertEqual(response.status_code, 405)
        self.assertFalse(conversation.hidden_for.filter(pk=self.user.pk).exists())

    def test_message_delete_requires_post(self):
        conversation = Conversation.objects.create()
        conversation.participants.add(self.user, self.seller)
        message = Message.objects.create(
            conversation=conversation,
            sender=self.user,
            body='Keep this message',
        )

        response = self.client.get(reverse(
            'delete-message',
            args=[conversation.pk, message.pk],
        ))

        self.assertEqual(response.status_code, 405)
        self.assertTrue(Message.objects.filter(pk=message.pk).exists())

    def test_notification_bell_dot_shows_only_when_user_has_unread_notifications(self):
        # 1. Initially, user has 0 unread messages -> no blue dot
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'class="sidebar-bell-dot"')

        # 2. Another user sends a message to self.user
        conversation = Conversation.objects.create()
        conversation.participants.add(self.user, self.seller)
        msg = Message.objects.create(
            conversation=conversation,
            sender=self.seller,
            body='Hello there, is your book available?',
            is_read=False,
        )

        # 3. User now has an unread notification -> blue dot appears!
        response_with_notif = self.client.get(reverse('dashboard'))
        self.assertContains(response_with_notif, 'class="sidebar-bell-dot"')
        self.assertContains(response_with_notif, '1 unread message')

        # 4. User opens the chat room with that conversation -> message marked read
        chat_response = self.client.get(reverse('chat-room', args=[conversation.pk]))
        self.assertEqual(chat_response.status_code, 200)
        msg.refresh_from_db()
        self.assertTrue(msg.is_read)

        # 5. User checks dashboard again -> blue dot has disappeared
        response_cleared = self.client.get(reverse('dashboard'))
        self.assertNotContains(response_cleared, 'class="sidebar-bell-dot"')
