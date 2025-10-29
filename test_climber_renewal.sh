#!/bin/bash

# Test script for Climber Access Renewal System
# Tests the complete flow from expired climber to successful renewal

echo "=========================================="
echo "Testing ClimaCocal Climber Renewal System"
echo "=========================================="

cd /home/bruno/cocalClima

echo ""
echo "Test 1: Existing Expired Climbers"
echo "--------------------------------"

docker-compose exec -T climacocal python manage.py shell << 'EOF'
from core.models import TemporaryClimber
from django.utils import timezone

print("Current expired climbers in database:")
expired = TemporaryClimber.objects.filter(
    email_verified=True,
    access_until__lt=timezone.now()
)

for climber in expired:
    days_expired = (timezone.now() - climber.access_until).days
    print(f"  - {climber.name} ({climber.email}) - Expired {days_expired} days ago")

if expired.count() == 0:
    print("  No expired climbers found.")
EOF

echo ""
echo "Test 2: Testing Registration with Expired Climber"
echo "------------------------------------------------"

docker-compose exec -T climacocal python manage.py shell << 'EOF'
from django.test import Client
from django.core.cache import cache
from core.models import TemporaryClimber
from django.utils import timezone
from datetime import timedelta

# Create expired climber for testing
cache.clear()
TemporaryClimber.objects.filter(email='renewal_test@example.com').delete()

expired_climber = TemporaryClimber.objects.create(
    name='Expired Test User',
    email='renewal_test@example.com',
    phone='11999999999',
    email_verified=True,
    access_until=timezone.now() - timedelta(hours=2)  # Expired 2 hours ago
)

print(f"Created expired climber: {expired_climber.name}")
print(f"  Email: {expired_climber.email}")
print(f"  Access until: {expired_climber.access_until}")
print(f"  Has access: {expired_climber.has_access}")

# Try to register again with same email
client = Client(HTTP_HOST='climacocal.com.br')

print("\nTrying to register with same email (should allow renewal)...")
response = client.post('/escaladores/cadastro/', {
    'name': 'Renewed Test User', 
    'email': 'renewal_test@example.com',
    'phone': '11888888888'
})

print(f"Registration response status: {response.status_code}")

# Check if climber was renewed
renewed_climber = TemporaryClimber.objects.get(email='renewal_test@example.com')
print(f"\nAfter renewal attempt:")
print(f"  Name: {renewed_climber.name}")
print(f"  Access until: {renewed_climber.access_until}")
print(f"  Has access: {renewed_climber.has_access}")

if renewed_climber.has_access:
    print("  ✅ SUCCESS: Climber access was renewed!")
else:
    print("  ❌ FAILED: Climber access was not renewed")

# Clean up
expired_climber.delete()
EOF

echo ""
echo "Test 3: Login with Expired Climber (Should Fail)"
echo "-----------------------------------------------"

docker-compose exec -T climacocal python manage.py shell << 'EOF'
from django.test import Client
from core.models import TemporaryClimber
from django.utils import timezone
from datetime import timedelta

# Create expired climber
TemporaryClimber.objects.filter(email='login_test@example.com').delete()

expired_climber = TemporaryClimber.objects.create(
    name='Login Test User',
    email='login_test@example.com',
    phone='11777777777',
    email_verified=True,
    access_until=timezone.now() - timedelta(hours=1)  # Expired 1 hour ago
)

# Try to login
client = Client(HTTP_HOST='climacocal.com.br')
response = client.post('/escaladores/login/', {
    'email': 'login_test@example.com'
})

print(f"Login response status: {response.status_code}")

if response.status_code == 200:
    content = response.content.decode()
    if 'expirou' in content.lower():
        print("  ✅ SUCCESS: Login correctly rejected expired user")
    else:
        print("  ❌ FAILED: Login should have rejected expired user")
elif response.status_code == 302:
    print("  ❌ FAILED: Login should not redirect expired user")

# Clean up
expired_climber.delete()
EOF

echo ""
echo "Test 4: Complete Renewal and Streaming Flow"
echo "------------------------------------------"

