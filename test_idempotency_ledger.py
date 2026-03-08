"""
Phase 1: Idempotency & Ledger Testing
Core Banking System - Transfer API Validation

Test Suite: Validates idempotency enforcement on transfer operations
Author: Senior QA Automation Engineer
Target: POST /api/v1/core/transfer
"""

import pytest
import requests
import uuid
from datetime import datetime


# Configuration
BASE_URL = "http://localhost:8080"
TRANSFER_ENDPOINT = f"{BASE_URL}/api/v1/transactions/transfer"


@pytest.fixture
def auth_token():
    """
    Fixture: Authenticate and return JWT token for API requests
    """
    # First register a test user
    register_url = f"{BASE_URL}/api/v1/auth/register"
    username = f"test_user_{uuid.uuid4().hex[:8]}"
    
    register_payload = {
        "username": username,
        "password": "Test123!@#",
        "email": f"{username}@test.com",
        "firstName": "Test",
        "lastName": "User",
        "pin": "1234"
    }
    
    requests.post(register_url, json=register_payload)
    
    # Now login
    auth_url = f"{BASE_URL}/api/v1/auth/login"
    login_payload = {
        "username": username,
        "password": "Test123!@#"
    }
    
    response = requests.post(auth_url, json=login_payload)
    if response.status_code == 200:
        return response.json().get("token")
    
    return None


@pytest.fixture
def transfer_payload(auth_token):
    """
    Fixture: Generate valid transfer request payload with user's own accounts
    """
    # Create two accounts for the user
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    }
    
    # Create USD account
    usd_payload = {
        "accountType": "SAVINGS",
        "currency": "USD",
        "initialDeposit": 10000.00
    }
    usd_resp = requests.post(f"{BASE_URL}/api/v1/accounts", json=usd_payload, headers=headers)
    from_account = usd_resp.json().get("accountNumber")
    
    # Create KHR account
    khr_payload = {
        "accountType": "CHECKING",
        "currency": "KHR",
        "initialDeposit": 500000.00
    }
    khr_resp = requests.post(f"{BASE_URL}/api/v1/accounts", json=khr_payload, headers=headers)
    to_account = khr_resp.json().get("accountNumber")
    
    return {
        "fromAccountNumber": from_account,
        "toAccountNumber": to_account,
        "amount": 100.00,
        "transactionType": "TRANSFER",
        "pin": "1234",
        "note": "Idempotency test transfer"
    }


def test_case_a_valid_transfer_with_unique_idempotency_key(auth_token, transfer_payload):
    """
    Test Case A: Valid Transfer with Unique Idempotency Key
    
    Scenario:
        - Send a valid transfer request with a dynamically generated UUID
        - Expect: 200 OK response indicating successful transfer
    
    Validates:
        - Transfer endpoint accepts valid requests
        - Idempotency key is properly processed
        - Transfer is executed successfully
    """
    # Generate unique idempotency key
    idempotency_key = str(uuid.uuid4())
    
    # Prepare headers
    headers = {
        "Content-Type": "application/json",
        "Idempotency-Key": idempotency_key
    }
    
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    
    # Execute transfer request
    response = requests.post(
        TRANSFER_ENDPOINT,
        json=transfer_payload,
        headers=headers,
        timeout=10
    )
    
    # Assertions
    assert response.status_code == 200, (
        f"Expected 200 OK, got {response.status_code}. "
        f"Response: {response.text}"
    )
    
    # Validate response structure
    response_data = response.json()
    assert "transactionId" in response_data or "id" in response_data, (
        "Response should contain transaction identifier"
    )
    
    print(f"✅ Test Case A PASSED: Transfer successful with idempotency key {idempotency_key}")


def test_case_b_duplicate_request_with_same_idempotency_key(auth_token, transfer_payload):
    """
    Test Case B: Duplicate Request with Same Idempotency Key
    
    Scenario:
        - Send initial transfer request with idempotency key
        - Immediately send EXACT same request with SAME idempotency key
        - Expect: 409 Conflict response indicating duplicate detection
    
    Validates:
        - Idempotency enforcement is working correctly
        - System prevents duplicate transactions
        - Proper HTTP status code returned for conflicts
    """
    # Generate idempotency key (will be reused)
    idempotency_key = str(uuid.uuid4())
    
    # Prepare headers
    headers = {
        "Content-Type": "application/json",
        "Idempotency-Key": idempotency_key
    }
    
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    
    # First request - should succeed
    response_1 = requests.post(
        TRANSFER_ENDPOINT,
        json=transfer_payload,
        headers=headers,
        timeout=10
    )
    
    assert response_1.status_code == 200, (
        f"First request should succeed. Got {response_1.status_code}"
    )
    
    print(f"✅ First request successful with key {idempotency_key}")
    
    # Second request - SAME idempotency key (should be rejected)
    response_2 = requests.post(
        TRANSFER_ENDPOINT,
        json=transfer_payload,
        headers=headers,
        timeout=10
    )
    
    # Assertions
    assert response_2.status_code == 409, (
        f"Expected 409 Conflict for duplicate request, got {response_2.status_code}. "
        f"Response: {response_2.text}"
    )
    
    # Validate error message
    response_data = response_2.json()
    assert "error" in response_data or "message" in response_data, (
        "Response should contain error message"
    )
    
    print(f"✅ Test Case B PASSED: Duplicate request correctly rejected with 409 Conflict")


