import tempfile
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from marketplace.models import MarketplaceListing


class MarketplaceListingTests(TestCase):
    def setUp(self):
        media_dir = tempfile.TemporaryDirectory()
        self.addCleanup(media_dir.cleanup)
        media_settings = override_settings(MEDIA_ROOT=media_dir.name)
        media_settings.enable()
        self.addCleanup(media_settings.disable)
        user_model = get_user_model()
        self.seller = user_model.objects.create_user(username='seller', password='secret123')
        self.other_user = user_model.objects.create_user(username='buyer', password='secret123')
        self.listing = MarketplaceListing.objects.create(
            title='Used textbook',
            price='100.00',
            category='textbooks',
            description='A textbook in good condition.',
            seller=self.seller,
        )

    def test_create_listing_saves_uploaded_image(self):
        self.client.force_login(self.seller)
        image_content = BytesIO()
        Image.new('RGB', (1, 1), color='red').save(image_content, format='PNG')
        response = self.client.post(
            reverse('create_listing'),
            {
                'title': 'Calculator',
                'price': '150.00',
                'quantity_available': '1',
                'category': 'electronics',
                'condition': 'Used',
                'description': 'Scientific calculator.',
                'location': 'Campus',
                'image': SimpleUploadedFile('calculator.png', image_content.getvalue(), content_type='image/png'),
            },
        )

        self.assertRedirects(response, reverse('marketplace'))
        listing = MarketplaceListing.objects.get(title='Calculator', seller=self.seller)
        self.assertTrue(listing.image.name.endswith('calculator.png'))

    def test_seller_can_delete_own_listing(self):
        self.client.force_login(self.seller)
        page = self.client.get(reverse('marketplace'))
        self.assertContains(page, 'Delete my listing')
        response = self.client.post(reverse('delete_listing', args=[self.listing.pk]))

        self.assertRedirects(response, reverse('marketplace'))
        self.assertFalse(MarketplaceListing.objects.filter(pk=self.listing.pk).exists())

    def test_other_user_cannot_delete_listing(self):
        self.client.force_login(self.other_user)
        response = self.client.post(reverse('delete_listing', args=[self.listing.pk]))

        self.assertEqual(response.status_code, 404)
        self.assertTrue(MarketplaceListing.objects.filter(pk=self.listing.pk).exists())

    def test_seller_can_update_quantity_left(self):
        self.client.force_login(self.seller)
        response = self.client.post(
            reverse('update_listing_stock', args=[self.listing.pk]),
            {'quantity_available': '2'},
        )

        self.assertRedirects(response, reverse('listing_detail', args=[self.listing.pk]))
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.quantity_available, 2)

    def test_seller_can_mark_listing_sold_out(self):
        self.client.force_login(self.seller)
        response = self.client.post(
            reverse('update_listing_stock', args=[self.listing.pk]),
            {'quantity_available': '0'},
        )

        self.assertRedirects(response, reverse('listing_detail', args=[self.listing.pk]))
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.quantity_available, 0)

    def test_other_user_cannot_update_listing_quantity(self):
        self.client.force_login(self.other_user)
        response = self.client.post(
            reverse('update_listing_stock', args=[self.listing.pk]),
            {'quantity_available': '2'},
        )

        self.assertEqual(response.status_code, 404)
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.quantity_available, 1)

    def test_listing_form_rejects_negative_quantity(self):
        self.client.force_login(self.seller)
        response = self.client.post(
            reverse('create_listing'),
            {
                'title': 'Bad stock',
                'price': '10.00',
                'quantity_available': '-1',
                'category': 'electronics',
                'condition': 'Used',
                'description': 'Invalid quantity.',
                'location': 'Campus',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(MarketplaceListing.objects.filter(title='Bad stock').exists())
