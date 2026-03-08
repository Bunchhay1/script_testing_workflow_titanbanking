"""
Phase 2: IAM & API Gateway Routing Testing
Core Banking System - Authentication & Authorization Validation

Test Suite: Validates JWT authentication and API Gateway routing
Author: Senior QA Automation Engineer
Target: IAM Service + API Gateway Protected Endpoints
"""

import pytest
import requests
import uuid


# Configuration
IAM_BASE_URL = "http://localhost:8080"
GATEWAY_BASE_URL = "http://localhost:8000"
IAM_LOGIN_ENDPOINT = f"{IAM_BASE_URL}/api/v1/auth/login"
PROTECTED_ENDPOINT = f"{GATEWAY_BASE_URL}/api/v1/accounts"  # Protected endpoint via gateway


@pytest.fixture(scope="module")
def test_user_credentials():
    """
    Fixture: Create test user and return credentials
    """
    username = f"iam_test_{uuid.uuid4().hex[:8]}"
    password = "SecurePass123!@#"
    
    # Register test user
    register_url = f"{IAM_BASE_URL}/api/v1/auth/register"
    register_payload = {
        "username": username,
        "password": password,
        "email": f"{username}@test.com",
        "firstName": "IAM",
        "lastName": "Test",
        "pin": "1234"
    }
    
    response = requests.post(register_url, json=register_payload)
    
    if response.status_code not in [200, 201]:
        pytest.skip(f"User registration failed: {response.text}")
    
    return {
        "username": username,
        "password": password
    }


def test_target_1_iam_login_and_extract_token(test_user_credentials):
    """
    Target 1: IAM Service Login & Token Extraction
    
    Scenario:
        - POST to IAM Service /api/v1/auth/login with valid credentials
        - Expect: 200 OK response
        - Extract: accessToken from response
    
    Validates:
        - IAM service is operational
        - Login endpoint accepts valid credentials
        - JWT token is generated and returned
    """
    # Prepare login payload
    login_payload = {
        "username": test_user_credentials["username"],
        "password": test_user_credentials["password"]
    }
    
    # Execute login request
    response = requests.post(
        IAM_LOGIN_ENDPOINT,
        json=login_payload,
        timeout=10
    )
    
    # Assert status code
    assert response.status_code == 200, (
        f"Expected 200 OK from IAM login, got {response.status_code}. "
        f"Response: {response.text}"
    )
    
    # Parse response
    response_data = response.json()
    
    # Assert token exists
    assert "token" in response_data or "accessToken" in response_data, (
        f"Response should contain 'token' or 'accessToken'. "
        f"Got: {list(response_data.keys())}"
    )
    
    # Extract token
    access_token = response_data.get("token") or response_data.get("accessToken")
    
    assert access_token is not None, "Access token should not be None"
    assert len(access_token) > 0, "Access token should not be empty"
    
    print(f"✅ Target 1 PASSED: Login successful")
    print(f"   Username: {test_user_credentials['username']}")
    print(f"   Token: {access_token[:20]}...")
    
    # Store token for subsequent tests
    pytest.access_token = access_token


def test_target_2_gateway_with_valid_token(test_user_credentials):
    """
    Target 2: API Gateway Protected Endpoint with Valid Token
    
    Scenario:
        - Send request to protected endpoint via API Gateway
        - Include valid JWT token in Authorization header
        - Expect: 200 OK response (access granted)
    
    Validates:
        - API Gateway is operational
        - Gateway properly forwards authenticated requests
        - Protected endpoint accepts valid JWT tokens
        - Authorization header is correctly processed
    """
    # Ensure we have a token from Target 1
    if not hasattr(pytest, 'access_token'):
        # Fallback: Login again if token not available
        login_payload = {
            "username": test_user_credentials["username"],
            "password": test_user_credentials["password"]
        }
        login_response = requests.post(IAM_LOGIN_ENDPOINT, json=login_payload)
        pytest.access_token = login_response.json().get("token") or login_response.json().get("accessToken")
    
    # Prepare headers with Bearer token
    headers = {
        "Authorization": f"Bearer {pytest.access_token}",
        "Content-Type": "application/json"
    }
    
    # Execute request to protected endpoint via gateway
    response = requests.get(
        PROTECTED_ENDPOINT,
        headers=headers,
        timeout=10
    )
    
    # Assert status code
    assert response.status_code == 200, (
        f"Expected 200 OK with valid token, got {response.status_code}. "
        f"Response: {response.text}"
    )
    
    print(f"✅ Target 2 PASSED: Gateway accepted valid token")
    print(f"   Endpoint: {PROTECTED_ENDPOINT}")
    print(f"   Status: {response.status_code}")


