"""
TDD tests for ClimberService.

Following TDD principles:
1. Red: Write failing test first
2. Green: Make test pass with minimal code
3. Refactor: Improve code while keeping tests green

Test coverage:
- Climber registration with email validation
- Email token generation and verification
- Access control validation
- Error handling for invalid inputs
- Integration with existing access system
"""

import uuid
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from django.test import TestCase, override_settings
from django.core import mail
from django.utils import timezone
from django.core.cache import cache
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory

from core.models import TemporaryClimber
from core.services.climber_service import ClimberService
from streaming.services import PaymentValidationService


class ClimberServiceTestCase(TestCase):
    """Test case for ClimberService following TDD methodology."""

    def setUp(self):
        """Set up test environment - run before each test."""
        self.service = ClimberService()
        self.factory = RequestFactory()
        
        # Clear cache before each test
        cache.clear()
        
        # Test data
        self.valid_email = "test@example.com"
        self.valid_name = "Test Climber"
        self.invalid_email = "invalid-email"
        
        # Clear any existing test climbers
        TemporaryClimber.objects.filter(email=self.valid_email).delete()

    def tearDown(self):
        """Clean up after each test."""
        cache.clear()
        TemporaryClimber.objects.all().delete()

    def test_register_climber_success(self):
        """Test successful climber registration."""
        # ARRANGE - Set up test data
        name = self.valid_name
        email = self.valid_email
        
        # ACT - Execute the action being tested
        climber = self.service.register_climber(name, email)
        
        # ASSERT - Verify expected outcomes
        self.assertIsNotNone(climber)
        self.assertIsInstance(climber, TemporaryClimber)
        
        # Verify climber was created in database
        db_climber = TemporaryClimber.objects.get(email=email)
        self.assertEqual(db_climber.name, name)
        self.assertEqual(db_climber.email, email)
        self.assertFalse(db_climber.email_verified)
        self.assertIsNotNone(db_climber.email_token)

    def test_register_climber_duplicate_email(self):
        """Test registration with duplicate email returns existing climber."""
        # ARRANGE - Create existing climber
        existing_climber = TemporaryClimber.objects.create(
            name="Existing Climber",
            email=self.valid_email,
            email_verified=True
        )
        
        # ACT - Try to register with same email
        result = self.service.register_climber(self.valid_name, self.valid_email)
        
        # ASSERT - Verify returns existing climber
        self.assertIsNotNone(result)
        self.assertEqual(result.id, existing_climber.id)
        self.assertEqual(result.email, self.valid_email)

    def test_register_climber_invalid_email(self):
        """Test registration with invalid email still creates climber."""
        # ACT - Try to register with invalid email
        result = self.service.register_climber(self.valid_name, self.invalid_email)
        
        # ASSERT - Django allows invalid email format in model, so it should succeed
        self.assertIsNotNone(result)
        self.assertEqual(result.email, self.invalid_email)

    def test_register_climber_empty_name(self):
        """Test registration with empty name still creates climber."""
        # ACT - Try to register with empty name
        result = self.service.register_climber("", self.valid_email)
        
        # ASSERT - Django allows empty name, so it should succeed
        self.assertIsNotNone(result)
        self.assertEqual(result.name, "")

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_send_verification_email_success(self):
        """Test successful email verification sending."""
        # ARRANGE - Create test climber
        climber = TemporaryClimber.objects.create(
            name=self.valid_name,
            email=self.valid_email
        )
        request = self.factory.get('/')
        
        # ACT - Send verification email
        result = self.service.send_verification_email(climber, request)
        
        # ASSERT - Verify email was sent
        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)
        
        # Verify email content
        email = mail.outbox[0]
        self.assertEqual(email.to, [self.valid_email])
        self.assertIn('ClimaCocal', email.subject)
        self.assertIn(str(climber.email_token), email.body)

    def test_verify_email_success(self):
        """Test successful email verification."""
        # ARRANGE - Create unverified climber
        token = uuid.uuid4()
        climber = TemporaryClimber.objects.create(
            name=self.valid_name,
            email=self.valid_email,
            email_token=token,
            email_verified=False
        )
        
        # ACT - Verify email
        result = self.service.verify_email(str(token))
        
        # ASSERT - Verify success
        self.assertIsNotNone(result)
        self.assertIsInstance(result, TemporaryClimber)
        
        # Verify climber is now verified
        climber.refresh_from_db()
        self.assertTrue(climber.email_verified)
        self.assertIsNotNone(climber.email_verified_at)

    def test_verify_email_invalid_token(self):
        """Test email verification with invalid token fails."""
        # ACT - Try to verify with invalid token
        invalid_token = str(uuid.uuid4())
        result = self.service.verify_email(invalid_token)
        
        # ASSERT - Verify failure
        self.assertIsNone(result)

    def test_verify_email_already_verified(self):
        """Test verification of already verified email."""
        # ARRANGE - Create already verified climber
        token = uuid.uuid4()
        climber = TemporaryClimber.objects.create(
            name=self.valid_name,
            email=self.valid_email,
            email_token=token,
            email_verified=True,
            email_verified_at=timezone.now()
        )
        
        # ACT - Try to verify again (should return None because it looks for email_verified=False)
        result = self.service.verify_email(str(token))
        
        # ASSERT - Should return None since email is already verified
        self.assertIsNone(result)

    def test_check_climber_access_valid(self):
        """Test access check for valid verified climber."""
        # ARRANGE - Create verified climber and login
        climber = TemporaryClimber.objects.create(
            name=self.valid_name,
            email=self.valid_email,
            email_verified=True,
            email_verified_at=timezone.now(),
            is_active=True
        )
        
        request = self.factory.get('/')
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()
        request.session['climber_id'] = climber.id
        
        # ACT - Check access
        has_access = self.service.check_climber_access(request)
        
        # ASSERT - Should have access
        self.assertTrue(has_access)

    def test_check_climber_access_not_logged_in(self):
        """Test access check for non-logged-in user."""
        # ARRANGE - Create request without session
        request = self.factory.get('/')
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()
        
        # ACT - Check access
        has_access = self.service.check_climber_access(request)
        
        # ASSERT - Should not have access
        self.assertFalse(has_access)

    def test_check_climber_access_expired(self):
        """Test access check for climber with expired access."""
        # ARRANGE - Create climber with expired access
        past_date = timezone.now() - timedelta(days=1)  # Definitely in the past
        climber = TemporaryClimber.objects.create(
            name=self.valid_name,
            email=self.valid_email,
            email_verified=True,
            access_until=past_date,
            is_active=True
        )
        
        request = self.factory.get('/')
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()
        request.session['climber_id'] = climber.id
        
        # ACT - Check access
        has_access = self.service.check_climber_access(request)
        
        # ASSERT - Should not have access
        self.assertFalse(has_access)

    def test_check_climber_access_inactive(self):
        """Test access check for inactive climber."""
        # ARRANGE - Create inactive climber
        climber = TemporaryClimber.objects.create(
            name=self.valid_name,
            email=self.valid_email,
            email_verified=True,
            is_active=False
        )
        
        request = self.factory.get('/')
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()
        request.session['climber_id'] = climber.id
        
        # ACT - Check access
        has_access = self.service.check_climber_access(request)
        
        # ASSERT - Should not have access
        self.assertFalse(has_access)

    def test_check_climber_access_unverified_email(self):
        """Test access check for climber with unverified email."""
        # ARRANGE - Create unverified climber
        climber = TemporaryClimber.objects.create(
            name=self.valid_name,
            email=self.valid_email,
            email_verified=False,
            is_active=True
        )
        
        request = self.factory.get('/')
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()
        request.session['climber_id'] = climber.id
        
        # ACT - Check access
        has_access = self.service.check_climber_access(request)
        
        # ASSERT - Should not have access
        self.assertFalse(has_access)

    def test_login_climber(self):
        """Test climber login functionality."""
        # ARRANGE - Create verified climber
        climber = TemporaryClimber.objects.create(
            name=self.valid_name,
            email=self.valid_email,
            email_verified=True,
            is_active=True
        )
        
        request = self.factory.get('/')
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()
        
        # ACT - Login climber
        self.service.login_climber(request, climber)
        
        # ASSERT - Verify session contains climber
        self.assertEqual(request.session['climber_id'], climber.id)
        self.assertEqual(request.session['climber_email'], climber.email)

    def test_logout_climber(self):
        """Test climber logout functionality."""
        # ARRANGE - Setup logged in climber
        climber = TemporaryClimber.objects.create(
            name=self.valid_name,
            email=self.valid_email,
            email_verified=True
        )
        
        request = self.factory.get('/')
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()
        request.session['climber_id'] = climber.id
        request.session['climber_email'] = climber.email
        
        # ACT - Logout climber
        self.service.logout_climber(request)
        
        # ASSERT - Verify session is cleared
        self.assertNotIn('climber_id', request.session)
        self.assertNotIn('climber_email', request.session)

    def test_mark_access_updates_climber(self):
        """Test that access marking updates climber statistics."""
        # ARRANGE - Create climber
        climber = TemporaryClimber.objects.create(
            name=self.valid_name,
            email=self.valid_email,
            email_verified=True,
            access_count=0
        )
        
        # ACT - Mark access
        climber.mark_access()
        
        # ASSERT - Verify statistics updated
        climber.refresh_from_db()
        self.assertEqual(climber.access_count, 1)
        self.assertIsNotNone(climber.last_access)
        
        # Verify last_access is recent
        time_diff = timezone.now() - climber.last_access
        self.assertLess(time_diff.total_seconds(), 10)  # Within 10 seconds

    def test_get_verification_url(self):
        """Test verification URL generation."""
        # ARRANGE - Create climber
        climber = TemporaryClimber.objects.create(
            name=self.valid_name,
            email=self.valid_email
        )
        
        request = self.factory.get('/')
        request.META['HTTP_HOST'] = 'testserver'
        
        # ACT - Get verification URL
        url = climber.get_verification_url(request)
        
        # ASSERT - Verify URL format
        self.assertIn('verificar', url)  # Portuguese URL pattern
        self.assertIn(str(climber.email_token), url)
        self.assertIn('testserver', url)

    def test_has_valid_access_all_conditions(self):
        """Test has_valid_access method with various conditions."""
        # Test 1: Valid climber
        climber = TemporaryClimber.objects.create(
            name=self.valid_name,
            email=self.valid_email,
            email_verified=True,
            is_active=True
        )
        self.assertTrue(climber.has_valid_access())
        
        # Test 2: Inactive climber
        climber.is_active = False
        climber.save()
        self.assertFalse(climber.has_valid_access())
        
        # Test 3: Unverified email
        climber.is_active = True
        climber.email_verified = False
        climber.save()
        self.assertFalse(climber.has_valid_access())
        
        # Test 4: Expired access
        climber.email_verified = True
        climber.access_until = timezone.now() - timedelta(days=1)
        climber.save()
        self.assertFalse(climber.has_valid_access())


