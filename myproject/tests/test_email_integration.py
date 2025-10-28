"""
Integration tests for email functionality with login system.
Tests the complete flow from registration to email sending to login.
"""
import uuid
from django.test import TestCase, Client
from django.urls import reverse
from django.core import mail
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch, Mock

from core.models import TemporaryClimber
from core.services.climber_service import ClimberService


class EmailIntegrationTestCase(TestCase):
    """Integration tests for email functionality with new login system."""
    
    def setUp(self):
        """Set up test case."""
        self.client = Client()
        self.register_url = reverse('climber-register')
        self.login_url = reverse('climber-login')
        
    def test_complete_registration_email_login_flow(self):
        """Test complete flow from registration → email → verification → login."""
        # Step 1: Register new climber
        registration_data = {
            'name': 'Test User Integration',
            'email': 'integration@example.com',
            'phone': '+55 11 99999-9999'
        }
        
        response = self.client.post(self.register_url, registration_data)
        self.assertEqual(response.status_code, 200)
        
        # Check climber was created
        climber = TemporaryClimber.objects.get(email='integration@example.com')
        self.assertFalse(climber.email_verified)
        
        # Step 2: Check email was sent
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertIn('ClimaCocal', email.subject)
        self.assertIn('integration@example.com', email.to)
        
        # Check email contains login instructions
        self.assertIn('/escaladores/login/', email.body)
        self.assertIn('Digite: integration@example.com', email.body)
        self.assertIn('Redirecionamento automático', email.body)
        
        # Step 3: Simulate email verification
        verification_response = self.client.get(
            reverse('verify-email', kwargs={'token': str(climber.email_token)})
        )
        self.assertEqual(verification_response.status_code, 200)
        
        # Check climber is now verified
        climber.refresh_from_db()
        self.assertTrue(climber.email_verified)
        
        # Step 4: Test login with verified email
        login_response = self.client.post(self.login_url, {
            'email': 'integration@example.com'
        })
        self.assertRedirects(login_response, reverse('climber-access'))
        
        # Check session was created
        session = self.client.session
        self.assertEqual(session['climber_email'], 'integration@example.com')
        self.assertEqual(session['climber_id'], climber.id)

    def test_email_template_contains_correct_instructions(self):
        """Test that email template contains updated login instructions."""
        # Create climber
        climber = TemporaryClimber.objects.create(
            name='Template Test',
            email='template@example.com',
            email_verified=False
        )
        
        # Mock request for email sending
        from django.test import RequestFactory
        factory = RequestFactory()
        request = factory.get('/')
        request.META['HTTP_HOST'] = 'testserver'
        request.is_secure = lambda: False
        
        # Send verification email
        ClimberService.send_verification_email(climber, request)
        
        # Check email content
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        
        # Check for new login instructions
        self.assertIn('https://climacocal.com.br/escaladores/login/', email.body)
        self.assertIn('Digite: template@example.com', email.body)
        self.assertIn('Clique: "Entrar"', email.body)
        self.assertIn('Redirecionamento automático para página de streaming', email.body)

    def test_login_after_system_restart_simulation(self):
        """Test that login works after system restart (session cleared)."""
        # Create verified climber
        climber = TemporaryClimber.objects.create(
            name='Restart Test',
            email='restart@example.com',
            email_verified=True,
            access_until=timezone.now() + timedelta(hours=24)
        )
        
        # Simulate system restart by clearing session
        self.client.logout()
        
        # Try to access streaming directly (should redirect to login)
        access_response = self.client.get(reverse('climber-access'))
        self.assertRedirects(access_response, reverse('climber-login'))
        
        # Login should work
        login_response = self.client.post(self.login_url, {
            'email': 'restart@example.com'
        })
        self.assertRedirects(login_response, reverse('climber-access'))
        
        # Now access should work
        access_response = self.client.get(reverse('climber-access'))
        self.assertEqual(access_response.status_code, 200)

    def test_email_html_template_formatting(self):
        """Test that HTML email template is properly formatted."""
        # Create climber
        climber = TemporaryClimber.objects.create(
            name='HTML Test',
            email='html@example.com',
            email_verified=False
        )
        
        # Mock request
        from django.test import RequestFactory
        factory = RequestFactory()
        request = factory.get('/')
        request.META['HTTP_HOST'] = 'testserver'
        request.is_secure = lambda: False
        
        # Send email
        ClimberService.send_verification_email(climber, request)
        
        # Check HTML content
        email = mail.outbox[0]
        html_content = email.alternatives[0][0] if email.alternatives else None
        
        if html_content:
            # Check for key HTML elements
            self.assertIn('<h3>🎯 Instruções após verificação:</h3>', html_content)
            self.assertIn('https://climacocal.com.br/escaladores/login/', html_content)
            self.assertIn('Redirecionamento automático para página de streaming', html_content)
            self.assertIn('ClimaCocal', html_content)

    def test_case_insensitive_email_handling(self):
        """Test that email handling is case insensitive throughout the flow."""
        # Register with mixed case email
        registration_data = {
            'name': 'Case Test',
            'email': 'CaseTest@Example.Com',
            'phone': '+55 11 99999-9999'
        }
        
        response = self.client.post(self.register_url, registration_data)
        self.assertEqual(response.status_code, 200)
        
        # Check email was stored in lowercase
        climber = TemporaryClimber.objects.get(email='casetest@example.com')
        
        # Verify email
        verification_response = self.client.get(
            reverse('verify-email', kwargs={'token': str(climber.email_token)})
        )
        self.assertEqual(verification_response.status_code, 200)
        
        # Login with different case
        login_response = self.client.post(self.login_url, {
            'email': 'CASETEST@EXAMPLE.COM'
        })
        self.assertRedirects(login_response, reverse('climber-access'))

    def test_expired_access_handling_in_email_flow(self):
        """Test handling of expired access during email flow."""
        # Create climber with expired access
        climber = TemporaryClimber.objects.create(
            name='Expired Test',
            email='expired@example.com',
            email_verified=True,
            access_until=timezone.now() - timedelta(hours=1)
        )
        
        # Try to login
        login_response = self.client.post(self.login_url, {
            'email': 'expired@example.com'
        })
        
        # Should stay on login page with error
        self.assertEqual(login_response.status_code, 200)
        self.assertContains(login_response, 'acesso temporário expirou')
        
    def test_multiple_verification_attempts(self):
        """Test that multiple verification attempts work correctly."""
        # Create climber
        climber = TemporaryClimber.objects.create(
            name='Multi Test',
            email='multi@example.com',
            email_verified=False
        )
        
        # First verification
        verification_response = self.client.get(
            reverse('verify-email', kwargs={'token': str(climber.email_token)})
        )
        self.assertEqual(verification_response.status_code, 200)
        
        # Second verification (should still work)
        verification_response2 = self.client.get(
            reverse('verify-email', kwargs={'token': str(climber.email_token)})
        )
        self.assertEqual(verification_response2.status_code, 200)
        
        # Login should work
        login_response = self.client.post(self.login_url, {
            'email': 'multi@example.com'
        })
        self.assertRedirects(login_response, reverse('climber-access'))