def test_case_c_different_idempotency_keys_allow_multiple_transfers(auth_token, transfer_payload):
    """
    Test Case C: Different Idempotency Keys Allow Multiple Transfers (Bonus)
    
    Scenario:
        - Send multiple transfer requests with DIFFERENT idempotency keys
        - Expect: All requests succeed with 200 OK
    
    Validates:
        - System allows legitimate multiple transfers
        - Idempotency only blocks exact duplicates
    """
    results = []
    
    for i in range(3):
        # Generate unique idempotency key for each request
        idempotency_key = str(uuid.uuid4())
        
        headers = {
            "Content-Type": "application/json",
            "Idempotency-Key": idempotency_key
        }
        
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        
        # Modify amount slightly to ensure different transactions
        payload = transfer_payload.copy()
        payload["amount"] = 100.00 + i
        
        response = requests.post(
            TRANSFER_ENDPOINT,
            json=payload,
            headers=headers,
            timeout=10
        )
        
        results.append(response.status_code)
        print(f"  Request {i+1}: {response.status_code} (Key: {idempotency_key[:8]}...)")
    
    # All requests should succeed
    assert all(status == 200 for status in results), (
        f"All requests with unique keys should succeed. Got: {results}"
    )
    
    print(f"✅ Test Case C PASSED: Multiple transfers with different keys all succeeded")


if __name__ == "__main__":
    """
    Run tests directly without pytest runner
    """
    print("\n" + "="*70)
    print("🧪 PHASE 1: IDEMPOTENCY & LEDGER TESTING")
    print("="*70 + "\n")
    
    # Get auth token
    print("Authenticating...")
    register_url = f"{BASE_URL}/api/v1/auth/register"
    username = f"test_user_{uuid.uuid4().hex[:8]}"
    
    register_payload = {
        "username": username,
        "password": "Test123!@#",
        "email": f"{username}@test.com",
        "firstName": "Test",
        "lastName": "User",
        "pin": "1234"
    }
    
    requests.post(register_url, json=register_payload)
    
    auth_url = f"{BASE_URL}/api/v1/auth/login"
    login_payload = {
        "username": username,
        "password": "Test123!@#"
    }
    
    response = requests.post(auth_url, json=login_payload)
    token = response.json().get("token") if response.status_code == 200 else None
    
    if token:
        print(f"✅ Authenticated as {username}\n")
        
        # Create accounts
        print("Creating test accounts...")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        
        usd_payload = {
            "accountType": "SAVINGS",
            "currency": "USD",
            "initialDeposit": 10000.00
        }
        usd_resp = requests.post(f"{BASE_URL}/api/v1/accounts", json=usd_payload, headers=headers)
        from_account = usd_resp.json().get("accountNumber")
        
        khr_payload = {
            "accountType": "CHECKING",
            "currency": "KHR",
            "initialDeposit": 500000.00
        }
        khr_resp = requests.post(f"{BASE_URL}/api/v1/accounts", json=khr_payload, headers=headers)
        to_account = khr_resp.json().get("accountNumber")
        
        print(f"✅ Created accounts: {from_account} → {to_account}\n")
    else:
        print("⚠️  Running without authentication\n")
        from_account = "001202640700"
        to_account = "001202624829"
    
    payload = {
        "fromAccountNumber": from_account,
        "toAccountNumber": to_account,
        "amount": 100.00,
        "transactionType": "TRANSFER",
        "pin": "1234",
        "note": "Idempotency test transfer"
    }
    
    try:
        print("Running Test Case A...")
        test_case_a_valid_transfer_with_unique_idempotency_key(token, payload)
        print()
        
        print("Running Test Case B...")
        test_case_b_duplicate_request_with_same_idempotency_key(token, payload)
        print()
        
        print("Running Test Case C...")
        test_case_c_different_idempotency_keys_allow_multiple_transfers(token, payload)
        print()
        
        print("="*70)
        print("✅ ALL TESTS PASSED")
        print("="*70)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
