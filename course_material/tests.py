from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from course_material.models import Resource


class CourseMaterialTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='alice', password='secret123')
        self.client.force_login(self.user)

    def test_upload_resource_via_post(self):
        uploaded_file = SimpleUploadedFile(
            'sample-notes.pdf',
            b'%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF',
            content_type='application/pdf',
        )

        response = self.client.post(
            reverse('course_material'),
            {
                'title': 'Intro to Stats',
                'category': 'NOTES',
                'pdf_file': uploaded_file,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Resource.objects.filter(title='Intro to Stats', uploaded_by=self.user).exists())

    def test_download_resource_returns_attachment(self):
        uploaded_file = SimpleUploadedFile(
            'download-test.pdf',
            b'%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF',
            content_type='application/pdf',
        )
        resource = Resource.objects.create(
            title='Algorithms',
            category='NOTES',
            pdf_file=uploaded_file,
            uploaded_by=self.user,
        )

        response = self.client.get(reverse('resource-download', args=[resource.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertIn('attachment', response.get('Content-Disposition', ''))
        self.assertIn('download-test', response.get('Content-Disposition', ''))
