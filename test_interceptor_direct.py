#!/usr/bin/env python3
"""
Direct test to verify if Redis interceptor is caching responses
"""

import requests
import uuid
import time

BASE_URL = "http://localhost:8080/api/v1"

def test_interceptor():
    print("\n" + "="*70)
    print("🔍 DIRECT INTERCEPTOR TEST")
    print("="*70)
    
    # Register and login
    username = f"interceptor_test_{uuid.uuid4().hex[:8]}"
    register_payload = {
        "username": username,
        "password": "Test123!",
        "email": f"{username}@test.com",
        "firstName": "Test",
        "lastName": "User",
        "pin": "1234"
    }
    
    print("\nAuthenticating...")
    requests.post(f"{BASE_URL}/auth/register", json=register_payload)
    login_response = requests.post(f"{BASE_URL}/auth/login", json={
        "username": username,
        "password": "Test123!"
    })
    token = login_response.json()["token"]
    print(f"✅ Authenticated as {username}")
    
    # Create accounts
    headers = {"Authorization": f"Bearer {token}"}
    acc1 = requests.post(f"{BASE_URL}/accounts", json={
        "accountType": "SAVINGS",
        "currency": "USD",
        "initialDeposit": 1000.00
    }, headers=headers).json()
    
    acc2 = requests.post(f"{BASE_URL}/accounts", json={
        "accountType": "CHECKING",
        "currency": "USD",
        "initialDeposit": 1000.00
    }, headers=headers).json()
    
    source = acc1["accountNumber"]
    dest = acc2["accountNumber"]
    print(f"✅ Created accounts: {source} → {dest}\n")
    
    # Test with same idempotency key
    idempotency_key = str(uuid.uuid4())
    transfer_payload = {
        "fromAccountNumber": source,
        "toAccountNumber": dest,
        "amount": 50.00,
        "transactionType": "TRANSFER",
        "pin": "1234",
        "note": "Interceptor test"
    }
    
    headers_with_key = {
        "Authorization": f"Bearer {token}",
        "Idempotency-Key": idempotency_key
    }
    
    print(f"Idempotency-Key: {idempotency_key}\n")
    
    # First request
    print("Request 1: Sending transfer...")
    start1 = time.time()
    response1 = requests.post(f"{BASE_URL}/transactions/transfer", 
                              json=transfer_payload, 
                              headers=headers_with_key)
    duration1 = time.time() - start1
    
    print(f"   Status: {response1.status_code}")
    print(f"   Duration: {duration1*1000:.0f}ms")
    print(f"   Transaction ID: {response1.json().get('id')}")
    
    # Wait a moment
    time.sleep(0.5)
    
    # Second request (duplicate)
    print("\nRequest 2: Sending DUPLICATE transfer...")
    start2 = time.time()
    response2 = requests.post(f"{BASE_URL}/transactions/transfer", 
                              json=transfer_payload, 
                              headers=headers_with_key)
    duration2 = time.time() - start2
    
    print(f"   Status: {response2.status_code}")
    print(f"   Duration: {duration2*1000:.0f}ms")
    print(f"   Transaction ID: {response2.json().get('id')}")
    
    # Analysis
    print("\n" + "="*70)
    print("📊 ANALYSIS")
    print("="*70)
    
    tx_id_1 = response1.json().get('id')
    tx_id_2 = response2.json().get('id')
    
    print(f"\nResponse 1 Transaction ID: {tx_id_1}")
    print(f"Response 2 Transaction ID: {tx_id_2}")
    print(f"Same Transaction ID: {tx_id_1 == tx_id_2}")
    
    print(f"\nRequest 1 Duration: {duration1*1000:.0f}ms")
    print(f"Request 2 Duration: {duration2*1000:.0f}ms")
    
    if duration2 < duration1 * 0.5:
        print("✅ Request 2 was MUCH faster → Likely cached by interceptor")
    elif duration2 < duration1 * 0.8:
        print("⚠️  Request 2 was faster → Possibly cached")
    else:
        print("❌ Request 2 took similar time → NOT cached by interceptor")
    
    if response2.status_code == 200 and tx_id_1 == tx_id_2:
        print("\n✅ INTERCEPTOR WORKING: Returned cached response (200 with same TX ID)")
    elif response2.status_code == 409:
        print("\n✅ SERVICE LAYER WORKING: Rejected duplicate (409)")
    else:
        print("\n❌ IDEMPOTENCY NOT WORKING: Different transaction created")
    
    print()

if __name__ == "__main__":
    test_interceptor()
