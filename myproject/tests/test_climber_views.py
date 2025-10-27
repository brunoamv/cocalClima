"""
TDD integration tests for climber views.

Tests the complete view layer functionality including:
- HTTP request/response handling
- Template rendering
- Form validation
- URL routing
- Session management
- Error handling
"""

import json
import uuid
from unittest.mock import patch, MagicMock

from django.test import TestCase, Client, override_settings
from django.core import mail
from django.utils import timezone
from django.urls import reverse
from django.core.cache import cache
from django.contrib.sessions.models import Session

from core.models import TemporaryClimber


class ClimberViewsTestCase(TestCase):
    """Test case for climber-related views."""

    def setUp(self):
        """Set up test environment."""
        self.client = Client()
        cache.clear()
        
        # Test data
        self.valid_data = {
            'name': 'Test Climber',
            'email': 'test@example.com',
            'phone': '+5561999887766'
        }
        
        # Clear any existing test climbers
        TemporaryClimber.objects.filter(email=self.valid_data['email']).delete()

    def tearDown(self):
        """Clean up after tests."""
        cache.clear()
        TemporaryClimber.objects.all().delete()
        Session.objects.all().delete()

    def test_climber_register_get_request(self):
        """Test GET request to registration page."""
        # ACT - Make GET request
        response = self.client.get(reverse('climber-register'))
        
        # ASSERT - Verify response
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cadastro Escaladores')
        self.assertContains(response, 'form')
        self.assertContains(response, 'name="name"')
        self.assertContains(response, 'name="email"')
        self.assertContains(response, 'name="phone"')

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_climber_register_post_success(self):
        """Test successful POST request to registration."""
        # ACT - Submit registration form
        response = self.client.post(reverse('climber-register'), self.valid_data)
        
        # ASSERT - Verify success page rendered
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cadastro Realizado com Sucesso!')
        
        # Verify climber was created
        climber = TemporaryClimber.objects.get(email=self.valid_data['email'])
        self.assertEqual(climber.name, self.valid_data['name'])
        self.assertEqual(climber.phone, self.valid_data['phone'])
        self.assertFalse(climber.email_verified)
        
        # Verify email was sent
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, [self.valid_data['email']])
        self.assertIn('ClimaCocal', email.subject)

    def test_climber_register_post_duplicate_email(self):
        """Test registration with duplicate email."""
        # ARRANGE - Create existing climber
        TemporaryClimber.objects.create(
            name="Existing Climber",
            email=self.valid_data['email'],
            email_verified=True
        )
        
        # ACT - Try to register with same email
        response = self.client.post(reverse('climber-register'), self.valid_data)
        
        # ASSERT - Verify error response
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'já cadastrado')
        self.assertContains(response, 'alert-error')

    def test_climber_register_post_invalid_email(self):
        """Test registration with invalid email format."""
        # ARRANGE - Invalid email data
        invalid_data = self.valid_data.copy()
        invalid_data['email'] = 'invalid-email-format'
        
        # ACT - Submit invalid data
        response = self.client.post(reverse('climber-register'), invalid_data)
        
        # ASSERT - Verify error response
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'alert-error')

    def test_climber_register_post_missing_name(self):
        """Test registration with missing name."""
        # ARRANGE - Data without name
        invalid_data = self.valid_data.copy()
        del invalid_data['name']
        
        # ACT - Submit incomplete data
        response = self.client.post(reverse('climber-register'), invalid_data)
        
        # ASSERT - Verify error response
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'alert-error')

    def test_verify_email_success(self):
        """Test successful email verification."""
        # ARRANGE - Create unverified climber
        token = uuid.uuid4()
        climber = TemporaryClimber.objects.create(
            name=self.valid_data['name'],
            email=self.valid_data['email'],
            email_token=token,
            email_verified=False
        )
        
        # ACT - Verify email
        response = self.client.get(reverse('verify-email', kwargs={'token': str(token)}))
        
        # ASSERT - Verify response and verification success
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Email Verificado com Sucesso!')
        # Note: Template doesn't use Bootstrap alerts, uses custom styling
        
        # Verify climber is now verified
        climber.refresh_from_db()
        self.assertTrue(climber.email_verified)
        self.assertIsNotNone(climber.email_verified_at)

    def test_verify_email_invalid_token(self):
        """Test email verification with invalid token."""
        # ACT - Try to verify with invalid token
        invalid_token = str(uuid.uuid4())
        response = self.client.get(reverse('verify-email', kwargs={'token': invalid_token}))
        
        # ASSERT - Verify error response
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Erro na Verificação')
        # Note: Template doesn't use Bootstrap alerts, uses custom styling

    def test_climber_status_not_logged_in(self):
        """Test status page when not logged in."""
        # ACT - Access status page without login
        response = self.client.get(reverse('climber-status'))
        
        # ASSERT - Verify shows not logged in status (JSON API)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data.get('has_access', True))
        self.assertEqual(data.get('climber_type'), None)

    def test_climber_status_logged_in_unverified(self):
        """Test status page for logged in but unverified climber."""
        # ARRANGE - Create unverified climber and login
        climber = TemporaryClimber.objects.create(
            name=self.valid_data['name'],
            email=self.valid_data['email'],
            email_verified=False
        )
        
        session = self.client.session
        session['climber_id'] = climber.id
        session['climber_email'] = climber.email
        session.save()
        
        # ACT - Access status page
        response = self.client.get(reverse('climber-status'))
        
        # ASSERT - Verify shows verification needed (JSON API)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data.get('has_access', True))  # Unverified should not have access

    def test_climber_status_logged_in_verified(self):
        """Test status page for verified climber."""
        # ARRANGE - Create verified climber and login
        climber = TemporaryClimber.objects.create(
            name=self.valid_data['name'],
            email=self.valid_data['email'],
            email_verified=True,
            email_verified_at=timezone.now(),
            is_active=True
        )
        
        session = self.client.session
        session['climber_id'] = climber.id
        session['climber_email'] = climber.email
        session.save()
        
        # ACT - Access status page
        response = self.client.get(reverse('climber-status'))
        
        # ASSERT - Verify shows verified status (JSON API)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data.get('has_access', False))
        self.assertEqual(data.get('climber_type'), 'temporary')

    def test_climber_access_verified_user(self):
        """Test access page for verified climber."""
        # ARRANGE - Create verified climber and login
        climber = TemporaryClimber.objects.create(
            name=self.valid_data['name'],
            email=self.valid_data['email'],
            email_verified=True,
            is_active=True
        )
        
        session = self.client.session
        session['climber_id'] = climber.id
        session['climber_email'] = climber.email
        session.save()
        
        # ACT - Access the access page
        response = self.client.get(reverse('climber-access'))
        
        # ASSERT - Verify access granted
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Acesso Escalador Ativo')
        self.assertContains(response, 'Transmissão ao Vivo')
        
        # Verify access count was updated
        climber.refresh_from_db()
        self.assertEqual(climber.access_count, 1)
        self.assertIsNotNone(climber.last_access)

    def test_climber_access_unverified_user(self):
        """Test access page for unverified climber."""
        # ARRANGE - Create unverified climber and login
        climber = TemporaryClimber.objects.create(
            name=self.valid_data['name'],
            email=self.valid_data['email'],
            email_verified=False
        )
        
        session = self.client.session
        session['climber_id'] = climber.id
        session['climber_email'] = climber.email
        session.save()
        
        # ACT - Try to access
        response = self.client.get(reverse('climber-access'))
        
        # ASSERT - Verify access denied
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('climber-register'))

    def test_climber_access_not_logged_in(self):
        """Test access page when not logged in."""
        # ACT - Try to access without login
        response = self.client.get(reverse('climber-access'))
        
        # ASSERT - Verify redirect to register
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('climber-register'))

    def test_climber_logout(self):
        """Test climber logout functionality."""
        # ARRANGE - Login climber
        climber = TemporaryClimber.objects.create(
            name=self.valid_data['name'],
            email=self.valid_data['email'],
            email_verified=True
        )
        
        session = self.client.session
        session['climber_id'] = climber.id
        session['climber_email'] = climber.email
        session.save()
        
        # Verify initially logged in
        self.assertIn('climber_id', self.client.session)
        
        # ACT - Logout
        response = self.client.get(reverse('climber-logout'))
        
        # ASSERT - Verify logout and redirect
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('home'))
        
        # Verify session cleared
        self.assertNotIn('climber_id', self.client.session)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_resend_verification_success(self):
        """Test successful verification email resend."""
        # ARRANGE - Create unverified climber and login
        climber = TemporaryClimber.objects.create(
            name=self.valid_data['name'],
            email=self.valid_data['email'],
            email_verified=False
        )
        
        session = self.client.session
        session['climber_id'] = climber.id
        session['climber_email'] = climber.email
        session.save()
        
        # ACT - Request resend
        response = self.client.post(reverse('resend-verification'), {
            'email': climber.email
        })
        
        # ASSERT - Verify success response
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Email de verificação reenviado')
        
        # Verify email was sent
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, [climber.email])

    def test_resend_verification_not_logged_in(self):
        """Test resend verification when not logged in."""
        # ACT - Try to resend without login
        response = self.client.post(reverse('resend-verification'))
        
        # ASSERT - Verify template rendered (no redirect for unauthenticated)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Email é obrigatório')

    def test_resend_verification_already_verified(self):
        """Test resend verification for already verified climber."""
        # ARRANGE - Create verified climber and login
        climber = TemporaryClimber.objects.create(
            name=self.valid_data['name'],
            email=self.valid_data['email'],
            email_verified=True
        )
        
        session = self.client.session
        session['climber_id'] = climber.id
        session['climber_email'] = climber.email
        session.save()
        
        # ACT - Try to resend
        response = self.client.post(reverse('resend-verification'), {
            'email': climber.email
        })
        
        # ASSERT - Verify error message (already verified)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Email não encontrado ou já verificado')

    def test_climber_admin_stats_access(self):
        """Test admin stats page accessibility."""
        # ARRANGE - Create staff user
        from django.contrib.auth.models import User
        admin_user = User.objects.create_user('admin', 'admin@test.com', 'password')
        admin_user.is_staff = True
        admin_user.save()
        self.client.login(username='admin', password='password')
        
        # ACT - Access admin stats
        response = self.client.get(reverse('climber-admin-stats'))
        
        # ASSERT - Verify page loads (authentication handled by decorator if needed)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])

    def test_url_patterns_exist(self):
        """Test that all climber URL patterns are properly configured."""
        # Test all climber-related URL patterns
        urls_to_test = [
            'climber-register',
            'climber-status', 
            'climber-access',
            'climber-logout',
            'resend-verification',
            'climber-admin-stats'
        ]
        
        for url_name in urls_to_test:
            try:
                url = reverse(url_name)
                self.assertIsNotNone(url)
            except Exception as e:
                self.fail(f"URL pattern '{url_name}' not found: {e}")
        
        # Test URL with parameter
        test_token = str(uuid.uuid4())
        try:
            url = reverse('verify-email', kwargs={'token': test_token})
            self.assertIn(test_token, url)
        except Exception as e:
            self.fail(f"URL pattern 'verify-email' with token not found: {e}")


