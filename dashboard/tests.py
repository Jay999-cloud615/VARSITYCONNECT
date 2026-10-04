import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from course_material.models import Resource
from housing.models import Job
from marketplace.models import MarketplaceListing


class ProfileTests(TestCase):
    def setUp(self):
        media_dir = tempfile.TemporaryDirectory()
        self.addCleanup(media_dir.cleanup)
        media_settings = override_settings(MEDIA_ROOT=media_dir.name)
        media_settings.enable()
        self.addCleanup(media_settings.disable)

        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username='profileuser',
            password='secret123',
            first_name='Profile',
            last_name='User',
        )
        self.other_user = user_model.objects.create_user(
            username='otheruser',
            password='secret123',
        )
        self.client.force_login(self.user)

    def test_profile_shows_name_and_clickable_contribution_counts(self):
        MarketplaceListing.objects.create(
            title='My textbook',
            price='100.00',
            category='textbooks',
            description='A textbook for sale.',
            seller=self.user,
        )
        Job.objects.create(
            title='My campus job',
            location='Campus',
            description='A student job.',
            posted_by=self.user,
        )
        Resource.objects.create(
            title='My lecture notes',
            category='NOTES',
            pdf_file=SimpleUploadedFile(
                'notes.pdf',
                b'%PDF-1.4\n%%EOF',
                content_type='application/pdf',
            ),
            uploaded_by=self.user,
        )

        response = self.client.get(reverse('profile'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "font-family:'Plus Jakarta Sans', sans-serif !important;",
        )
        self.assertContains(response, 'Profile User')
        self.assertContains(response, '@profileuser')
        self.assertContains(response, 'class="profile-avatar" aria-hidden="true"')
        self.assertContains(response, 'class="sidebar-avatar" aria-hidden="true"')
        self.assertContains(response, '<circle cx="50" cy="34" r="19"></circle>')
        self.assertNotContains(response, 'class="brand-mark"')
        self.assertContains(response, 'Marketplace listings')
        self.assertContains(response, 'Jobs you posted')
        self.assertContains(response, 'Course materials')
        self.assertContains(
            response,
            'class="profile-stat" href="{}"'.format(reverse('marketplace')),
        )
        self.assertContains(
            response,
            'class="profile-stat" href="{}"'.format(reverse('jobs')),
        )
        self.assertContains(
            response,
            'class="profile-stat" href="{}"'.format(reverse('course_material')),
        )
        self.assertContains(response, '<strong>1</strong>', count=3)
        self.assertNotContains(response, 'My textbook')
        self.assertNotContains(response, 'My campus job')
        self.assertNotContains(response, 'My lecture notes')
        self.assertNotContains(response, 'Your campus footprint')
        self.assertNotContains(response, 'Explore the community')
        self.assertNotContains(response, 'Buy and sell')
        self.assertNotContains(response, 'Campus opportunities')
        self.assertNotContains(response, 'Study and share')

    def test_profile_counts_only_content_shared_by_current_user(self):
        MarketplaceListing.objects.create(
            title='Someone elses listing',
            price='100.00',
            category='textbooks',
            description='Another user listing.',
            seller=self.other_user,
        )
        Job.objects.create(
            title='Someone elses job',
            location='Campus',
            description='Another user job.',
            posted_by=self.other_user,
        )
        Resource.objects.create(
            title='Someone elses notes',
            category='NOTES',
            pdf_file=SimpleUploadedFile(
                'other-notes.pdf',
                b'%PDF-1.4\n%%EOF',
                content_type='application/pdf',
            ),
            uploaded_by=self.other_user,
        )

        response = self.client.get(reverse('profile'))

        self.assertNotContains(response, 'Someone elses listing')
        self.assertNotContains(response, 'Someone elses job')
        self.assertNotContains(response, 'Someone elses notes')
        self.assertContains(response, '<strong>0</strong>', count=3)

    def test_profile_requires_login_and_is_linked_from_sidebar(self):
        self.client.logout()
        response = self.client.get(reverse('profile'))

        self.assertRedirects(
            response,
            '{}?next={}'.format(reverse('login'), reverse('profile')),
        )

        self.client.force_login(self.user)
        response = self.client.get(reverse('profile'))

        self.assertContains(response, 'href="{}"'.format(reverse('profile')))
        self.assertContains(response, 'class="nav-item active"')


class DashboardHomeTests(TestCase):
    def setUp(self):
        media_dir = tempfile.TemporaryDirectory()
        self.addCleanup(media_dir.cleanup)
        media_settings = override_settings(MEDIA_ROOT=media_dir.name)
        media_settings.enable()
        self.addCleanup(media_settings.disable)

        self.user = get_user_model().objects.create_user(
            username='student',
            password='secret123',
            first_name='Alex',
        )
        self.client.force_login(self.user)

    def test_dashboard_shows_only_greeting_and_activity_cards(self):
        MarketplaceListing.objects.create(
            title='Campus calculator',
            price='150.00',
            category='electronics',
            description='Scientific calculator.',
            seller=self.user,
        )
        Job.objects.create(
            title='Library assistant',
            location='Campus library',
            description='Help at the front desk.',
            posted_by=self.user,
        )
        Resource.objects.create(
            title='Biology notes',
            category='NOTES',
            pdf_file=SimpleUploadedFile(
                'biology.pdf',
                b'%PDF-1.4\n%%EOF',
                content_type='application/pdf',
            ),
            uploaded_by=self.user,
        )

        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Home')
        self.assertContains(response, 'Hello Alex')
        self.assertContains(response, 'Here’s what’s happening across your campus hub today.')
        self.assertContains(response, 'Marketplace items')
        self.assertContains(response, 'Student jobs')
        self.assertContains(response, 'Course resources')
        self.assertNotContains(response, 'Campus calculator')
        self.assertNotContains(response, 'Library assistant')
        self.assertNotContains(response, 'Biology notes')
        self.assertNotContains(response, 'Quick actions')
        self.assertNotContains(response, 'Latest student jobs')
        self.assertContains(response, 'href="{}"'.format(reverse('marketplace')))
        self.assertContains(response, 'href="{}"'.format(reverse('jobs')))
        self.assertContains(response, 'href="{}"'.format(reverse('course_material')))
        self.assertContains(response, '<strong>1</strong>')

    def test_dashboard_requires_login(self):
        self.client.logout()

        response = self.client.get(reverse('dashboard'))

        self.assertRedirects(
            response,
            '{}?next={}'.format(reverse('login'), reverse('dashboard')),
        )
