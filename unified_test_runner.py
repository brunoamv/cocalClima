#!/usr/bin/env python3
"""
ClimaCocal v2.2.0 - Unified Test Runner
Executes comprehensive test validation for the system
"""
import sys
import os
sys.path.append('/app')

import django
from django.conf import settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from streaming.services import CameraStreamingService, PaymentValidationService
from django.core.cache import cache
from django.test import Client
import json

def run_unified_tests():
    """Run comprehensive system tests"""
    
    print('🧪 ClimaCocal v2.2.0 - Sistema de Testes Unificado')
    print('=' * 60)
    
    tests_passed = 0
    tests_total = 0
    
    # Test 1: Service Initialization
    tests_total += 1
    try:
        camera_service = CameraStreamingService()
        payment_service = PaymentValidationService()
        assert camera_service is not None
        assert payment_service is not None
        print('✅ 1. Service Initialization: PASS')
        tests_passed += 1
    except Exception as e:
        print(f'❌ 1. Service Initialization: FAIL - {e}')
    
    # Test 2: Payment Validation
    tests_total += 1
    try:
        cache.clear()
        payment_service.set_payment_status('test_user', 'approved')
        status = payment_service.check_payment_status('test_user')
        access = payment_service.is_access_granted('test_user')
        assert status == 'approved'
        assert access == True
        print('✅ 2. Payment Validation: PASS')
        tests_passed += 1
    except Exception as e:
        print(f'❌ 2. Payment Validation: FAIL - {e}')
    
    # Test 3: Camera Status Check
    tests_total += 1
    try:
        camera_online = camera_service.test_camera_connection()
        print(f'✅ 3. Camera Status Check: PASS (Camera: {"Online" if camera_online else "Offline"})')
        tests_passed += 1
    except Exception as e:
        print(f'❌ 3. Camera Status Check: FAIL - {e}')
    
    # Test 4: Streaming Status
    tests_total += 1
    try:
        status = camera_service.get_status()
        assert 'is_streaming' in status
        assert 'camera_available' in status
        print('✅ 4. Streaming Status: PASS')
        tests_passed += 1
    except Exception as e:
        print(f'❌ 4. Streaming Status: FAIL - {e}')
    
    # Test 5: API Response Structure
    tests_total += 1
    try:
        client = Client()
        cache.set('payment_status_test', 'approved', timeout=600)
        response = client.get('/streaming/api/status/')
        assert response.status_code == 200
        data = json.loads(response.content)
        assert 'has_access' in data
        assert 'streaming_active' in data
        assert 'camera_available' in data
        print('✅ 5. API Response Structure: PASS')
        tests_passed += 1
    except Exception as e:
        print(f'❌ 5. API Response Structure: FAIL - {e}')
    
    # Test 6: Stream File Access
    tests_total += 1
    try:
        import os
        stream_file = '/app/camera_stream/stream.m3u8'
        if os.path.exists(stream_file):
            print('✅ 6. Stream File Access: PASS (HLS playlist exists)')
            tests_passed += 1
        else:
            print('⚠️  6. Stream File Access: WARNING (No HLS playlist)')
    except Exception as e:
        print(f'❌ 6. Stream File Access: FAIL - {e}')
    
    # Test 7: URLs Accessibility
    tests_total += 1
    try:
        client = Client()
        cache.set('payment_status_direct', 'approved', timeout=600)
        
        # Test main URLs
        response1 = client.get('/test-payment-direct/')
        response2 = client.get('/escaladores/acesso/')
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        print('✅ 7. URLs Accessibility: PASS')
        tests_passed += 1
    except Exception as e:
        print(f'❌ 7. URLs Accessibility: FAIL - {e}')
    
    # Test Summary
    print('\n📊 Resumo dos Testes:')
    print(f'   ✅ Testes Passaram: {tests_passed}/{tests_total}')
    print(f'   🎯 Taxa de Sucesso: {(tests_passed/tests_total)*100:.1f}%')
    
    if tests_passed == tests_total:
        print('\n🎉 TODOS OS TESTES PASSARAM!')
        return True
    else:
        print(f'\n⚠️  {tests_total - tests_passed} testes falharam')
        return False

if __name__ == '__main__':
    run_unified_tests()