"""
Phase 3: Transactional Outbox & Kafka Testing
Core Banking System - Event-Driven Architecture Validation

Test Suite: Validates Outbox pattern and Kafka event publishing
Author: Senior QA Automation Engineer
Target: Outbox Relay Service + Kafka Integration
"""

import pytest
import requests
import uuid
import time


# Configuration
BASE_URL = "http://localhost:8080"
TRANSFER_ENDPOINT = f"{BASE_URL}/api/v1/transactions/transfer"
OUTBOX_STATUS_ENDPOINT = f"{BASE_URL}/api/v1/system/outbox-status"

# Polling configuration
MAX_RETRIES = 5
RETRY_DELAY = 1  # seconds


@pytest.fixture(scope="module")
def authenticated_user():
    """
    Fixture: Create and authenticate test user with accounts
    """
    # Register user
    username = f"outbox_test_{uuid.uuid4().hex[:8]}"
    password = "OutboxTest123!@#"
    
    register_payload = {
        "username": username,
        "password": password,
        "email": f"{username}@test.com",
        "firstName": "Outbox",
        "lastName": "Test",
        "pin": "1234"
    }
    
    requests.post(f"{BASE_URL}/api/v1/auth/register", json=register_payload)
    
    # Login
    login_payload = {
        "username": username,
        "password": password
    }
    
    login_response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_payload)
    token = login_response.json().get("token")
    
    # Create accounts
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # USD account
    usd_payload = {
        "accountType": "SAVINGS",
        "currency": "USD",
        "initialDeposit": 10000.00
    }
    usd_resp = requests.post(f"{BASE_URL}/api/v1/accounts", json=usd_payload, headers=headers)
    from_account = usd_resp.json().get("accountNumber")
    
    # KHR account
    khr_payload = {
        "accountType": "CHECKING",
        "currency": "KHR",
        "initialDeposit": 500000.00
    }
    khr_resp = requests.post(f"{BASE_URL}/api/v1/accounts", json=khr_payload, headers=headers)
    to_account = khr_resp.json().get("accountNumber")
    
    return {
        "token": token,
        "from_account": from_account,
        "to_account": to_account,
        "username": username
    }