def test_target_3_gateway_without_token():
    """
    Target 3: API Gateway Protected Endpoint WITHOUT Token
    
    Scenario:
        - Send request to protected endpoint via API Gateway
        - Do NOT include Authorization header
        - Expect: 401 Unauthorized response (access denied)
    
    Validates:
        - API Gateway enforces authentication
        - Requests without tokens are rejected
        - Proper HTTP 401 status code returned
        - Security is properly enforced
    """
    # Execute request WITHOUT Authorization header
    response = requests.get(
        PROTECTED_ENDPOINT,
        timeout=10
    )
    
    # Assert status code is 401 Unauthorized
    assert response.status_code == 401, (
        f"Expected 401 Unauthorized without token, got {response.status_code}. "
        f"Response: {response.text}"
    )
    
    # Validate error response structure
    try:
        response_data = response.json()
        assert "error" in response_data or "message" in response_data, (
            "Response should contain error message"
        )
    except:
        # Some APIs return plain text for 401
        pass
    
    print(f"✅ Target 3 PASSED: Gateway correctly rejected request without token")
    print(f"   Endpoint: {PROTECTED_ENDPOINT}")
    print(f"   Status: {response.status_code}")


def test_bonus_gateway_with_invalid_token():
    """
    Bonus Test: API Gateway with Invalid/Malformed Token
    
    Scenario:
        - Send request with invalid JWT token
        - Expect: 401 Unauthorized response
    
    Validates:
        - Gateway validates token authenticity
        - Malformed tokens are rejected
    """
    # Use invalid token
    headers = {
        "Authorization": "Bearer invalid.token.here",
        "Content-Type": "application/json"
    }
    
    response = requests.get(
        PROTECTED_ENDPOINT,
        headers=headers,
        timeout=10
    )
    
    # Should be 401 Unauthorized
    assert response.status_code == 401, (
        f"Expected 401 for invalid token, got {response.status_code}"
    )
    
    print(f"✅ Bonus Test PASSED: Gateway rejected invalid token")


if __name__ == "__main__":
    """
    Run tests directly without pytest runner
    """
    print("\n" + "="*70)
    print("🔐 PHASE 2: IAM & API GATEWAY ROUTING TESTING")
    print("="*70 + "\n")
    
    # Create test user
    print("Setting up test user...")
    username = f"iam_test_{uuid.uuid4().hex[:8]}"
    password = "SecurePass123!@#"
    
    register_url = f"{IAM_BASE_URL}/api/v1/auth/register"
    register_payload = {
        "username": username,
        "password": password,
        "email": f"{username}@test.com",
        "firstName": "IAM",
        "lastName": "Test",
        "pin": "1234"
    }
    
    reg_response = requests.post(register_url, json=register_payload)
    if reg_response.status_code in [200, 201]:
        print(f"✅ Test user created: {username}\n")
    else:
        print(f"⚠️  Using existing user or registration failed\n")
    
    credentials = {
        "username": username,
        "password": password
    }
    
    try:
        # Target 1: Login and extract token
        print("Running Target 1: IAM Login & Token Extraction...")
        login_payload = {
            "username": credentials["username"],
            "password": credentials["password"]
        }
        
        response = requests.post(IAM_LOGIN_ENDPOINT, json=login_payload, timeout=10)
        assert response.status_code == 200, f"Login failed: {response.status_code}"
        
        token = response.json().get("token") or response.json().get("accessToken")
        assert token, "No token in response"
        
        print(f"✅ Target 1 PASSED: Token extracted: {token[:20]}...\n")
        
        # Target 2: Gateway with valid token
        print("Running Target 2: Gateway with Valid Token...")
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(PROTECTED_ENDPOINT, headers=headers, timeout=10)
        assert response.status_code == 200, f"Gateway rejected valid token: {response.status_code}"
        
        print(f"✅ Target 2 PASSED: Gateway accepted valid token\n")
        
        # Target 3: Gateway without token
        print("Running Target 3: Gateway WITHOUT Token...")
        response = requests.get(PROTECTED_ENDPOINT, timeout=10)
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        
        print(f"✅ Target 3 PASSED: Gateway rejected request without token\n")
        
        # Bonus: Invalid token
        print("Running Bonus Test: Gateway with Invalid Token...")
        headers = {"Authorization": "Bearer invalid.token.here"}
        response = requests.get(PROTECTED_ENDPOINT, headers=headers, timeout=10)
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        
        print(f"✅ Bonus Test PASSED: Gateway rejected invalid token\n")
        
        print("="*70)
        print("✅ ALL TESTS PASSED")
        print("="*70)
        print("\n📊 Summary:")
        print("   ✅ IAM Service: Operational")
        print("   ✅ JWT Token Generation: Working")
        print("   ✅ API Gateway Routing: Working")
        print("   ✅ Authentication Enforcement: Working")
        print("   ✅ Authorization Header: Properly Processed")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