docker-compose exec -T climacocal python manage.py shell << 'EOF'
from django.test import Client
from django.core.cache import cache
from core.models import TemporaryClimber
from django.utils import timezone
from datetime import timedelta
import json

# Create expired climber
cache.clear()
TemporaryClimber.objects.filter(email='flow_test@example.com').delete()

expired_climber = TemporaryClimber.objects.create(
    name='Flow Test User',
    email='flow_test@example.com',
    phone='11666666666',
    email_verified=True,
    access_until=timezone.now() - timedelta(hours=1)
)

client = Client(HTTP_HOST='climacocal.com.br')

# Step 1: Register again (renew)
print("Step 1: Renewing expired climber...")
response = client.post('/escaladores/cadastro/', {
    'name': 'Flow Test Renewed',
    'email': 'flow_test@example.com',
    'phone': '11555555555'
})

renewed_climber = TemporaryClimber.objects.get(email='flow_test@example.com')
print(f"  Climber renewed: {renewed_climber.has_access}")

if renewed_climber.has_access:
    # Step 2: Login with renewed access
    print("\nStep 2: Login with renewed access...")
    login_response = client.post('/escaladores/login/', {
        'email': 'flow_test@example.com'
    })
    print(f"  Login status: {login_response.status_code}")
    
    if login_response.status_code == 302:
        # Step 3: Access streaming page
        print("\nStep 3: Access streaming page...")
        access_response = client.get(login_response.url)
        print(f"  Access page status: {access_response.status_code}")
        
        # Step 4: Check streaming API
        print("\nStep 4: Check streaming API...")
        api_response = client.get('/streaming/api/status/')
        print(f"  API status: {api_response.status_code}")
        
        if api_response.status_code == 200:
            data = json.loads(api_response.content)
            print(f"  Has access: {data.get('has_access')}")
            print(f"  User type: {data.get('user_type')}")
            print(f"  Climber name: {data.get('climber_name')}")
            
            if data.get('has_access') and data.get('user_type') == 'climber':
                print("  ✅ SUCCESS: Complete renewal and streaming flow works!")
            else:
                print("  ❌ FAILED: Streaming API not recognizing renewed climber")
        else:
            print("  ❌ FAILED: Streaming API error")
    else:
        print("  ❌ FAILED: Login should redirect to access page")
else:
    print("  ❌ FAILED: Climber was not renewed")

# Clean up
renewed_climber.delete()
cache.clear()
EOF

echo ""
echo "Test 5: Admin Renewal Functions"
echo "------------------------------"

docker-compose exec -T climacocal python manage.py shell << 'EOF'
from core.services.climber_service import ClimberService
from core.models import TemporaryClimber
from django.utils import timezone
from datetime import timedelta

# Test service renewal function
TemporaryClimber.objects.filter(email='service_test@example.com').delete()

expired_climber = TemporaryClimber.objects.create(
    name='Service Test User',
    email='service_test@example.com',
    phone='11444444444',
    email_verified=True,
    access_until=timezone.now() - timedelta(hours=3)
)

print("Testing ClimberService.renew_climber_access()...")
print(f"  Before: {expired_climber.has_access}")

# Renew access using service
success = ClimberService.renew_climber_access('service_test@example.com', 30)
print(f"  Renewal success: {success}")

# Check result
renewed_climber = TemporaryClimber.objects.get(email='service_test@example.com')
print(f"  After: {renewed_climber.has_access}")

if renewed_climber.has_access:
    print("  ✅ SUCCESS: Service renewal works!")
else:
    print("  ❌ FAILED: Service renewal failed")

# Test get expired climbers
print("\nTesting ClimberService.get_expired_climbers()...")
expired_list = ClimberService.get_expired_climbers()
print(f"  Found {expired_list.count()} expired climbers")

# Clean up
renewed_climber.delete()
EOF

echo ""
echo "=========================================="
echo "Test Summary Complete"
echo "=========================================="
echo ""
echo "If all tests show ✅ SUCCESS, the renewal system is working!"
echo "Users can now re-register with expired emails to renew access."
echo ""
echo "Admin functions available:"
echo "- GET  /escaladores/admin/expired/ - List expired climbers"
echo "- POST /escaladores/admin/renew/   - Renew specific climber"
echo "=========================================="