"""
Test suite for Climber Access with Streaming Integration.

Tests the integration between climber authentication and streaming access,
ensuring that verified climbers can access the streaming service.
"""

import json
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client
from django.urls import reverse
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
import uuid

from core.models import TemporaryClimber
from core.services.climber_service import ClimberService
from core.services.payment_service import PaymentService


class ClimberStreamingAccessTest(TestCase):
    """Test streaming access for verified climbers."""
    
    def setUp(self):
        """Set up test client and clear cache."""
        self.client = Client()
        cache.clear()
        
        # Create a verified climber for testing
        self.climber = TemporaryClimber.objects.create(
            name='Test Climber',
            email='test@example.com',
            phone='11999999999',
            email_verified=True,
            email_token=uuid.uuid4(),
            access_until=timezone.now() + timedelta(days=30)
        )
    
    def tearDown(self):
        """Clean up after tests."""
        cache.clear()
        TemporaryClimber.objects.all().delete()
    
    def test_climber_access_without_login_redirects(self):
        """Test that unauthenticated access redirects to login."""
        response = self.client.get(reverse('climber-access'))
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('/escaladores/login/', response.url)
    
    def test_climber_access_with_login_shows_page(self):
        """Test that authenticated climber can access the page."""
        # Login the climber
        session = self.client.session
        session['climber_id'] = self.climber.id
        session['climber_name'] = self.climber.name
        session['climber_access_until'] = '2025-11-11'
        session.save()
        
        response = self.client.get(reverse('climber-access'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'climber/access.html')
        self.assertIn('Test Climber', response.content.decode())
    
    def test_climber_access_sets_payment_status_for_streaming(self):
        """Test that climber access page sets payment status for streaming."""
        # Login the climber
        session = self.client.session
        session['climber_id'] = self.climber.id
        session['climber_name'] = self.climber.name
        session['climber_access_until'] = '2025-11-11'
        session.save()
        
        # Access the page
        response = self.client.get(reverse('climber-access'))
        
        self.assertEqual(response.status_code, 200)
        
        # Check that payment status is set in cache for streaming
        payment_status = cache.get('payment_status')
        self.assertEqual(payment_status, 'approved')
    
    def test_streaming_api_works_after_climber_access(self):
        """Test that streaming API recognizes climber access."""
        # Login the climber
        session = self.client.session
        session['climber_id'] = self.climber.id
        session['climber_name'] = self.climber.name
        session['climber_access_until'] = '2025-11-11'
        session.save()
        
        # Access the climber page (should set payment status)
        response = self.client.get(reverse('climber-access'))
        self.assertEqual(response.status_code, 200)
        
        # Now check streaming API status
        response = self.client.get('/streaming/api/status/')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['has_access'])
        self.assertEqual(data['user_type'], 'climber')
        self.assertEqual(data['climber_name'], 'Test Climber')
    
    def test_test_payment_direct_vs_climber_access_consistency(self):
        """Test that both endpoints provide similar streaming access."""
        # Test 1: test-payment-direct
        response1 = self.client.get('/test-payment-direct/')
        self.assertEqual(response1.status_code, 200)
        
        # Check cache after test-payment-direct
        payment_status1 = cache.get('payment_status')
        self.assertEqual(payment_status1, 'approved')
        
        # Clear cache for second test
        cache.clear()
        
        # Test 2: climber access with login
        session = self.client.session
        session['climber_id'] = self.climber.id
        session['climber_name'] = self.climber.name
        session['climber_access_until'] = '2025-11-11'
        session.save()
        
        response2 = self.client.get(reverse('climber-access'))
        self.assertEqual(response2.status_code, 200)
        
        # Check cache after climber access
        payment_status2 = cache.get('payment_status')
        self.assertEqual(payment_status2, 'approved')
        
        # Both should set the same payment status
        self.assertEqual(payment_status1, payment_status2)
    
    def test_climber_login_and_access_flow(self):
        """Test complete flow from login to streaming access."""
        # Step 1: Login
        response = self.client.post(reverse('climber-login'), {
            'email': 'test@example.com'
        })
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/escaladores/acesso/')
        
        # Step 2: Access page (follows redirect)
        response = self.client.get(response.url)
        self.assertEqual(response.status_code, 200)
        
        # Step 3: Verify streaming access
        payment_status = cache.get('payment_status')
        self.assertEqual(payment_status, 'approved')
        
        # Step 4: Test streaming API
        response = self.client.get('/streaming/api/status/')
        data = json.loads(response.content)
        self.assertTrue(data['has_access'])
    
    def test_expired_climber_cannot_access_streaming(self):
        """Test that expired climber cannot access streaming."""
        # Create expired climber
        expired_climber = TemporaryClimber.objects.create(
            name='Expired Climber',
            email='expired@example.com',
            phone='11888888888',
            email_verified=True,
            email_token=uuid.uuid4(),
            access_until=timezone.now() - timedelta(days=1)  # Expired
        )
        
        # Try to login
        response = self.client.post(reverse('climber-login'), {
            'email': 'expired@example.com'
        })
        
        # Should not redirect to access page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'climber/login.html')
        self.assertIn('acesso temporário expirou', response.content.decode())
        
        # Payment status should not be set
        payment_status = cache.get('payment_status')
        self.assertIsNone(payment_status)
    
    def test_unverified_climber_cannot_access_streaming(self):
        """Test that unverified climber cannot access streaming."""
        # Create unverified climber
        unverified_climber = TemporaryClimber.objects.create(
            name='Unverified Climber',
            email='unverified@example.com',
            phone='11777777777',
            email_verified=False,  # Not verified
            email_token=uuid.uuid4(),
            access_until=timezone.now() + timedelta(days=30)
        )
        
        # Try to login
        response = self.client.post(reverse('climber-login'), {
            'email': 'unverified@example.com'
        })
        
        # Should not redirect to access page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'climber/login.html')
        self.assertIn('não encontrado ou não verificado', response.content.decode())
        
        # Payment status should not be set
        payment_status = cache.get('payment_status')
        self.assertIsNone(payment_status)
    
    def test_climber_logout_clears_streaming_access(self):
        """Test that logout clears streaming access."""
        # Login first
        session = self.client.session
        session['climber_id'] = self.climber.id
        session['climber_name'] = self.climber.name
        session['climber_access_until'] = '2025-11-11'
        session.save()
        
        # Access to set payment status
        self.client.get(reverse('climber-access'))
        
        # Verify payment status is set
        self.assertEqual(cache.get('payment_status'), 'approved')
        
        # Logout
        response = self.client.get(reverse('climber-logout'))
        self.assertEqual(response.status_code, 302)
        
        # Check that payment status is cleared
        payment_status = cache.get('payment_status')
        self.assertIn(payment_status, [None, 'pending', 'failure'])
        
        # Session should be cleared
        self.assertNotIn('climber_id', self.client.session)


