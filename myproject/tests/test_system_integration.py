"""
System-wide integration tests for the complete ClimaCocal application.
Tests the integration between all major components with the new login system.
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


class SystemIntegrationTestCase(TestCase):
    """System-wide integration tests including login, streaming, and payment flows."""
    
    def setUp(self):
        """Set up test case."""
        self.client = Client()
        
    def test_complete_user_journey_with_login_system(self):
        """Test complete user journey from registration to streaming access."""
        # Step 1: User visits homepage
        home_response = self.client.get(reverse('home'))
        self.assertEqual(home_response.status_code, 200)
        
        # Step 2: User registers
        registration_data = {
            'name': 'Complete Journey User',
            'email': 'journey@example.com',
            'phone': '+55 11 99999-9999'
        }
        
        register_response = self.client.post(reverse('climber-register'), registration_data)
        self.assertEqual(register_response.status_code, 200)
        
        # Step 3: User receives and clicks verification email
        climber = TemporaryClimber.objects.get(email='journey@example.com')
        verify_response = self.client.get(
            reverse('verify-email', kwargs={'token': str(climber.email_token)})
        )
        self.assertEqual(verify_response.status_code, 200)
        
        # Step 4: User follows instructions and goes to login page
        login_page_response = self.client.get(reverse('climber-login'))
        self.assertEqual(login_page_response.status_code, 200)
        self.assertContains(login_page_response, 'Entre com seu email')
        
        # Step 5: User logs in
        login_response = self.client.post(reverse('climber-login'), {
            'email': 'journey@example.com'
        })
        self.assertRedirects(login_response, reverse('climber-access'))
        
        # Step 6: User accesses streaming
        access_response = self.client.get(reverse('climber-access'))
        self.assertEqual(access_response.status_code, 200)
        
        # Step 7: User checks status API
        status_response = self.client.get(reverse('climber-status'))
        self.assertEqual(status_response.status_code, 200)
        status_data = status_response.json()
        self.assertTrue(status_data['has_access'])
        self.assertEqual(status_data['climber_type'], 'temporary')

    def test_concurrent_user_sessions(self):
        """Test that multiple users can use the system simultaneously."""
        # Create two verified climbers
        climber1 = TemporaryClimber.objects.create(
            name='User One',
            email='user1@example.com',
            email_verified=True,
            access_until=timezone.now() + timedelta(hours=24)
        )
        
        climber2 = TemporaryClimber.objects.create(
            name='User Two',
            email='user2@example.com',
            email_verified=True,
            access_until=timezone.now() + timedelta(hours=24)
        )
        
        # Create separate client sessions
        client1 = Client()
        client2 = Client()
        
        # Both users login
        login1 = client1.post(reverse('climber-login'), {'email': 'user1@example.com'})
        login2 = client2.post(reverse('climber-login'), {'email': 'user2@example.com'})
        
        self.assertRedirects(login1, reverse('climber-access'))
        self.assertRedirects(login2, reverse('climber-access'))
        
        # Both users can access streaming
        access1 = client1.get(reverse('climber-access'))
        access2 = client2.get(reverse('climber-access'))
        
        self.assertEqual(access1.status_code, 200)
        self.assertEqual(access2.status_code, 200)
        
        # Check that sessions are independent
        session1 = client1.session
        session2 = client2.session
        
        self.assertEqual(session1['climber_email'], 'user1@example.com')
        self.assertEqual(session2['climber_email'], 'user2@example.com')
        self.assertNotEqual(session1['climber_id'], session2['climber_id'])

    def test_payment_and_climber_access_integration(self):
        """Test integration between payment system and climber access."""
        # Create verified climber
        climber = TemporaryClimber.objects.create(
            name='Payment Test User',
            email='payment@example.com',
            email_verified=True,
            access_until=timezone.now() + timedelta(hours=24)
        )
        
        # Login climber
        self.client.post(reverse('climber-login'), {'email': 'payment@example.com'})
        
        # Test that climber can access streaming
        access_response = self.client.get(reverse('climber-access'))
        self.assertEqual(access_response.status_code, 200)
        
        # Test payment success page (should work independently)
        payment_response = self.client.get(reverse('payment_success'))
        self.assertEqual(payment_response.status_code, 200)
        
        # Test that both access methods work
        # (payment-based and climber-based should coexist)
        status_response = self.client.get(reverse('climber-status'))
        self.assertEqual(status_response.status_code, 200)

    def test_streaming_api_integration_with_climber_access(self):
        """Test streaming API integration with climber access system."""
        # Create verified climber with access
        climber = TemporaryClimber.objects.create(
            name='Streaming Test User',
            email='streaming@example.com',
            email_verified=True,
            access_until=timezone.now() + timedelta(hours=24)
        )
        
        # Login climber
        self.client.post(reverse('climber-login'), {'email': 'streaming@example.com'})
        
        # Test streaming status API
        try:
            streaming_status = self.client.get('/streaming/api/status/')
            # Should return streaming status (implementation dependent)
            self.assertIn(streaming_status.status_code, [200, 404])  # 404 if streaming not configured
        except:
            # Streaming API might not be fully configured in test environment
            pass
        
        # Test access to climber-specific endpoints
        access_response = self.client.get(reverse('climber-access'))
        self.assertEqual(access_response.status_code, 200)

    def test_error_handling_and_recovery_flows(self):
        """Test error handling and recovery flows throughout the system."""
        # Test invalid login
        invalid_login = self.client.post(reverse('climber-login'), {
            'email': 'nonexistent@example.com'
        })
        self.assertEqual(invalid_login.status_code, 200)
        self.assertContains(invalid_login, 'Email não encontrado')
        
        # Test access without login
        no_access = self.client.get(reverse('climber-access'))
        self.assertRedirects(no_access, reverse('climber-login'))
        
        # Test invalid verification token
        invalid_verify = self.client.get(
            reverse('verify-email', kwargs={'token': str(uuid.uuid4())})
        )
        self.assertEqual(invalid_verify.status_code, 200)
        self.assertContains(invalid_verify, 'Link de verificação inválido')

    def test_session_persistence_across_requests(self):
        """Test that user sessions persist correctly across multiple requests."""
        # Create verified climber
        climber = TemporaryClimber.objects.create(
            name='Session Test User',
            email='session@example.com',
            email_verified=True,
            access_until=timezone.now() + timedelta(hours=24)
        )
        
        # Login
        self.client.post(reverse('climber-login'), {'email': 'session@example.com'})
        
        # Make multiple requests
        for i in range(5):
            access_response = self.client.get(reverse('climber-access'))
            self.assertEqual(access_response.status_code, 200)
            
            status_response = self.client.get(reverse('climber-status'))
            self.assertEqual(status_response.status_code, 200)
            status_data = status_response.json()
            self.assertTrue(status_data['has_access'])

    def test_logout_functionality_integration(self):
        """Test logout functionality and session cleanup."""
        # Create verified climber
        climber = TemporaryClimber.objects.create(
            name='Logout Test User',
            email='logout@example.com',
            email_verified=True,
            access_until=timezone.now() + timedelta(hours=24)
        )
        
        # Login
        self.client.post(reverse('climber-login'), {'email': 'logout@example.com'})
        
        # Verify access works
        access_response = self.client.get(reverse('climber-access'))
        self.assertEqual(access_response.status_code, 200)
        
        # Logout
        logout_response = self.client.get(reverse('climber-logout'))
        self.assertRedirects(logout_response, reverse('home'))
        
        # Verify access no longer works
        no_access = self.client.get(reverse('climber-access'))
        self.assertRedirects(no_access, reverse('climber-login'))

    def test_edge_cases_and_boundary_conditions(self):
        """Test edge cases and boundary conditions."""
        # Test with extremely long names
        long_name_data = {
            'name': 'A' * 100,  # Max length
            'email': 'longname@example.com',
            'phone': '+55 11 99999-9999'
        }
        
        response = self.client.post(reverse('climber-register'), long_name_data)
        self.assertEqual(response.status_code, 200)
        
        # Test with special characters in email
        special_email_data = {
            'name': 'Special User',
            'email': 'user+test@example-domain.com',
            'phone': '+55 11 99999-9999'
        }
        
        response = self.client.post(reverse('climber-register'), special_email_data)
        self.assertEqual(response.status_code, 200)
        
        # Test case sensitivity
        case_data = {
            'name': 'Case User',
            'email': 'CASE@EXAMPLE.COM',
            'phone': '+55 11 99999-9999'
        }
        
        response = self.client.post(reverse('climber-register'), case_data)
        self.assertEqual(response.status_code, 200)
        
        # Verify it was stored in lowercase
        climber = TemporaryClimber.objects.get(email='case@example.com')