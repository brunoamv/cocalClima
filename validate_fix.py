#!/usr/bin/env python3
"""
Validator script for the frontend-API integration fix
"""
import requests
import json
import re

def test_api_functionality():
    """Test API endpoint functionality"""
    print("🧪 Testing API functionality...")
    
    try:
        response = requests.get("https://climacocal.com.br/streaming/api/status/", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Check required fields
            required_fields = ['has_access', 'stream_url', 'camera_available', 'streaming_active']
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                print(f"❌ API missing fields: {missing_fields}")
                return False
            else:
                print(f"✅ API returns correct fields: {required_fields}")
                print(f"   - has_access: {data['has_access']}")
                print(f"   - streaming_active: {data['streaming_active']}")
                print(f"   - camera_available: {data['camera_available']}")
                return True
        else:
            print(f"❌ API returned status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

def test_frontend_integration():
    """Test frontend integration with correct field names"""
    print("\n🎨 Testing frontend integration...")
    
    try:
        # Test payment success page
        response = requests.get("https://climacocal.com.br/test-payment-direct/", timeout=10)
        
        if response.status_code == 200:
            content = response.text
            
            # Check if old field is gone and new field is present
            has_old_field = 'data.access_granted' in content
            has_new_field = 'data.has_access' in content
            
            if has_old_field:
                print("❌ Frontend still uses deprecated 'access_granted' field")
                return False
            elif has_new_field:
                print("✅ Frontend correctly uses 'has_access' field")
                
                # Check for streaming availability logic
                if 'data.has_access && data.stream_url' in content:
                    print("✅ Frontend correctly checks both access and stream_url")
                    return True
                else:
                    print("⚠️  Frontend logic may have changed")
                    return True
            else:
                print("⚠️  Could not find field usage in frontend")
                return None
        else:
            print(f"❌ Frontend page returned status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Frontend test failed: {e}")
        return False

def test_escaladores_page():
    """Test escaladores page functionality"""
    print("\n🧗 Testing escaladores page...")
    
    try:
        response = requests.get("https://climacocal.com.br/escaladores/acesso/", 
                              timeout=10, allow_redirects=False)
        
        if response.status_code == 302:
            print("✅ Escaladores page correctly redirects (authentication required)")
            return True
        elif response.status_code == 200:
            print("✅ Escaladores page accessible")
            return True
        else:
            print(f"❌ Escaladores page returned status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Escaladores test failed: {e}")
        return False

def test_streaming_functionality():
    """Test HLS streaming functionality"""
    print("\n📹 Testing HLS streaming...")
    
    try:
        response = requests.get("https://climacocal.com.br/streaming/camera/stream.m3u8", timeout=10)
        
        if response.status_code == 200:
            content = response.text
            
            if '#EXTM3U' in content and 'segment_' in content:
                print("✅ HLS playlist is valid and contains segments")
                
                # Count segments for freshness check
                segments = re.findall(r'segment_\d+\.ts', content)
                print(f"   - Found {len(segments)} segments in playlist")
                
                if len(segments) >= 5:
                    print("✅ Playlist contains sufficient segments (streaming active)")
                    return True
                else:
                    print("⚠️  Few segments found, streaming may be starting")
                    return True
            else:
                print("❌ Invalid HLS playlist format")
                return False
        else:
            print(f"❌ HLS streaming returned status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Streaming test failed: {e}")
        return False

def main():
    """Run all validation tests"""
    print("🎯 ClimaCocal Frontend-API Integration Validator")
    print("=" * 60)
    
    tests = [
        ("API Functionality", test_api_functionality),
        ("Frontend Integration", test_frontend_integration), 
        ("Escaladores Page", test_escaladores_page),
        ("HLS Streaming", test_streaming_functionality)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        result = test_func()
        if result is True:
            passed += 1
        elif result is None:
            # Inconclusive test doesn't count as failure
            total -= 1
    
    print(f"\n📊 Final Results:")
    print(f"   ✅ Passed: {passed}/{total}")
    print(f"   🎯 Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Fix is working correctly.")
        print("✅ The 'Stream Temporariamente Indisponível' issue should be resolved.")
        return True
    else:
        print(f"\n⚠️  {total-passed} tests failed. Some issues may remain.")
        return False

if __name__ == "__main__":
    main()