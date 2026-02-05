"""
Integration tests for authentication system
Tests login, registration, token verification, and password change
"""
import sys
import os
import requests
import time
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

API_BASE_URL = "http://localhost:8000/api"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_test(name, passed, message=""):
    status = f"{Colors.GREEN}✓ PASS{Colors.END}" if passed else f"{Colors.RED}✗ FAIL{Colors.END}"
    print(f"{status} - {name}")
    if message:
        print(f"      {message}")

def test_health_check():
    """Test 1: Health Check"""
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        passed = response.status_code == 200
        print_test("Health Check", passed, f"Status: {response.status_code}")
        return passed
    except Exception as e:
        print_test("Health Check", False, f"Error: {str(e)}")
        return False

def test_user_registration():
    """Test 2: User Registration"""
    try:
        test_email = f"test_auth_{int(time.time())}@example.com"
        payload = {
            "email": test_email,
            "password": "testpassword123",
            "name": "Test User"
        }
        response = requests.post(f"{API_BASE_URL}/auth/register", json=payload)
        data = response.json()
        
        passed = (
            response.status_code == 200 and
            "access_token" in data and
            "user" in data
        )
        
        print_test("User Registration", passed, f"Email: {test_email}")
        return passed, data.get("access_token"), test_email, payload["password"]
    except Exception as e:
        print_test("User Registration", False, f"Error: {str(e)}")
        return False, None, None, None

def test_duplicate_registration(email):
    """Test 3: Duplicate Registration Prevention"""
    try:
        payload = {
            "email": email,
            "password": "differentpassword",
            "name": "Duplicate User"
        }
        response = requests.post(f"{API_BASE_URL}/auth/register", json=payload)
        
        # Should fail with 400
        passed = response.status_code == 400
        print_test("Duplicate Registration Prevention", passed, 
                  f"Expected 400, got {response.status_code}")
        return passed
    except Exception as e:
        print_test("Duplicate Registration Prevention", False, f"Error: {str(e)}")
        return False

def test_user_login(email, password):
    """Test 4: User Login"""
    try:
        payload = {
            "email": email,
            "password": password
        }
        response = requests.post(f"{API_BASE_URL}/auth/login", json=payload)
        data = response.json()
        
        passed = (
            response.status_code == 200 and
            "access_token" in data and
            "user" in data
        )
        
        print_test("User Login", passed, f"Token received: {bool(data.get('access_token'))}")
        return passed, data.get("access_token")
    except Exception as e:
        print_test("User Login", False, f"Error: {str(e)}")
        return False, None

def test_invalid_login():
    """Test 5: Invalid Login Credentials"""
    try:
        payload = {
            "email": "nonexistent@example.com",
            "password": "wrongpassword"
        }
        response = requests.post(f"{API_BASE_URL}/auth/login", json=payload)
        
        # Should fail with 401
        passed = response.status_code == 401
        print_test("Invalid Login Credentials", passed, 
                  f"Expected 401, got {response.status_code}")
        return passed
    except Exception as e:
        print_test("Invalid Login Credentials", False, f"Error: {str(e)}")
        return False

def test_token_verification(token):
    """Test 6: Token Verification"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{API_BASE_URL}/auth/verify", headers=headers)
        data = response.json()
        
        passed = (
            response.status_code == 200 and
            "user" in data
        )
        
        print_test("Token Verification", passed, f"User data: {data.get('user', {}).get('email')}")
        return passed
    except Exception as e:
        print_test("Token Verification", False, f"Error: {str(e)}")
        return False

def test_invalid_token():
    """Test 7: Invalid Token Rejection"""
    try:
        headers = {"Authorization": "Bearer invalid_token_here"}
        response = requests.get(f"{API_BASE_URL}/auth/verify", headers=headers)
        
        # Should fail with 401
        passed = response.status_code == 401
        print_test("Invalid Token Rejection", passed, 
                  f"Expected 401, got {response.status_code}")
        return passed
    except Exception as e:
        print_test("Invalid Token Rejection", False, f"Error: {str(e)}")
        return False

def test_protected_endpoint(token):
    """Test 8: Protected Endpoint Access"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{API_BASE_URL}/strategies/", headers=headers)
        
        passed = response.status_code in [200, 404]  # 200 with data, 404 if no strategies
        print_test("Protected Endpoint Access", passed, 
                  f"Status: {response.status_code}")
        return passed
    except Exception as e:
        print_test("Protected Endpoint Access", False, f"Error: {str(e)}")
        return False

