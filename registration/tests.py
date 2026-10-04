from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class LogoutTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='alice', password='secret123')
        self.client.force_login(self.user)

    def test_logout_shows_thank_you_then_redirects_to_login(self):
        response = self.client.post(reverse('logout'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Thanks for visiting')
        self.assertContains(response, 'http-equiv="refresh"')
        self.assertContains(
            response,
            'content="4;url={}"'.format(reverse('login')),
        )
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_successful_login_does_not_show_welcome_toast(self):
        self.client.logout()
        response = self.client.post(
            reverse('login'),
            {'username': 'alice', 'password': 'secret123', 'login_submit': '1'},
        )

        self.assertRedirects(response, reverse('dashboard'))
        login_response = self.client.get(reverse('login'))
        self.assertNotContains(login_response, 'Welcome back, alice!')

    def test_opening_login_page_logs_out_current_user(self):
        response = self.client.get(reverse('login'))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        self.assertEqual(
            self.client.get(reverse('dashboard')).status_code,
            302,
        )

    def test_login_session_cookie_expires_when_browser_closes(self):
        self.client.logout()
        response = self.client.post(
            reverse('login'),
            {'username': 'alice', 'password': 'secret123', 'login_submit': '1'},
        )

        self.assertTrue(settings.SESSION_EXPIRE_AT_BROWSER_CLOSE)
        self.assertEqual(response.cookies[settings.SESSION_COOKIE_NAME]['expires'], '')
        self.assertEqual(response.cookies[settings.SESSION_COOKIE_NAME]['max-age'], '')

    def test_another_user_can_log_in_after_opening_login_page(self):
        get_user_model().objects.create_user(
            username='bob',
            password='secret456',
        )
        self.client.get(reverse('login'))

        response = self.client.post(
            reverse('login'),
            {'username': 'bob', 'password': 'secret456', 'login_submit': '1'},
        )

        self.assertRedirects(response, reverse('dashboard'))
        dashboard_response = self.client.get(reverse('dashboard'))
        self.assertContains(dashboard_response, 'Welcome back, bob!')
        self.assertNotContains(dashboard_response, 'Welcome back, alice!')

    def test_successful_login_returns_to_requested_page(self):
        self.client.logout()
        destination = '/messaging/chat/10/'
        response = self.client.get(reverse('login'), {'next': destination})

        self.assertContains(response, 'name="next" value="{}"'.format(destination))

        response = self.client.post(
            reverse('login'),
            {
                'username': 'alice',
                'password': 'secret123',
                'login_submit': '1',
                'next': destination,
            },
        )

        self.assertRedirects(response, destination, fetch_redirect_response=False)

    def test_successful_login_rejects_external_next_url(self):
        self.client.logout()
        response = self.client.post(
            reverse('login'),
            {
                'username': 'alice',
                'password': 'secret123',
                'login_submit': '1',
                'next': 'https://malicious.example/',
            },
        )

        self.assertRedirects(response, reverse('dashboard'))

    def test_admin_tab_hidden_for_non_staff_users(self):
        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Admin')
        self.assertContains(response, '<span class="role-status">Student</span>')

    def test_superusers_can_see_admin_tab(self):
        superuser = get_user_model().objects.create_user(
            username='superadmin',
            password='secret123',
            is_staff=True,
            is_superuser=True,
        )
        self.client.force_login(superuser)

        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Admin')
        self.assertContains(response, reverse('admin:index'))

    def test_staff_users_can_open_admin_from_header(self):
        staff_user = get_user_model().objects.create_user(
            username='staffmember',
            password='secret123',
            is_staff=True,
        )
        self.client.force_login(staff_user)

        dashboard_response = self.client.get(reverse('dashboard'))
        admin_response = self.client.get(reverse('admin:index'))

        self.assertContains(dashboard_response, 'href="{}"'.format(reverse('admin:index')))
        self.assertEqual(admin_response.status_code, 200)

    def test_non_superusers_cannot_access_admin_directly(self):
        response = self.client.get('/admin/')

        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/login/', response.url)

    def test_menu_button_visible_after_login(self):
        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="sidebarToggle"')

    def test_notification_bell_hidden_before_login(self):
        self.client.logout()
        response = self.client.get(reverse('login'))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, '🔔')
        self.assertNotContains(response, 'id="sidebarToggle"')