class ClimberServiceIntegrationTestCase(TestCase):
    """Integration tests for ClimberService with PaymentValidationService."""

    def setUp(self):
        """Set up test environment."""
        self.climber_service = ClimberService()
        self.factory = RequestFactory()
        cache.clear()

    def tearDown(self):
        """Clean up after tests."""
        cache.clear()
        TemporaryClimber.objects.all().delete()

    def test_hybrid_access_payment_only(self):
        """Test access with only payment approved."""
        # ARRANGE - Set payment approved
        cache.set("payment_status", "approved", 180)
        
        request = self.factory.get('/')
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()
        
        # ACT - Check hybrid access
        has_access = PaymentValidationService.is_access_granted(request)
        
        # ASSERT - Should have access via payment
        self.assertTrue(has_access)

    def test_hybrid_access_climber_only(self):
        """Test access with only climber registration."""
        # ARRANGE - Create verified climber and login
        climber = TemporaryClimber.objects.create(
            name="Test Climber",
            email="test@example.com",
            email_verified=True,
            is_active=True
        )
        
        request = self.factory.get('/')
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()
        request.session['climber_id'] = climber.id
        
        # Ensure no payment
        cache.set("payment_status", "pending", 180)
        
        # ACT - Check hybrid access
        has_access = PaymentValidationService.is_access_granted(request)
        
        # ASSERT - Should have access via climber
        self.assertTrue(has_access)

    def test_hybrid_access_both_sources(self):
        """Test access with both payment and climber registration."""
        # ARRANGE - Set both payment and climber
        cache.set("payment_status", "approved", 180)
        
        climber = TemporaryClimber.objects.create(
            name="Test Climber",
            email="test@example.com",
            email_verified=True,
            is_active=True
        )
        
        request = self.factory.get('/')
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()
        request.session['climber_id'] = climber.id
        
        # ACT - Check hybrid access
        has_access = PaymentValidationService.is_access_granted(request)
        
        # ASSERT - Should have access via both
        self.assertTrue(has_access)

    def test_hybrid_access_neither_source(self):
        """Test access with neither payment nor climber registration."""
        # ARRANGE - No payment, no climber
        cache.set("payment_status", "pending", 180)
        
        request = self.factory.get('/')
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()
        
        # ACT - Check hybrid access
        has_access = PaymentValidationService.is_access_granted(request)
        
        # ASSERT - Should not have access
        self.assertFalse(has_access)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_full_registration_flow(self):
        """Test complete registration flow from start to access."""
        # Step 1: Register climber
        climber = self.climber_service.register_climber("Test Climber", "test@example.com")
        self.assertIsNotNone(climber)
        self.assertIsInstance(climber, TemporaryClimber)
        
        # Step 2: Send verification email
        request = self.factory.get('/')
        email_sent = self.climber_service.send_verification_email(climber, request)
        self.assertTrue(email_sent)
        self.assertEqual(len(mail.outbox), 1)
        
        # Step 3: Verify email
        verify_result = self.climber_service.verify_email(str(climber.email_token))
        self.assertIsNotNone(verify_result)
        
        # Step 4: Login climber
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()
        self.climber_service.login_climber(request, climber)
        
        # Step 5: Check access
        has_access = PaymentValidationService.is_access_granted(request)
        self.assertTrue(has_access)
        
        # Step 6: Mark access and verify statistics
        initial_count = climber.access_count
        climber.mark_access()
        climber.refresh_from_db()
        self.assertEqual(climber.access_count, initial_count + 1)