class StreamingAPIClimberIntegrationTest(TestCase):
    """Test streaming API integration with climber system."""
    
    def setUp(self):
        """Set up test environment."""
        self.client = Client()
        cache.clear()
        
        # Create test climber
        self.climber = TemporaryClimber.objects.create(
            name='Stream Tester',
            email='stream@test.com',
            phone='11666666666',
            email_verified=True,
            email_token=uuid.uuid4(),
            access_until=timezone.now() + timedelta(days=30)
        )
    
    def test_streaming_status_api_with_climber_session(self):
        """Test streaming status API recognizes climber session."""
        # Setup climber session
        session = self.client.session
        session['climber_id'] = self.climber.id
        session['climber_name'] = self.climber.name
        session['climber_access_until'] = '2025-11-11'
        session.save()
        
        # Access climber page to set payment status
        self.client.get(reverse('climber-access'))
        
        # Check streaming status
        response = self.client.get('/streaming/api/status/')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertTrue(data['has_access'])
        self.assertEqual(data['user_type'], 'climber')
        self.assertEqual(data['climber_name'], 'Stream Tester')
        self.assertIn('access_until', data)
    
    def test_streaming_playlist_access_with_climber(self):
        """Test that climber can access streaming playlist."""
        # Setup climber session
        session = self.client.session
        session['climber_id'] = self.climber.id
        session['climber_name'] = self.climber.name
        session['climber_access_until'] = '2025-11-11'
        session.save()
        
        # Access climber page to set payment status
        self.client.get(reverse('climber-access'))
        
        # Try to access streaming playlist
        response = self.client.get('/streaming/stream.m3u8')
        
        # Should either return playlist or 404 if stream not active
        # but should NOT return 403 Forbidden
        self.assertIn(response.status_code, [200, 404])
        self.assertNotEqual(response.status_code, 403)