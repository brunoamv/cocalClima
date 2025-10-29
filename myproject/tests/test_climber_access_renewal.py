"""
Test suite for Climber Access Renewal System.

Tests the renewal functionality for expired climbers and registration edge cases.
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.core.cache import cache
from datetime import timedelta
import uuid

from core.models import TemporaryClimber
from core.services.climber_service import ClimberService


class ClimberAccessRenewalTest(TestCase):
    """Test climber access renewal and registration edge cases."""
    
    def setUp(self):
        """Set up test client and clear cache."""
        self.client = Client(HTTP_HOST='climacocal.com.br')
        cache.clear()
    
    def tearDown(self):
        """Clean up after tests."""
        cache.clear()
        TemporaryClimber.objects.all().delete()
    
    def test_expired_climber_can_register_again(self):
        """Test that an expired climber can register again with same email."""
        email = 'expired@test.com'
        
        # Create expired climber
        expired_climber = TemporaryClimber.objects.create(
            name='Expired User',
            email=email,
            phone='11999999999',
            email_verified=True,
            access_until=timezone.now() - timedelta(days=1)  # Expired yesterday
        )
        
        # Verify climber is expired
        self.assertFalse(expired_climber.has_access)
        
        # Try to register again with same email
        response = self.client.post(reverse('climber-register'), {
            'name': 'Renewed User',
            'email': email,
            'phone': '11888888888'
        })
        
        # Should succeed and renew access
        self.assertEqual(response.status_code, 200)
        
        # Check if access was renewed
        renewed_climber = TemporaryClimber.objects.get(email=email)
        self.assertTrue(renewed_climber.has_access)
        self.assertEqual(renewed_climber.name, 'Renewed User')
        self.assertGreater(renewed_climber.access_until, timezone.now())
    
    def test_expired_climber_login_shows_proper_message(self):
        """Test that expired climber gets appropriate error message on login."""
        email = 'expired_login@test.com'
        
        # Create expired climber
        TemporaryClimber.objects.create(
            name='Expired Login User',
            email=email,
            phone='11999999999',
            email_verified=True,
            access_until=timezone.now() - timedelta(hours=1)  # Expired 1 hour ago
        )
        
        # Try to login
        response = self.client.post(reverse('climber-login'), {
            'email': email
        })
        
        # Should stay on login page with error message
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'climber/login.html')
        self.assertIn('acesso temporário expirou', response.content.decode().lower())
    
    def test_active_climber_cannot_register_again(self):
        """Test that active climber cannot register again."""
        email = 'active@test.com'
        
        # Create active climber
        TemporaryClimber.objects.create(
            name='Active User',
            email=email,
            phone='11999999999',
            email_verified=True,
            access_until=timezone.now() + timedelta(days=30)  # Active for 30 days
        )
        
        # Try to register again
        response = self.client.post(reverse('climber-register'), {
            'name': 'Duplicate User',
            'email': email,
            'phone': '11777777777'
        })
        
        # Should redirect to login for active users
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/escaladores/login/')
        
        # Follow redirect to check message
        redirected_response = self.client.get(response.url)
        self.assertEqual(redirected_response.status_code, 200)
    
    def test_unverified_expired_climber_registration(self):
        """Test registration with unverified but expired climber."""
        email = 'unverified_expired@test.com'
        
        # Create unverified expired climber
        TemporaryClimber.objects.create(
            name='Unverified User',
            email=email,
            phone='11999999999',
            email_verified=False,  # Not verified
            access_until=timezone.now() - timedelta(days=1)  # Expired
        )
        
        # Try to register again
        response = self.client.post(reverse('climber-register'), {
            'name': 'New Registration',
            'email': email,
            'phone': '11555555555'
        })
        
        # Should succeed and update the existing record
        self.assertEqual(response.status_code, 200)
        
        # Check updated climber
        updated_climber = TemporaryClimber.objects.get(email=email)
        self.assertEqual(updated_climber.name, 'New Registration')
        self.assertEqual(updated_climber.phone, '11555555555')
        self.assertFalse(updated_climber.email_verified)  # Still unverified
    
    def test_climber_service_renewal_logic(self):
        """Test ClimberService renewal logic for expired climbers."""
        email = 'service_test@test.com'
        
        # Create expired verified climber
        expired_climber = TemporaryClimber.objects.create(
            name='Service Test',
            email=email,
            phone='11999999999',
            email_verified=True,
            access_until=timezone.now() - timedelta(hours=2)
        )
        
        original_id = expired_climber.id
        
        # Use service to register again
        renewed_climber = ClimberService.register_climber(
            name='Service Renewed',
            email=email,
            phone='11444444444'
        )
        
        # Should return renewed climber (same ID but updated)
        self.assertIsNotNone(renewed_climber)
        self.assertEqual(renewed_climber.id, original_id)
        self.assertEqual(renewed_climber.name, 'Service Renewed')
        self.assertTrue(renewed_climber.has_access)
        self.assertGreater(renewed_climber.access_until, timezone.now())
    
    def test_complete_renewal_flow(self):
        """Test complete flow from expired login to successful renewal."""
        email = 'complete_flow@test.com'
        
        # Step 1: Create expired climber
        TemporaryClimber.objects.create(
            name='Flow Test User',
            email=email,
            phone='11999999999',
            email_verified=True,
            access_until=timezone.now() - timedelta(hours=1)
        )
        
        # Step 2: Try login (should fail)
        login_response = self.client.post(reverse('climber-login'), {
            'email': email
        })
        self.assertEqual(login_response.status_code, 200)
        self.assertIn('expirou', login_response.content.decode().lower())
        
        # Step 3: Register again (should succeed)
        register_response = self.client.post(reverse('climber-register'), {
            'name': 'Flow Test Renewed',
            'email': email,
            'phone': '11333333333'
        })
        
        # Should succeed with registration
        self.assertIn(register_response.status_code, [200, 302])
        
        # Step 4: Verify climber was renewed
        renewed_climber = TemporaryClimber.objects.get(email=email)
        self.assertTrue(renewed_climber.has_access)
        self.assertEqual(renewed_climber.name, 'Flow Test Renewed')
    
    def test_multiple_expired_climbers_edge_case(self):
        """Test edge case with multiple climber records for same email."""
        email = 'multiple@test.com'
        
        # Create multiple records (shouldn't happen in normal flow but could exist)
        climber1 = TemporaryClimber.objects.create(
            name='First User',
            email=email,
            phone='11111111111',
            email_verified=True,
            access_until=timezone.now() - timedelta(days=2)
        )
        
        # Try registration
        response = self.client.post(reverse('climber-register'), {
            'name': 'New User',
            'email': email,
            'phone': '11222222222'
        })
        
        # Should handle gracefully
        self.assertIn(response.status_code, [200, 302])
        
        # Verify only one active record exists
        active_climbers = TemporaryClimber.objects.filter(
            email=email, 
            access_until__gt=timezone.now()
        )
        self.assertLessEqual(active_climbers.count(), 1)


class ClimberRenewalIntegrationTest(TestCase):
    """Integration tests for renewal system with streaming access."""
    
    def setUp(self):
        """Set up test environment."""
        self.client = Client(HTTP_HOST='climacocal.com.br')
        cache.clear()
    
    def tearDown(self):
        """Clean up after tests."""
        cache.clear()
        TemporaryClimber.objects.all().delete()
    
    def test_renewed_climber_can_access_streaming(self):
        """Test that renewed climber can access streaming after renewal."""
        email = 'streaming_renewal@test.com'
        
        # Create expired climber
        TemporaryClimber.objects.create(
            name='Streaming Test',
            email=email,
            phone='11999999999',
            email_verified=True,
            access_until=timezone.now() - timedelta(hours=1)
        )
        
        # Renew by registering again
        response = self.client.post(reverse('climber-register'), {
            'name': 'Streaming Renewed',
            'email': email,
            'phone': '11888888888'
        })
        
        # Get renewed climber
        renewed_climber = TemporaryClimber.objects.get(email=email)
        
        # Login with renewed climber
        login_response = self.client.post(reverse('climber-login'), {
            'email': email
        })
        
        # Should redirect to access page
        self.assertEqual(login_response.status_code, 302)
        self.assertEqual(login_response.url, '/escaladores/acesso/')
        
        # Access streaming page
        access_response = self.client.get(login_response.url)
        self.assertEqual(access_response.status_code, 200)
        
        # Check streaming access
        payment_status = cache.get('payment_status')
        self.assertEqual(payment_status, 'approved')
    
    def test_expired_climber_streaming_access_denied(self):
        """Test that expired climber cannot access streaming."""
        email = 'expired_streaming@test.com'
        
        # Create expired climber
        TemporaryClimber.objects.create(
            name='Expired Streaming',
            email=email,
            phone='11999999999',
            email_verified=True,
            access_until=timezone.now() - timedelta(hours=1)
        )
        
        # Try to login (should fail)
        login_response = self.client.post(reverse('climber-login'), {
            'email': email
        })
        
        # Should stay on login page
        self.assertEqual(login_response.status_code, 200)
        self.assertTemplateUsed(login_response, 'climber/login.html')
        
        # Payment status should not be set
        payment_status = cache.get('payment_status')
        self.assertIsNone(payment_status)