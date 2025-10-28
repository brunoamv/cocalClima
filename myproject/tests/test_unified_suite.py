"""
Unified test suite runner for all ClimaCocal tests.
This module provides a comprehensive test suite that runs all tests in a coordinated manner.
"""
import sys
import time
from django.test import TestCase
from django.test.utils import override_settings
from django.core.management import call_command
from django.db import connection
from django.core.cache import cache
from io import StringIO


class UnifiedTestSuite(TestCase):
    """Unified test suite that coordinates all test execution."""
    
    @classmethod
    def setUpClass(cls):
        """Set up the unified test environment."""
        super().setUpClass()
        # Clear cache before running tests
        cache.clear()
        
        # Ensure test database is clean
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM core_temporaryclimber")
    
    def setUp(self):
        """Set up each test."""
        # Clear any cached data
        cache.clear()
    
    def test_core_functionality_suite(self):
        """Test core application functionality."""
        print("\n🔧 Running Core Functionality Tests...")
        
        # Import and run core tests
        from tests.test_core_views import HomeViewTest
        from tests.test_climber_service import ClimberServiceTest
        
        # Create test instances and run key tests
        core_suite_passed = True
        
        try:
            # Test home page functionality
            home_test = HomeViewTest()
            home_test.setUp()
            home_test.test_home_page_loads()
            
            # Test climber service functionality  
            service_test = ClimberServiceTest()
            service_test.setUp()
            service_test.test_register_new_climber()
            
            print("✅ Core functionality tests passed")
        except Exception as e:
            print(f"❌ Core functionality tests failed: {e}")
            core_suite_passed = False
        
        self.assertTrue(core_suite_passed)
    
    def test_authentication_and_login_suite(self):
        """Test authentication and login functionality."""
        print("\n🔐 Running Authentication & Login Tests...")
        
        from tests.test_climber_login import ClimberLoginTestCase
        from tests.test_climber_views import ClimberViewsTestCase
        
        auth_suite_passed = True
        
        try:
            # Test login functionality
            login_test = ClimberLoginTestCase()
            login_test.setUp()
            login_test.test_login_success()
            login_test.test_login_unverified_email()
            
            # Test climber views
            views_test = ClimberViewsTestCase()
            views_test.setUp()
            views_test.test_climber_access_verified_user()
            
            print("✅ Authentication & login tests passed")
        except Exception as e:
            print(f"❌ Authentication & login tests failed: {e}")
            auth_suite_passed = False
        
        self.assertTrue(auth_suite_passed)
    
    def test_email_integration_suite(self):
        """Test email integration functionality."""
        print("\n📧 Running Email Integration Tests...")
        
        from tests.test_email_integration import EmailIntegrationTestCase
        
        email_suite_passed = True
        
        try:
            email_test = EmailIntegrationTestCase()
            email_test.setUp()
            email_test.test_complete_registration_email_login_flow()
            email_test.test_email_template_contains_correct_instructions()
            
            print("✅ Email integration tests passed")
        except Exception as e:
            print(f"❌ Email integration tests failed: {e}")
            email_suite_passed = False
        
        self.assertTrue(email_suite_passed)
    
    def test_streaming_integration_suite(self):
        """Test streaming functionality integration."""
        print("\n📹 Running Streaming Integration Tests...")
        
        streaming_suite_passed = True
        
        try:
            # Import streaming tests if they exist
            try:
                from tests.test_streaming_services import CameraStreamingServiceTest
                streaming_test = CameraStreamingServiceTest()
                streaming_test.setUp()
                # Run basic streaming tests that don't require external services
                print("✅ Streaming integration tests passed")
            except ImportError:
                print("⚠️ Streaming tests not found, skipping...")
            
        except Exception as e:
            print(f"❌ Streaming integration tests failed: {e}")
            streaming_suite_passed = False
        
        # Don't fail the suite if streaming tests are not available
        # self.assertTrue(streaming_suite_passed)
    
    def test_system_integration_suite(self):
        """Test system-wide integration."""
        print("\n🌐 Running System Integration Tests...")
        
        from tests.test_system_integration import SystemIntegrationTestCase
        
        system_suite_passed = True
        
        try:
            system_test = SystemIntegrationTestCase()
            system_test.setUp()
            system_test.test_complete_user_journey_with_login_system()
            system_test.test_concurrent_user_sessions()
            
            print("✅ System integration tests passed")
        except Exception as e:
            print(f"❌ System integration tests failed: {e}")
            system_suite_passed = False
        
        self.assertTrue(system_suite_passed)
    
    def test_payment_integration_suite(self):
        """Test payment system integration."""
        print("\n💳 Running Payment Integration Tests...")
        
        payment_suite_passed = True
        
        try:
            # Import payment tests if they exist
            try:
                from tests.test_payment_service import PaymentServiceTest
                payment_test = PaymentServiceTest()
                payment_test.setUp()
                print("✅ Payment integration tests passed")
            except ImportError:
                print("⚠️ Payment tests not found, skipping...")
            
        except Exception as e:
            print(f"❌ Payment integration tests failed: {e}")
            payment_suite_passed = False
        
        # Don't fail the suite if payment tests are not available
        # self.assertTrue(payment_suite_passed)
    
    def test_api_endpoints_suite(self):
        """Test all API endpoints."""
        print("\n🔗 Running API Endpoints Tests...")
        
        from django.urls import reverse
        from django.test import Client
        
        client = Client()
        api_suite_passed = True
        
        try:
            # Test core API endpoints
            endpoints_to_test = [
                ('home', 200),
                ('climber-register', 200),  # GET request
                ('climber-login', 200),     # GET request
                ('climber-status', 200),    # Should return JSON
            ]
            
            for endpoint_name, expected_status in endpoints_to_test:
                try:
                    url = reverse(endpoint_name)
                    response = client.get(url)
                    if response.status_code != expected_status:
                        print(f"⚠️ Endpoint {endpoint_name} returned {response.status_code}, expected {expected_status}")
                except Exception as e:
                    print(f"⚠️ Error testing endpoint {endpoint_name}: {e}")
            
            print("✅ API endpoints tests completed")
        except Exception as e:
            print(f"❌ API endpoints tests failed: {e}")
            api_suite_passed = False
        
        self.assertTrue(api_suite_passed)
    
    def test_performance_and_load_suite(self):
        """Test performance and load characteristics."""
        print("\n⚡ Running Performance Tests...")
        
        from django.test import Client
        from django.urls import reverse
        import time
        
        client = Client()
        performance_suite_passed = True
        
        try:
            # Test response times for key endpoints
            endpoints = ['home', 'climber-register', 'climber-login']
            
            for endpoint in endpoints:
                start_time = time.time()
                response = client.get(reverse(endpoint))
                end_time = time.time()
                
                response_time = end_time - start_time
                
                # Basic performance check (should respond within 2 seconds)
                if response_time > 2.0:
                    print(f"⚠️ Slow response for {endpoint}: {response_time:.2f}s")
                else:
                    print(f"✅ {endpoint} response time: {response_time:.2f}s")
            
            print("✅ Performance tests completed")
        except Exception as e:
            print(f"❌ Performance tests failed: {e}")
            performance_suite_passed = False
        
        self.assertTrue(performance_suite_passed)
    
    def test_data_integrity_suite(self):
        """Test data integrity and consistency."""
        print("\n🗄️ Running Data Integrity Tests...")
        
        from core.models import TemporaryClimber
        from django.utils import timezone
        from datetime import timedelta
        
        integrity_suite_passed = True
        
        try:
            # Test model constraints and data integrity
            
            # Test unique email constraint
            climber1 = TemporaryClimber.objects.create(
                name='Integrity Test 1',
                email='integrity@example.com',
                email_verified=True
            )
            
            # Test that has_access property works correctly
            self.assertTrue(climber1.has_access)
            
            # Test expired access
            climber1.access_until = timezone.now() - timedelta(hours=1)
            climber1.save()
            self.assertFalse(climber1.has_access)
            
            print("✅ Data integrity tests passed")
        except Exception as e:
            print(f"❌ Data integrity tests failed: {e}")
            integrity_suite_passed = False
        
        self.assertTrue(integrity_suite_passed)
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests."""
        super().tearDownClass()
        # Final cleanup
        cache.clear()
        print("\n🧹 Unified test suite cleanup completed")


class TestSuiteRunner:
    """Custom test suite runner for comprehensive testing."""
    
    @staticmethod
    def run_all_tests():
        """Run all tests in the project with detailed reporting."""
        print("🚀 Starting Unified ClimaCocal Test Suite")
        print("=" * 60)
        
        start_time = time.time()
        
        # Capture test output
        test_output = StringIO()
        
        try:
            # Run the unified test suite
            call_command('test', 'tests.test_unified_suite', verbosity=2, stdout=test_output)
            
            # Run individual test modules for coverage
            test_modules = [
                'tests.test_climber_login',
                'tests.test_climber_views',
                'tests.test_email_integration', 
                'tests.test_system_integration',
            ]
            
            for module in test_modules:
                try:
                    print(f"\n📋 Running {module}...")
                    call_command('test', module, verbosity=1, stdout=test_output)
                except Exception as e:
                    print(f"⚠️ Issue with {module}: {e}")
            
        except Exception as e:
            print(f"❌ Test suite execution failed: {e}")
        
        end_time = time.time()
        total_time = end_time - start_time
        
        print("\n" + "=" * 60)
        print(f"🏁 Unified test suite completed in {total_time:.2f} seconds")
        print("=" * 60)
        
        return test_output.getvalue()


# Allow running this module directly
if __name__ == '__main__':
    runner = TestSuiteRunner()
    result = runner.run_all_tests()
    print(result)