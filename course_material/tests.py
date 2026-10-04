import tempfile
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from course_material.models import Resource


class CourseMaterialTests(TestCase):
    def setUp(self):
        media_dir = tempfile.TemporaryDirectory()
        self.addCleanup(media_dir.cleanup)
        media_settings = override_settings(MEDIA_ROOT=media_dir.name)
        media_settings.enable()
        self.addCleanup(media_settings.disable)
        self.user = get_user_model().objects.create_user(username='alice', password='secret123')
        self.client.force_login(self.user)

    def test_upload_resource_via_post(self):
        uploaded_file = SimpleUploadedFile(
            'sample-notes.pdf',
            b'%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF',
            content_type='application/pdf',
        )
        image_content = BytesIO()
        Image.new('RGB', (1, 1), color='blue').save(image_content, format='PNG')
        uploaded_image = SimpleUploadedFile(
            'study-notes.png',
            image_content.getvalue(),
            content_type='image/png',
        )

        response = self.client.post(
            reverse('course_material'),
            {
                'title': 'Intro to Stats',
                'category': 'NOTES',
                'pdf_file': uploaded_file,
                'image': uploaded_image,
            },
        )

        self.assertEqual(response.status_code, 302)
        resource = Resource.objects.get(title='Intro to Stats', uploaded_by=self.user)
        self.assertTrue(resource.image.name.endswith('study-notes.png'))

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
        response.close()

    def test_uploader_can_delete_resource(self):
        uploaded_file = SimpleUploadedFile(
            'delete-test.pdf',
            b'%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF',
            content_type='application/pdf',
        )
        resource = Resource.objects.create(
            title='Remove me',
            category='NOTES',
            pdf_file=uploaded_file,
            uploaded_by=self.user,
        )

        response = self.client.post(reverse('resource-delete', args=[resource.pk]))

        self.assertRedirects(response, reverse('course_material'))
        self.assertFalse(Resource.objects.filter(pk=resource.pk).exists())

    def test_other_user_cannot_delete_resource(self):
        other_user = get_user_model().objects.create_user(username='bob', password='secret123')
        uploaded_file = SimpleUploadedFile(
            'protected.pdf',
            b'%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF',
            content_type='application/pdf',
        )
        resource = Resource.objects.create(
            title='Protected resource',
            category='NOTES',
            pdf_file=uploaded_file,
            uploaded_by=other_user,
        )

        response = self.client.post(reverse('resource-delete', args=[resource.pk]))

        self.assertEqual(response.status_code, 404)
        self.assertTrue(Resource.objects.filter(pk=resource.pk).exists())

    def test_uploader_sees_remove_control_for_their_resource(self):
        uploaded_file = SimpleUploadedFile(
            'owned.pdf',
            b'%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF',
            content_type='application/pdf',
        )
        Resource.objects.create(
            title='My upload',
            category='NOTES',
            pdf_file=uploaded_file,
            uploaded_by=self.user,
        )

        response = self.client.get(reverse('course_material'))

        self.assertContains(response, 'Remove my upload')
