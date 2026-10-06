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
        self.assertContains(
            response,
            "font-family:'Plus Jakarta Sans', sans-serif !important;",
        )
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
        self.assertContains(dashboard_response, 'Hello, bob')
        self.assertNotContains(dashboard_response, 'Hello, alice')

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

    def test_login_page_links_to_separate_registration_page(self):
        self.client.logout()

        response = self.client.get(reverse('login'))

        self.assertContains(response, 'href="{}"'.format(reverse('register')))
        self.assertNotContains(response, 'Create New Profile')
        self.assertNotContains(response, 'name="password1"')

    def test_registration_page_shows_registration_form_and_login_link(self):
        self.client.logout()

        response = self.client.get(reverse('register'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create New Profile')
        self.assertContains(response, 'name="password1"')
        self.assertContains(response, 'href="{}"'.format(reverse('login')))
        self.assertNotContains(response, 'name="login_submit"')

    def test_successful_registration_creates_user_and_logs_them_in(self):
        self.client.logout()

        response = self.client.post(
            reverse('register'),
            {
                'username': 'newstudent',
                'password1': 'StrongPassword123!',
                'password2': 'StrongPassword123!',
            },
        )

        self.assertRedirects(response, reverse('dashboard'))
        self.assertTrue(
            get_user_model().objects.filter(username='newstudent').exists()
        )
        self.assertContains(self.client.get(reverse('dashboard')), 'Hello, newstudent')

    def test_invalid_registration_stays_on_registration_page(self):
        self.client.logout()

        response = self.client.post(
            reverse('register'),
            {
                'username': 'newstudent',
                'password1': 'different-password-123',
                'password2': 'different-password-456',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['register_form'].errors)
        self.assertFalse(
            get_user_model().objects.filter(username='newstudent').exists()
        )

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

    def test_student_with_cut_email_can_log_in_via_username_and_email(self):
        self.client.logout()
        get_user_model().objects.create_user(
            username='222084665',
            email='222084665@stud.cut.ac.za',
            password='StrongPassword123!',
        )
        # Login via student number / username
        response = self.client.post(
            reverse('login'),
            {'username': '222084665', 'password': 'StrongPassword123!', 'login_submit': '1'},
        )
        self.assertRedirects(response, reverse('dashboard'))

        # Logout and log in via full student email address
        self.client.logout()
        response2 = self.client.post(
            reverse('login'),
            {'username': '222084665@stud.cut.ac.za', 'password': 'StrongPassword123!', 'login_submit': '1'},
        )
        self.assertRedirects(response2, reverse('dashboard'))

    def test_user_with_non_cut_email_cannot_log_in(self):
        self.client.logout()
        get_user_model().objects.create_user(
            username='outsider',
            email='outsider@gmail.com',
            password='Password123!',
        )
        response = self.client.post(
            reverse('login'),
            {'username': 'outsider', 'password': 'Password123!', 'login_submit': '1'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        self.assertContains(response, 'stud.cut.ac.za')

    def test_registration_with_cut_email_requires_and_verifies_otp_code(self):
        self.client.logout()
        # 1. Register with legitimate student email
        response = self.client.post(
            reverse('register'),
            {
                'username': 'cutstudent99',
                'email': '222084665@stud.cut.ac.za',
                'password1': 'SafePass123!@#',
                'password2': 'SafePass123!@#',
            },
        )
        self.assertRedirects(response, reverse('verify_student_email'))
        student = get_user_model().objects.get(username='cutstudent99')
        self.assertEqual(student.email, '222084665@stud.cut.ac.za')

        # Verification record created with 6-digit OTP code
        verification = student.student_verification
        self.assertFalse(verification.is_verified)
        self.assertEqual(len(verification.otp_code), 6)
        self.assertTrue(verification.otp_code.isdigit())

        # 2. Submitting invalid OTP code fails
        wrong_code_resp = self.client.post(
            reverse('verify_student_email'),
            {'otp_code': '000000'},
        )
        self.assertEqual(wrong_code_resp.status_code, 200)
        verification.refresh_from_db()
        self.assertFalse(verification.is_verified)

        # 3. Submitting the legitimate OTP code verifies the email and logs student in
        valid_code_resp = self.client.post(
            reverse('verify_student_email'),
            {'otp_code': verification.otp_code},
        )
        self.assertRedirects(valid_code_resp, reverse('dashboard'))
        verification.refresh_from_db()
        self.assertTrue(verification.is_verified)
        self.assertTrue(valid_code_resp.wsgi_request.user.is_authenticated)

    def test_unverified_student_cannot_log_in_until_verified(self):
        self.client.logout()
        unverified_user = get_user_model().objects.create_user(
            username='pendingstudent',
            email='222084668@stud.cut.ac.za',
            password='SecretPassword123!',
        )
        from registration.models import StudentEmailVerification
        StudentEmailVerification.objects.create(
            user=unverified_user,
            email=unverified_user.email,
            otp_code='654321',
            is_verified=False,
        )

        # Login attempt before verification is blocked and redirected to verification
        response = self.client.post(
            reverse('login'),
            {'username': 'pendingstudent', 'password': 'SecretPassword123!', 'login_submit': '1'},
        )
        self.assertRedirects(response, reverse('verify_student_email'))

    def test_registration_rejects_already_registered_student_email(self):
        self.client.logout()
        get_user_model().objects.create_user(
            username='firststudent',
            email='222084665@stud.cut.ac.za',
            password='SafePass123!@#',
        )
        response = self.client.post(
            reverse('register'),
            {
                'username': 'imposter',
                'email': '222084665@stud.cut.ac.za',
                'password1': 'SafePass123!@#',
                'password2': 'SafePass123!@#',
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(get_user_model().objects.filter(username='imposter').exists())
        self.assertContains(response, 'already registered')

    def test_registration_with_invalid_email_domain_fails(self):
        self.client.logout()
        response = self.client.post(
            reverse('register'),
            {
                'username': 'fraudster',
                'email': 'fraudster@yahoo.com',
                'password1': 'SafePass123!@#',
                'password2': 'SafePass123!@#',
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(get_user_model().objects.filter(username='fraudster').exists())
        self.assertContains(response, 'stud.cut.ac.za')
