#!/bin/bash

# Test Runner Script for ClimaCocal
# Tests the climber access and streaming integration

echo "==========================================="
echo "Running ClimaCocal Tests - Climber Streaming"
echo "==========================================="

# Go to project directory
cd /home/bruno/cocalClima

# Check if containers are running
echo "Checking Docker containers..."
docker-compose ps | grep climacocal

if [ $? -ne 0 ]; then
    echo "Container not running! Starting..."
    docker-compose up -d climacocal
    sleep 5
fi

# Run tests in Docker container
echo ""
echo "Running tests in Docker container..."
echo "-----------------------------------"

# Test 1: Check if climber access endpoint sets payment status
echo "Test 1: Climber Access Payment Status"
docker-compose exec -T climacocal python manage.py shell << EOF
from django.test import Client
from django.core.cache import cache
from core.models import TemporaryClimber
import uuid
from django.utils import timezone
from datetime import timedelta

# Clear cache
cache.clear()

# Create test climber
climber = TemporaryClimber.objects.create(
    name='Test Climber',
    email='test@example.com',
    phone='11999999999',
    email_verified=True,
    email_token=uuid.uuid4(),
    access_until=timezone.now() + timedelta(days=30)
)

# Create client and login
client = Client()
session = client.session
session['climber_id'] = climber.id
session['climber_name'] = climber.name
session['climber_access_until'] = '2025-11-11'
session.save()

# Access the page
response = client.get('/escaladores/acesso/')

# Check response
print(f"Response status: {response.status_code}")

# Check payment status in cache
payment_status = cache.get('payment_status')
print(f"Payment status in cache: {payment_status}")

# Check if it's approved
if payment_status == 'approved':
    print("✅ Test PASSED: Payment status correctly set to 'approved'")
else:
    print(f"❌ Test FAILED: Expected 'approved', got '{payment_status}'")

# Clean up
climber.delete()
cache.clear()
EOF

echo ""
echo "-----------------------------------"
echo "Test 2: Streaming API with Climber"

docker-compose exec -T climacocal python manage.py shell << EOF
from django.test import Client
from django.core.cache import cache
from core.models import TemporaryClimber
from core.services.payment_service import PaymentService
import uuid
import json
from django.utils import timezone
from datetime import timedelta

# Clear cache
cache.clear()

# Create test climber
climber = TemporaryClimber.objects.create(
    name='Stream Tester',
    email='stream@test.com',
    phone='11666666666',
    email_verified=True,
    email_token=uuid.uuid4(),
    access_until=timezone.now() + timedelta(days=30)
)

# Create client and setup session
client = Client()
session = client.session
session['climber_id'] = climber.id
session['climber_name'] = climber.name
session['climber_access_until'] = '2025-11-11'
session.save()

# Access climber page to set payment status
response = client.get('/escaladores/acesso/')

# Check streaming API status
api_response = client.get('/streaming/api/status/')
print(f"API Response status: {api_response.status_code}")

if api_response.status_code == 200:
    data = json.loads(api_response.content)
    print(f"Has access: {data.get('has_access')}")
    print(f"User type: {data.get('user_type')}")
    print(f"Climber name: {data.get('climber_name')}")
    
    if data.get('has_access') and data.get('user_type') == 'climber':
        print("✅ Test PASSED: Streaming API recognizes climber access")
    else:
        print("❌ Test FAILED: API did not recognize climber")
else:
    print(f"❌ Test FAILED: API returned {api_response.status_code}")

# Clean up
climber.delete()
cache.clear()
EOF

echo ""
echo "-----------------------------------"
echo "Test 3: Test Payment Direct Comparison"

docker-compose exec -T climacocal python manage.py shell << EOF
from django.test import Client
from django.core.cache import cache

# Test both endpoints
client = Client()

# Test 1: test-payment-direct
cache.clear()
response1 = client.get('/test-payment-direct/')
payment1 = cache.get('payment_status')
print(f"test-payment-direct status: {response1.status_code}, payment: {payment1}")

# Test 2: Create climber and test access
cache.clear()
from core.models import TemporaryClimber
import uuid
from django.utils import timezone
from datetime import timedelta

climber = TemporaryClimber.objects.create(
    name='Compare Test',
    email='compare@test.com',
    phone='11555555555',
    email_verified=True,
    email_token=uuid.uuid4(),
    access_until=timezone.now() + timedelta(days=30)
)

session = client.session
session['climber_id'] = climber.id
session['climber_name'] = climber.name
session['climber_access_until'] = '2025-11-11'
session.save()

response2 = client.get('/escaladores/acesso/')
payment2 = cache.get('payment_status')
print(f"escaladores/acesso status: {response2.status_code}, payment: {payment2}")

# Compare
if payment1 == 'approved' and payment2 == 'approved':
    print("✅ Test PASSED: Both endpoints set payment status correctly")
else:
    print(f"❌ Test FAILED: Inconsistent payment status")

# Clean up
climber.delete()
cache.clear()
EOF

echo ""
echo "==========================================="
echo "Test Summary"
echo "==========================================="
echo "All tests completed. Check results above."
echo ""
echo "To access the working stream:"
echo "1. https://climacocal.com.br/test-payment-direct/ (test mode)"
echo "2. https://climacocal.com.br/escaladores/acesso/ (after login)"
echo "==========================================="