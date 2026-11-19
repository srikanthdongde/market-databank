import io
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import Category, Dataset, UserProfile


class MarketDatabankTests(TestCase):
    def setUp(self):
        self.client = Client()

        # 1. Users
        self.user1 = User.objects.create_user(
            username='student1',
            email='student1@test.com',
            password='Password@123'
        )
        self.user2 = User.objects.create_user(
            username='student2',
            email='student2@test.com',
            password='Password@123'
        )

        # 2. Category
        self.category_stock = Category.objects.create(
            name='Stock Market',
            description='Equities and Indices'
        )
        self.category_crypto = Category.objects.create(
            name='Cryptocurrency',
            description='Digital Assets'
        )

        # 3. Valid CSV File content
        csv_content = (
            "Date,Ticker,Close,Volume\n"
            "2024-01-01,AAPL,185.50,1000000\n"
            "2024-01-02,AAPL,187.20,1200000\n"
            "2024-01-03,AAPL,186.00,950000\n"
        ).encode('utf-8')

        self.valid_csv = SimpleUploadedFile(
            "apple_stock.csv",
            csv_content,
            content_type="text/csv"
        )

        # 4. Public Dataset owned by user1
        self.public_dataset = Dataset.objects.create(
            title='Apple Daily Stock Matrix',
            description='Daily stock prices for AAPL',
            category=self.category_stock,
            owner=self.user1,
            uploaded_file=self.valid_csv,
            source='NASDAQ Feed',
            is_public=True,
            row_count=3,
            column_count=4,
            column_names='Date, Ticker, Close, Volume',
            file_size=len(csv_content)
        )

        # 5. Private Dataset owned by user1
        private_csv_content = "Participant_ID,Score\nP001,88.5\nP002,92.0\n".encode('utf-8')
        self.private_csv = SimpleUploadedFile(
            "thesis_data.csv",
            private_csv_content,
            content_type="text/csv"
        )
        self.private_dataset = Dataset.objects.create(
            title='Private Student Thesis Metric',
            description='Confidential experimental scores',
            category=self.category_crypto,
            owner=self.user1,
            uploaded_file=self.private_csv,
            source='Lab Experiments',
            is_public=False,
            row_count=2,
            column_count=2,
            column_names='Participant_ID, Score',
            file_size=len(private_csv_content)
        )

    def test_home_page_loads(self):
        """Test public home page accessibility."""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Market Databank')
        self.assertContains(response, 'Apple Daily Stock Matrix')

    def test_about_page_loads(self):
        """Test about documentation page."""
        response = self.client.get(reverse('about'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'CSV Validation & Ingestion Pipeline')

    def test_user_registration(self):
        """Test account registration flow."""
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'Researcher',
            'email': 'new@test.com',
            'organization': 'MIT Research',
            'password1': 'SecurePass@123',
            'password2': 'SecurePass@123',
        })
        self.assertEqual(response.status_code, 302)  # Redirects to dashboard
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_user_login_and_dashboard(self):
        """Test user login and dashboard display."""
        login_success = self.client.login(username='student1', password='Password@123')
        self.assertTrue(login_success)

        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Research Dashboard')
        self.assertContains(response, 'Apple Daily Stock Matrix')

    def test_explore_datasets_public_vs_private(self):
        """
        Anonymous user should see public datasets but NEVER see private datasets.
        """
        response = self.client.get(reverse('explore_datasets'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Apple Daily Stock Matrix')
        self.assertNotContains(response, 'Private Student Thesis Metric')

    def test_dataset_detail_public(self):
        """Public dataset details viewable by anyone."""
        response = self.client.get(reverse('dataset_detail', kwargs={'pk': self.public_dataset.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Apple Daily Stock Matrix')
        self.assertContains(response, 'Data Preview')

    def test_dataset_detail_private_unauthorized(self):
        """Private dataset details must raise 403 for unauthorized users."""
        # Unauthenticated user
        response = self.client.get(reverse('dataset_detail', kwargs={'pk': self.private_dataset.pk}))
        self.assertEqual(response.status_code, 403)

        # Logged in as student2 (not owner)
        self.client.login(username='student2', password='Password@123')
        response = self.client.get(reverse('dataset_detail', kwargs={'pk': self.private_dataset.pk}))
        self.assertEqual(response.status_code, 403)

    def test_dataset_detail_private_authorized(self):
        """Private dataset details accessible to owner."""
        self.client.login(username='student1', password='Password@123')
        response = self.client.get(reverse('dataset_detail', kwargs={'pk': self.private_dataset.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Private Student Thesis Metric')

    def test_upload_valid_csv_dataset(self):
        """Test uploading a new dataset with CSV parsing."""
        self.client.login(username='student1', password='Password@123')

        csv_data = "City,Temperature,Humidity\nDelhi,32.5,65\nMumbai,29.0,80\n".encode('utf-8')
        upload_file = SimpleUploadedFile("weather.csv", csv_data, content_type="text/csv")

        response = self.client.post(reverse('dataset_upload'), {
            'title': 'Metropolitan Weather Parameters',
            'category': self.category_stock.pk,
            'description': 'Daily weather measurements across Indian metro cities.',
            'source': 'National Weather Service',
            'uploaded_file': upload_file,
            'is_public': True,
        })
        self.assertEqual(response.status_code, 302)

        # Check DB
        uploaded_ds = Dataset.objects.filter(title='Metropolitan Weather Parameters').first()
        self.assertIsNotNone(uploaded_ds)
        self.assertEqual(uploaded_ds.row_count, 2)
        self.assertEqual(uploaded_ds.column_count, 3)

    def test_upload_invalid_file_rejected(self):
        """Uploading non-csv file should fail validation."""
        self.client.login(username='student1', password='Password@123')

        bad_file = SimpleUploadedFile("notes.txt", b"plain text notes", content_type="text/plain")
        response = self.client.post(reverse('dataset_upload'), {
            'title': 'Invalid File Attempt',
            'category': self.category_stock.pk,
            'description': 'Attempting non-csv',
            'source': 'None',
            'uploaded_file': bad_file,
            'is_public': True,
        })
        self.assertEqual(response.status_code, 200)  # Form returns with errors
        self.assertFalse(Dataset.objects.filter(title='Invalid File Attempt').exists())

    def test_download_public_dataset(self):
        """Anyone can download public CSV."""
        response = self.client.get(reverse('dataset_download', kwargs={'pk': self.public_dataset.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')

    def test_download_private_dataset_permissions(self):
        """Unauthorized users cannot download private CSV."""
        # Unauthenticated
        response = self.client.get(reverse('dataset_download', kwargs={'pk': self.private_dataset.pk}))
        self.assertEqual(response.status_code, 403)

        # Different user
        self.client.login(username='student2', password='Password@123')
        response = self.client.get(reverse('dataset_download', kwargs={'pk': self.private_dataset.pk}))
        self.assertEqual(response.status_code, 403)

        # Owner can download
        self.client.login(username='student1', password='Password@123')
        response = self.client.get(reverse('dataset_download', kwargs={'pk': self.private_dataset.pk}))
        self.assertEqual(response.status_code, 200)

    def test_edit_and_delete_permissions(self):
        """Non-owners cannot edit or delete datasets."""
        self.client.login(username='student2', password='Password@123')

        # Try to edit student1's dataset
        response = self.client.get(reverse('dataset_edit', kwargs={'pk': self.public_dataset.pk}))
        self.assertEqual(response.status_code, 403)

        # Try to delete student1's dataset
        response = self.client.post(reverse('dataset_delete', kwargs={'pk': self.public_dataset.pk}))
        self.assertEqual(response.status_code, 403)

        # Owner can access edit
        self.client.login(username='student1', password='Password@123')
        response = self.client.get(reverse('dataset_edit', kwargs={'pk': self.public_dataset.pk}))
        self.assertEqual(response.status_code, 200)