class ClimberViewsIntegrationTestCase(TestCase):
    """Integration tests combining views with services and models."""

    def setUp(self):
        """Set up test environment."""
        self.client = Client()
        cache.clear()

    def tearDown(self):
        """Clean up after tests."""
        cache.clear()
        TemporaryClimber.objects.all().delete()

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_complete_user_journey(self):
        """Test complete user journey from registration to access."""
        # Step 1: Register climber
        registration_data = {
            'name': 'Journey Test Climber',
            'email': 'journey@example.com',
            'phone': '+5561999887766'
        }
        
        response = self.client.post(reverse('climber-register'), registration_data)
        self.assertEqual(response.status_code, 200)  # Changed from 302 to 200 as view renders success page
        self.assertContains(response, 'Cadastro realizado')
        
        # Verify climber created
        climber = TemporaryClimber.objects.get(email=registration_data['email'])
        self.assertFalse(climber.email_verified)
        
        # Verify email sent
        self.assertEqual(len(mail.outbox), 1)
        
        # Step 2: Check status (unverified) - API returns JSON
        response = self.client.get(reverse('climber-status'))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data.get('has_access', True))
        
        # Step 3: Verify email
        response = self.client.get(reverse('verify-email', kwargs={'token': str(climber.email_token)}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Email Verificado com Sucesso!')
        
        # Verify climber is now verified
        climber.refresh_from_db()
        self.assertTrue(climber.email_verified)
        
        # Step 4: Check status (verified, logged in) - API returns JSON
        response = self.client.get(reverse('climber-status'))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data.get('has_access', False))
        
        # Step 5: Access streaming
        response = self.client.get(reverse('climber-access'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Transmissão ao Vivo')
        
        # Verify access was marked
        climber.refresh_from_db()
        self.assertEqual(climber.access_count, 1)
        self.assertIsNotNone(climber.last_access)
        
        # Step 6: Logout
        response = self.client.get(reverse('climber-logout'))
        self.assertEqual(response.status_code, 302)
        
        # Step 7: Check status (logged out) - API returns JSON
        response = self.client.get(reverse('climber-status'))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data.get('has_access', True))

    def test_expired_access_handling(self):
        """Test handling of climber with expired access."""
        from datetime import datetime, timedelta
        
        # Create climber with expired access
        past_date = datetime(2025, 10, 1, 23, 59, 59).replace(tzinfo=timezone.get_current_timezone())
        climber = TemporaryClimber.objects.create(
            name='Expired Climber',
            email='expired@example.com',
            email_verified=True,
            access_until=past_date,
            is_active=True
        )
        
        # Login climber
        session = self.client.session
        session['climber_id'] = climber.id
        session['climber_email'] = climber.email
        session.save()
        
        # Try to access streaming
        response = self.client.get(reverse('climber-access'))
        
        # Should be redirected due to expired access
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('climber-register'))

    def test_inactive_climber_handling(self):
        """Test handling of inactive climber."""
        # Create inactive climber
        climber = TemporaryClimber.objects.create(
            name='Inactive Climber',
            email='inactive@example.com',
            email_verified=True,
            is_active=False
        )
        
        # Login climber
        session = self.client.session
        session['climber_id'] = climber.id
        session['climber_email'] = climber.email
        session.save()
        
        # Try to access streaming
        response = self.client.get(reverse('climber-access'))
        
        # Should be redirected due to inactive status
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('climber-register'))

    def test_concurrent_access_tracking(self):
        """Test that concurrent access requests are handled correctly."""
        # Create verified climber
        climber = TemporaryClimber.objects.create(
            name='Concurrent Test',
            email='concurrent@example.com',
            email_verified=True,
            is_active=True,
            access_count=5,
            access_until=timezone.now() + timezone.timedelta(hours=1)  # Valid for 1 hour
        )
        
        # Login climber
        session = self.client.session
        session['climber_id'] = climber.id
        session['climber_email'] = climber.email
        session['climber_name'] = climber.name
        session['climber_access_until'] = climber.access_until.isoformat()
        session.save()
        
        # Multiple access requests (clear cache between requests to test real counting)
        from django.core.cache import cache
        for i in range(3):
            # Clear cache to ensure mark_access is called each time
            cache_key = f"climber_access_{climber.id}"
            cache.delete(cache_key)
            response = self.client.get(reverse('climber-access'))
            self.assertEqual(response.status_code, 200)
        
        # Verify access count increased correctly
        climber.refresh_from_db()
        self.assertEqual(climber.access_count, 8)  # 5 + 3