def test_protected_endpoint_without_token():
    """Test 9: Protected Endpoint Without Token"""
    try:
        response = requests.get(f"{API_BASE_URL}/strategies/")
        
        # Should fail with 401 or 403
        passed = response.status_code in [401, 403]
        print_test("Protected Endpoint Without Token", passed, 
                  f"Expected 401/403, got {response.status_code}")
        return passed
    except Exception as e:
        print_test("Protected Endpoint Without Token", False, f"Error: {str(e)}")
        return False

def test_change_password(token, old_password):
    """Test 10: Password Change"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        payload = {
            "current_password": old_password,
            "new_password": "newpassword123"
        }
        response = requests.post(f"{API_BASE_URL}/auth/change-password", 
                               json=payload, headers=headers)
        
        passed = response.status_code == 200
        print_test("Password Change", passed, f"Status: {response.status_code}")
        return passed
    except Exception as e:
        print_test("Password Change", False, f"Error: {str(e)}")
        return False

def test_login_with_new_password(email):
    """Test 11: Login With New Password"""
    try:
        payload = {
            "email": email,
            "password": "newpassword123"
        }
        response = requests.post(f"{API_BASE_URL}/auth/login", json=payload)
        
        passed = response.status_code == 200
        print_test("Login With New Password", passed, 
                  f"Login successful with new password")
        return passed
    except Exception as e:
        print_test("Login With New Password", False, f"Error: {str(e)}")
        return False

def test_logout(token):
    """Test 12: User Logout"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(f"{API_BASE_URL}/auth/logout", headers=headers)
        
        passed = response.status_code == 200
        print_test("User Logout", passed, f"Status: {response.status_code}")
        return passed
    except Exception as e:
        print_test("User Logout", False, f"Error: {str(e)}")
        return False

def main():
    print(f"\n{Colors.BLUE}{'='*60}")
    print("AURELIUS Authentication Integration Tests")
    print(f"{'='*60}{Colors.END}\n")
    print(f"API URL: {API_BASE_URL}")
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    results = []
    
    # Run all tests
    results.append(test_health_check())
    
    reg_passed, token, email, password = test_user_registration()
    results.append(reg_passed)
    
    if not reg_passed:
        print(f"\n{Colors.RED}Registration failed - stopping tests{Colors.END}\n")
        return
    
    results.append(test_duplicate_registration(email))
    
    login_passed, login_token = test_user_login(email, password)
    results.append(login_passed)
    
    results.append(test_invalid_login())
    
    if login_token:
        results.append(test_token_verification(login_token))
    
    results.append(test_invalid_token())
    
    if login_token:
        results.append(test_protected_endpoint(login_token))
    
    results.append(test_protected_endpoint_without_token())
    
    if login_token:
        results.append(test_change_password(login_token, password))
        results.append(test_login_with_new_password(email))
        
        # Get new token after password change
        _, new_token = test_user_login(email, "newpassword123")
        if new_token:
            results.append(test_logout(new_token))
    
    # Summary
    print(f"\n{Colors.BLUE}{'='*60}")
    print("Test Summary")
    print(f"{'='*60}{Colors.END}\n")
    
    total = len(results)
    passed = sum(results)
    failed = total - passed
    
    print(f"Total Tests: {total}")
    print(f"{Colors.GREEN}Passed: {passed}{Colors.END}")
    if failed > 0:
        print(f"{Colors.RED}Failed: {failed}{Colors.END}")
    
    percentage = (passed / total * 100) if total > 0 else 0
    print(f"\nSuccess Rate: {percentage:.1f}%")
    
    if passed == total:
        print(f"\n{Colors.GREEN}✓ All authentication tests passed!{Colors.END}\n")
    else:
        print(f"\n{Colors.YELLOW}⚠ Some tests failed{Colors.END}\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Tests interrupted by user{Colors.END}\n")
    except Exception as e:
        print(f"\n{Colors.RED}Error running tests: {str(e)}{Colors.END}\n")
