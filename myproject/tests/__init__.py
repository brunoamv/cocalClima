"""
TDD Test Suite for ClimaCocal Application.

Test Categories:
- Unit Tests: Individual component testing
- Integration Tests: Component interaction testing  
- End-to-End Tests: Full workflow testing
- Service Tests: Business logic testing

Test Coverage Areas:
1. Streaming Services (Base - 988 linhas)
2. Core Views (354 linhas)
3. Payment Services (Updated for 3 reais/3 minutos)
4. Climber Registration System (New TDD)
5. Integration Workflows (New TDD)

New TDD Components:
- test_climber_service.py: ClimberService unit and integration tests
- test_climber_views.py: Climber views integration tests
- test_payment_service.py: Payment system tests (updated for 3 reais/3 minutos)

Usage:
    python manage.py test                           # Run all tests
    python manage.py test tests.test_climber_service # Run climber service tests
    python manage.py test tests.test_climber_views   # Run climber views tests
    
TDD Methodology:
    Red -> Green -> Refactor cycle applied to all new components
    Test-first development ensuring 90%+ coverage
"""