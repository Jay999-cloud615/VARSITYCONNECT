from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from housing.models import Job


class JobBoardTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='poster', password='secret123')
        self.client.force_login(self.user)

    def test_user_can_post_job(self):
        response = self.client.post(
            reverse('jobs'),
            {
                'title': 'Weekend tutor',
                'organization': 'Campus Tutoring',
                'location': 'On campus',
                'pay': 'R100/hour',
                'description': 'Tutor first-year students.',
            },
        )

        self.assertRedirects(response, reverse('jobs'))
        self.assertTrue(Job.objects.filter(title='Weekend tutor', posted_by=self.user).exists())

    def test_job_detail_and_jobs_route_are_available(self):
        job = Job.objects.create(
            title='Library assistant',
            location='Campus library',
            description='Help at the library desk.',
            posted_by=self.user,
        )

        self.assertEqual(self.client.get(reverse('jobs')).status_code, 200)
        self.assertEqual(self.client.get(reverse('job-detail', args=[job.pk])).status_code, 200)
        self.assertNotIn('accommodation', self.client.get(reverse('jobs')).content.decode().lower())
        self.assertEqual(self.client.get('/housing/').status_code, 404)

    def test_job_owner_can_delete_job_from_jobs_list(self):
        job = Job.objects.create(
            title='Weekend tutor',
            location='On campus',
            description='Tutor first-year students.',
            posted_by=self.user,
        )

        list_response = self.client.get(reverse('jobs'))

        self.assertContains(
            list_response,
            'action="{}"'.format(reverse('job-delete', args=[job.pk])),
        )
        self.assertContains(list_response, 'Delete my job post')

        response = self.client.post(reverse('job-delete', args=[job.pk]))

        self.assertRedirects(response, reverse('jobs'))
        self.assertFalse(Job.objects.filter(pk=job.pk).exists())

    def test_job_list_does_not_show_delete_button_for_another_users_job(self):
        other_user = get_user_model().objects.create_user(
            username='other',
            password='secret123',
        )
        job = Job.objects.create(
            title='Protected role',
            location='Remote',
            description='A protected job listing.',
            posted_by=other_user,
        )

        response = self.client.get(reverse('jobs'))

        self.assertNotContains(
            response,
            'action="{}"'.format(reverse('job-delete', args=[job.pk])),
        )
        self.assertNotContains(response, 'Delete my job post')

    def test_other_user_cannot_delete_job(self):
        other_user = get_user_model().objects.create_user(username='other', password='secret123')
        job = Job.objects.create(
            title='Protected role',
            location='Remote',
            description='A protected job listing.',
            posted_by=other_user,
        )

        response = self.client.post(reverse('job-delete', args=[job.pk]))

        self.assertEqual(response.status_code, 404)
        self.assertTrue(Job.objects.filter(pk=job.pk).exists())
