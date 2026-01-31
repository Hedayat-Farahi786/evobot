#!/usr/bin/env python3
"""
Authentication Test Script
Tests login, signup, and authentication flow
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8080"

def test_signup():
    """Test user signup"""
    print("\n=== Testing Signup ===")
    
    data = {
        "email": "test@example.com",
        "password": "Test@123!",
        "display_name": "Test User"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/signup", json=data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✓ Signup successful")
            return True
        elif response.status_code == 400 and "already exists" in response.text:
            print("⚠ User already exists (expected if running multiple times)")
            return True
        else:
            print("✗ Signup failed")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_login(email="admin@evobot.local", password="Admin@123!"):
    """Test user login"""
    print(f"\n=== Testing Login ({email}) ===")
    
    data = {
        "email": email,
        "password": password
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/login", json=data)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✓ Login successful")
            print(f"  Token: {result['access_token'][:50]}...")
            print(f"  User: {result['user']['email']}")
            print(f"  Role: {result['user']['role']}")
            return result['access_token']
        else:
            print(f"✗ Login failed: {response.text}")
            return None
    except Exception as e:
        print(f"✗ Error: {e}")
        return None

def test_protected_endpoint(token):
    """Test accessing protected endpoint"""
    print("\n=== Testing Protected Endpoint ===")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✓ Protected endpoint accessible")
            print(f"  User: {result['email']}")
            print(f"  Role: {result['role']}")
            return True
        else:
            print(f"✗ Failed to access protected endpoint: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_invalid_login():
    """Test login with invalid credentials"""
    print("\n=== Testing Invalid Login ===")
    
    data = {
        "email": "admin@evobot.local",
        "password": "WrongPassword123!"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/login", json=data)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 401:
            print("✓ Invalid login correctly rejected")
            return True
        else:
            print(f"✗ Unexpected response: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_weak_password():
    """Test signup with weak password"""
    print("\n=== Testing Weak Password ===")
    
    data = {
        "email": "weak@example.com",
        "password": "weak",
        "display_name": "Weak User"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/signup", json=data)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 400:
            print("✓ Weak password correctly rejected")
            print(f"  Message: {response.text}")
            return True
        else:
            print(f"✗ Weak password was accepted (should be rejected)")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def main():
    print("=" * 60)
    print("EvoBot Authentication Test Suite")
    print("=" * 60)
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/login", timeout=2)
        if response.status_code != 200:
            print("✗ Server not responding correctly")
            sys.exit(1)
    except Exception as e:
        print(f"✗ Cannot connect to server at {BASE_URL}")
        print(f"  Error: {e}")
        print("\nPlease start the dashboard server:")
        print("  python dashboard/app.py")
        sys.exit(1)
    
    print("✓ Server is running")
    
    # Run tests
    results = []
    
    # Test 1: Weak password rejection
    results.append(("Weak Password Rejection", test_weak_password()))
    
    # Test 2: Signup
    results.append(("User Signup", test_signup()))
    
    # Test 3: Admin login
    token = test_login()
    results.append(("Admin Login", token is not None))
    
    # Test 4: Protected endpoint
    if token:
        results.append(("Protected Endpoint", test_protected_endpoint(token)))
    
    # Test 5: Invalid login
    results.append(("Invalid Login Rejection", test_invalid_login()))
    
    # Test 6: Test user login
    test_token = test_login("test@example.com", "Test@123!")
    results.append(("Test User Login", test_token is not None))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print(f"\n⚠ {total - passed} test(s) failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
