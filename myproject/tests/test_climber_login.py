"""
Unit tests for climber login functionality.
"""
import uuid
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.messages import get_messages
from django.utils import timezone
from datetime import timedelta

from core.models import TemporaryClimber


class ClimberLoginTestCase(TestCase):
    """Test case for climber login view."""
    
    def setUp(self):
        """Set up test case."""
        self.client = Client()
        self.login_url = reverse('climber-login')
        
        # Create test climber
        self.verified_climber = TemporaryClimber.objects.create(
            name='Test Climber',
            email='test@example.com',
            email_verified=True,
            access_until=timezone.now() + timedelta(hours=24)
        )
        
        self.unverified_climber = TemporaryClimber.objects.create(
            name='Unverified Climber',
            email='unverified@example.com',
            email_verified=False
        )
        
        self.expired_climber = TemporaryClimber.objects.create(
            name='Expired Climber',
            email='expired@example.com',
            email_verified=True,
            access_until=timezone.now() - timedelta(hours=1)
        )

    def test_login_page_get(self):
        """Test GET request to login page."""
        response = self.client.get(self.login_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ClimaCocal')
        self.assertContains(response, 'Entre com seu email verificado')

    def test_login_success(self):
        """Test successful login with verified email."""
        response = self.client.post(self.login_url, {
            'email': self.verified_climber.email
        })
        
        # Should redirect to access page
        self.assertRedirects(response, reverse('climber-access'))
        
        # Check session data
        session = self.client.session
        self.assertEqual(session['climber_id'], self.verified_climber.id)
        self.assertEqual(session['climber_email'], self.verified_climber.email)
        
        # Check success message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('Login realizado com sucesso' in str(m) for m in messages))

    def test_login_unverified_email(self):
        """Test login with unverified email."""
        response = self.client.post(self.login_url, {
            'email': self.unverified_climber.email
        })
        
        # Should stay on login page with error
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Email não encontrado ou não verificado')

    def test_login_expired_access(self):
        """Test login with expired access."""
        response = self.client.post(self.login_url, {
            'email': self.expired_climber.email
        })
        
        # Should stay on login page with error
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'acesso temporário expirou')

    def test_login_nonexistent_email(self):
        """Test login with non-existent email."""
        response = self.client.post(self.login_url, {
            'email': 'nonexistent@example.com'
        })
        
        # Should stay on login page with error
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Email não encontrado ou não verificado')

    def test_login_empty_email(self):
        """Test login with empty email."""
        response = self.client.post(self.login_url, {
            'email': ''
        })
        
        # Should stay on login page with error
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Email é obrigatório')

    def test_login_case_insensitive(self):
        """Test that login is case insensitive."""
        response = self.client.post(self.login_url, {
            'email': self.verified_climber.email.upper()
        })
        
        # Should redirect to access page
        self.assertRedirects(response, reverse('climber-access'))
        
        # Check session data
        session = self.client.session
        self.assertEqual(session['climber_email'], self.verified_climber.email.lower())