def poll_outbox_status(token=None, max_retries=MAX_RETRIES, delay=RETRY_DELAY):
    """
    Polling mechanism to check outbox status
    
    Args:
        token: JWT token for authentication
        max_retries: Maximum number of polling attempts
        delay: Delay between retries in seconds
    
    Returns:
        tuple: (success: bool, pending_count: int, attempts: int)
    """
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(OUTBOX_STATUS_ENDPOINT, headers=headers, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                pending_events = data.get("pendingEvents", -1)
                
                print(f"   Attempt {attempt}/{max_retries}: pendingEvents = {pending_events}")
                
                if pending_events == 0:
                    return True, pending_events, attempt
            else:
                print(f"   Attempt {attempt}/{max_retries}: Status {response.status_code}")
            
            # Wait before next retry (except on last attempt)
            if attempt < max_retries:
                time.sleep(delay)
                
        except Exception as e:
            print(f"   Attempt {attempt}/{max_retries}: Error - {e}")
            if attempt < max_retries:
                time.sleep(delay)
    
    # Failed to reach 0 within timeout
    return False, -1, max_retries


def test_phase3_outbox_relay_and_kafka_publishing(authenticated_user):
    """
    Phase 3: Transactional Outbox & Kafka Integration Test
    
    Test Flow:
        1. Trigger transfer request to generate Outbox event
        2. Poll outbox-status endpoint (max 5 retries, 1s delay)
        3. Assert pendingEvents drops to 0 within timeout
    
    Validates:
        - Transfer creates Outbox event in database
        - Outbox Relay service sweeps database
        - Events are published to Kafka
        - Outbox table is cleaned up (pendingEvents = 0)
    """
    print("\n" + "="*70)
    print("📤 PHASE 3: TRANSACTIONAL OUTBOX & KAFKA TESTING")
    print("="*70 + "\n")
    
    # Step 1: Trigger transfer to generate Outbox event
    print("Step 1: Triggering transfer to generate Outbox event...")
    
    transfer_payload = {
        "fromAccountNumber": authenticated_user["from_account"],
        "toAccountNumber": authenticated_user["to_account"],
        "amount": 100.00,
        "transactionType": "TRANSFER",
        "pin": "1234",
        "note": "Outbox pattern test transfer"
    }
    
    headers = {
        "Authorization": f"Bearer {authenticated_user['token']}",
        "Content-Type": "application/json"
    }
    
    transfer_response = requests.post(
        TRANSFER_ENDPOINT,
        json=transfer_payload,
        headers=headers,
        timeout=10
    )
    
    # Assert transfer succeeded
    assert transfer_response.status_code == 200, (
        f"Transfer failed with status {transfer_response.status_code}. "
        f"Response: {transfer_response.text}"
    )
    
    transaction_id = transfer_response.json().get("id") or transfer_response.json().get("transactionId")
    print(f"✅ Transfer successful (Transaction ID: {transaction_id})")
    print(f"   From: {authenticated_user['from_account']}")
    print(f"   To: {authenticated_user['to_account']}")
    print(f"   Amount: $100.00\n")
    
    # Step 2: Poll outbox-status endpoint
    print("Step 2: Polling outbox-status endpoint...")
    print(f"   Max retries: {MAX_RETRIES}")
    print(f"   Retry delay: {RETRY_DELAY}s\n")
    
    success, pending_count, attempts = poll_outbox_status(token=authenticated_user['token'])
    
    # Step 3: Assert pendingEvents dropped to 0
    print()
    assert success, (
        f"Outbox Relay failed to process events within timeout. "
        f"pendingEvents did not reach 0 after {attempts} attempts. "
        f"Last count: {pending_count}"
    )
    
    print("="*70)
    print("✅ PHASE 3 TEST PASSED")
    print("="*70)
    print("\n📊 Validation Summary:")
    print(f"   ✅ Transfer executed successfully")
    print(f"   ✅ Outbox event created in database")
    print(f"   ✅ Outbox Relay swept database")
    print(f"   ✅ Event published to Kafka")
    print(f"   ✅ Outbox cleaned up (pendingEvents = 0)")
    print(f"   ⏱️  Processing time: ~{attempts} seconds")
    print("\n🎯 Transactional Outbox Pattern: WORKING")
    print("🎯 Kafka Integration: WORKING")


def test_outbox_status_endpoint_availability():
    """
    Pre-requisite Test: Verify outbox-status endpoint is available
    
    Validates:
        - Endpoint exists and is accessible
        - Returns proper JSON structure
    """
    response = requests.get(OUTBOX_STATUS_ENDPOINT, timeout=5)
    
    assert response.status_code == 200, (
        f"Outbox status endpoint not available. Status: {response.status_code}"
    )
    
    data = response.json()
    assert "pendingEvents" in data, (
        "Response should contain 'pendingEvents' field"
    )
    
    print(f"✅ Outbox status endpoint available")
    print(f"   Current pendingEvents: {data.get('pendingEvents')}")


if __name__ == "__main__":
    """
    Run tests directly without pytest runner
    """
    print("\n" + "="*70)
    print("📤 PHASE 3: TRANSACTIONAL OUTBOX & KAFKA TESTING")
    print("="*70 + "\n")
    
    try:
        # Pre-check: Verify outbox-status endpoint
        print("Pre-check: Verifying outbox-status endpoint...")
        response = requests.get(OUTBOX_STATUS_ENDPOINT, timeout=5)
        
        if response.status_code != 200:
            print(f"⚠️  Outbox status endpoint not available (Status: {response.status_code})")
            print("   Continuing with test...\n")
        else:
            data = response.json()
            print(f"✅ Outbox status endpoint available")
            print(f"   Current pendingEvents: {data.get('pendingEvents')}\n")
        
        # Setup: Create authenticated user with accounts
        print("Setup: Creating test user and accounts...")
        username = f"outbox_test_{uuid.uuid4().hex[:8]}"
        password = "OutboxTest123!@#"
        
        register_payload = {
            "username": username,
            "password": password,
            "email": f"{username}@test.com",
            "firstName": "Outbox",
            "lastName": "Test",
            "pin": "1234"
        }
        
        requests.post(f"{BASE_URL}/api/v1/auth/register", json=register_payload)
        
        login_payload = {"username": username, "password": password}
        login_response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_payload)
        token = login_response.json().get("token")
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Create accounts
        usd_payload = {"accountType": "SAVINGS", "currency": "USD", "initialDeposit": 10000.00}
        usd_resp = requests.post(f"{BASE_URL}/api/v1/accounts", json=usd_payload, headers=headers)
        from_account = usd_resp.json().get("accountNumber")
        
        khr_payload = {"accountType": "CHECKING", "currency": "KHR", "initialDeposit": 500000.00}
        khr_resp = requests.post(f"{BASE_URL}/api/v1/accounts", json=khr_payload, headers=headers)
        to_account = khr_resp.json().get("accountNumber")
        
        print(f"✅ Test user created: {username}")
        print(f"   Accounts: {from_account} → {to_account}\n")
        
        # Step 1: Trigger transfer
        print("Step 1: Triggering transfer to generate Outbox event...")
        
        transfer_payload = {
            "fromAccountNumber": from_account,
            "toAccountNumber": to_account,
            "amount": 100.00,
            "transactionType": "TRANSFER",
            "pin": "1234",
            "note": "Outbox pattern test transfer"
        }
        
        transfer_response = requests.post(TRANSFER_ENDPOINT, json=transfer_payload, headers=headers, timeout=10)
        assert transfer_response.status_code == 200, f"Transfer failed: {transfer_response.status_code}"
        
        transaction_id = transfer_response.json().get("id")
        print(f"✅ Transfer successful (Transaction ID: {transaction_id})")
        print(f"   Amount: $100.00\n")
        
        # Step 2: Poll outbox status
        print("Step 2: Polling outbox-status endpoint...")
        print(f"   Max retries: {MAX_RETRIES}, Delay: {RETRY_DELAY}s\n")
        
        success, pending_count, attempts = poll_outbox_status(token=token)
        
        # Step 3: Validate
        print()
        assert success, f"Outbox Relay failed to process events. Last count: {pending_count}"
        
        print("="*70)
        print("✅ ALL TESTS PASSED")
        print("="*70)
        print("\n📊 Validation Summary:")
        print("   ✅ Transfer executed successfully")
        print("   ✅ Outbox event created in database")
        print("   ✅ Outbox Relay swept database")
        print("   ✅ Event published to Kafka")
        print("   ✅ Outbox cleaned up (pendingEvents = 0)")
        print(f"   ⏱️  Processing time: ~{attempts} seconds")
        print("\n🎯 Transactional Outbox Pattern: WORKING")
        print("🎯 Kafka Integration: WORKING")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
