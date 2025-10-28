"""
ClimaCocal Test Suite Package

This package contains comprehensive tests for the ClimaCocal application,
including unit tests, integration tests, and system-wide tests.

Test Organization:
- test_climber_*: Climber registration, login, and access functionality
- test_email_*: Email functionality and integration
- test_system_*: System-wide integration tests
- test_streaming_*: Streaming functionality tests
- test_payment_*: Payment system tests
- test_unified_suite: Comprehensive test orchestration

Usage:
    # Run all tests
    python manage.py test
    
    # Run specific test module
    python manage.py test tests.test_climber_login
    
    # Run unified test suite
    python manage.py test tests.test_unified_suite
"""

# Test suite metadata
__version__ = '2.2.0'
__author__ = 'ClimaCocal Development Team'
__description__ = 'Comprehensive test suite for ClimaCocal application'

# Test categories
TEST_CATEGORIES = {
    'unit': [
        'test_climber_service',
        'test_climber_login',
        'test_weather_service',
        'test_payment_service'
    ],
    'integration': [
        'test_climber_views',
        'test_email_integration',
        'test_system_integration',
        'test_streaming_views'
    ],
    'e2e': [
        'test_e2e_playwright'
    ],
    'unified': [
        'test_unified_suite'
    ]
}

# Quality metrics targets
QUALITY_TARGETS = {
    'test_coverage': 85,  # Minimum test coverage percentage
    'test_count': 150,    # Minimum number of tests
    'max_test_time': 60,  # Maximum test suite execution time (seconds)
    'max_individual_test_time': 5  # Maximum individual test time (seconds)
}

def get_test_modules_by_category(category):
    """Get test modules for a specific category."""
    return TEST_CATEGORIES.get(category, [])

def get_all_test_modules():
    """Get all available test modules."""
    all_modules = []
    for modules in TEST_CATEGORIES.values():
        all_modules.extend(modules)
    return list(set(all_modules))  # Remove duplicates