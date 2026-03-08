"""
Phase 4: Pessimistic Locking / Race Condition Prevention
Core Banking System - Concurrent Transaction Stress Test

Test Suite: Validates database locking and race condition handling
Author: Senior QA Automation Engineer
Target: Concurrent transfers from same source account
"""

import requests
import uuid
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime


# Configuration
BASE_URL = "http://localhost:8080"
NUM_THREADS = 50
TRANSFER_AMOUNT = 10.00


class StressTestResults:
    """Thread-safe results collector"""
    def __init__(self):
        self.successful = []
        self.failed = []
        self.errors = []
        self.start_time = None
        self.end_time = None
    
    def add_success(self, thread_id, response_data):
        self.successful.append({
            'thread_id': thread_id,
            'data': response_data,
            'timestamp': datetime.now()
        })
    
    def add_failure(self, thread_id, status_code, response_text):
        self.failed.append({
            'thread_id': thread_id,
            'status_code': status_code,
            'response': response_text,
            'timestamp': datetime.now()
        })
    
    def add_error(self, thread_id, error):
        self.errors.append({
            'thread_id': thread_id,
            'error': str(error),
            'timestamp': datetime.now()
        })


def setup_test_account():
    """
    Setup: Create test user with funded account
    Returns: (token, source_account, destination_account)
    """
    print("Setup: Creating test user and accounts...")
    
    # Register user
    username = f"stress_test_{uuid.uuid4().hex[:8]}"
    password = "StressTest123!@#"
    
    register_payload = {
        "username": username,
        "password": password,
        "email": f"{username}@test.com",
        "firstName": "Stress",
        "lastName": "Test",
        "pin": "1234"
    }
    
    requests.post(f"{BASE_URL}/api/v1/auth/register", json=register_payload)
    
    # Login
    login_payload = {"username": username, "password": password}
    login_response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_payload)
    token = login_response.json().get("token")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Create source account with sufficient funds (50 threads * $10 = $500 minimum)
    source_payload = {
        "accountType": "SAVINGS",
        "currency": "USD",
        "initialDeposit": 1000.00  # Extra buffer
    }
    source_resp = requests.post(f"{BASE_URL}/api/v1/accounts", json=source_payload, headers=headers)
    source_account = source_resp.json().get("accountNumber")
    
    # Create destination account
    dest_payload = {
        "accountType": "CHECKING",
        "currency": "USD",
        "initialDeposit": 0.00
    }
    dest_resp = requests.post(f"{BASE_URL}/api/v1/accounts", json=dest_payload, headers=headers)
    dest_account = dest_resp.json().get("accountNumber")
    
    print(f"✅ Test user: {username}")
    print(f"✅ Source account: {source_account} (Balance: $1000.00)")
    print(f"✅ Destination account: {dest_account}\n")
    
    return token, source_account, dest_account


def execute_transfer(thread_id, token, source_account, dest_account, results):
    """
    Worker function: Execute single transfer with unique idempotency key
    
    Args:
        thread_id: Thread identifier
        token: JWT authentication token
        source_account: Source account number
        dest_account: Destination account number
        results: StressTestResults object
    """
    try:
        # Generate unique idempotency key for this request
        idempotency_key = str(uuid.uuid4())
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Idempotency-Key": idempotency_key
        }
        
        payload = {
            "fromAccountNumber": source_account,
            "toAccountNumber": dest_account,
            "amount": TRANSFER_AMOUNT,
            "transactionType": "TRANSFER",
            "pin": "1234",
            "note": f"Stress test thread {thread_id}"
        }
        
        # Execute transfer
        response = requests.post(
            f"{BASE_URL}/api/v1/transactions/transfer",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            results.add_success(thread_id, response.json())
            return True
        else:
            results.add_failure(thread_id, response.status_code, response.text)
            return False
            
    except Exception as e:
        results.add_error(thread_id, e)
        return False


def test_phase4_pessimistic_locking_stress_test():
    """
    Phase 4: Pessimistic Locking Stress Test
    
    Test Flow:
        1. Create test account with $1000 balance
        2. Spin up 50 concurrent threads
        3. Each thread transfers $10 from SAME source account
        4. Each request has unique Idempotency-Key
        5. Validate no deadlocks, race conditions, or data anomalies
    
    Validates:
        - Pessimistic locking prevents race conditions
        - All requests complete without deadlock
        - Final balance is mathematically correct
        - No duplicate transactions
        - System handles high concurrency
    """
    print("\n" + "="*70)
    print("🔒 PHASE 4: PESSIMISTIC LOCKING STRESS TEST")
    print("="*70 + "\n")
    
    # Setup
    token, source_account, dest_account = setup_test_account()
    results = StressTestResults()
    
    # Get initial balance
    headers = {"Authorization": f"Bearer {token}"}
    try:
        initial_response = requests.get(f"{BASE_URL}/api/v1/accounts", headers=headers)
        accounts = initial_response.json()
        
        # Handle both list and dict responses
        if isinstance(accounts, list):
            initial_balance = next((acc['balance'] for acc in accounts if acc['accountNumber'] == source_account), 1000.00)
        else:
            # If it's a dict with accounts key
            accounts_list = accounts.get('accounts', accounts.get('data', []))
            initial_balance = next((acc['balance'] for acc in accounts_list if acc['accountNumber'] == source_account), 1000.00)
    except Exception as e:
        print(f"⚠️  Error getting initial balance: {e}")
        initial_balance = 1000.00  # Fallback to known initial deposit
    
    print(f"Initial source balance: ${initial_balance:.2f}\n")
    
    # Execute concurrent transfers
    print(f"Executing {NUM_THREADS} concurrent transfers...")
    print(f"Each thread transfers ${TRANSFER_AMOUNT:.2f} from {source_account}")
    print(f"Expected total deduction: ${NUM_THREADS * TRANSFER_AMOUNT:.2f}\n")
    
    results.start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
        # Submit all tasks
        futures = [
            executor.submit(execute_transfer, i, token, source_account, dest_account, results)
            for i in range(NUM_THREADS)
        ]
        
        # Wait for completion with progress
        completed = 0
        for future in as_completed(futures):
            completed += 1
            if completed % 10 == 0:
                print(f"   Progress: {completed}/{NUM_THREADS} threads completed")
    
    results.end_time = time.time()
    duration = results.end_time - results.start_time
    
    print(f"\n✅ All threads completed in {duration:.2f} seconds\n")
    
    # Get final balance
    try:
        final_response = requests.get(f"{BASE_URL}/api/v1/accounts", headers=headers)
        accounts = final_response.json()
        
        # Handle both list and dict responses
        if isinstance(accounts, list):
            final_balance = next((acc['balance'] for acc in accounts if acc['accountNumber'] == source_account), None)
        else:
            accounts_list = accounts.get('accounts', accounts.get('data', []))
            final_balance = next((acc['balance'] for acc in accounts_list if acc['accountNumber'] == source_account), None)
        
        if final_balance is None:
            print(f"⚠️  Could not find source account {source_account} in response")
            final_balance = initial_balance  # Fallback
    except Exception as e:
        print(f"⚠️  Error getting final balance: {e}")
        final_balance = initial_balance  # Fallback
    
    # Calculate expected balance
    expected_balance = initial_balance - (NUM_THREADS * TRANSFER_AMOUNT)
    actual_deduction = initial_balance - final_balance
    
    # Results summary
    print("="*70)
    print("📊 STRESS TEST RESULTS")
    print("="*70 + "\n")
    
    print(f"Concurrency:")
    print(f"   Threads: {NUM_THREADS}")
    print(f"   Duration: {duration:.2f}s")
    print(f"   Throughput: {NUM_THREADS/duration:.2f} TPS\n")
    
    print(f"Request Results:")
    print(f"   ✅ Successful: {len(results.successful)}")
    print(f"   ❌ Failed: {len(results.failed)}")
    print(f"   ⚠️  Errors: {len(results.errors)}\n")
    
    print(f"Balance Verification:")
    print(f"   Initial balance: ${initial_balance:.2f}")
    print(f"   Final balance: ${final_balance:.2f}")
    print(f"   Expected balance: ${expected_balance:.2f}")
    print(f"   Actual deduction: ${actual_deduction:.2f}")
    print(f"   Expected deduction: ${NUM_THREADS * TRANSFER_AMOUNT:.2f}\n")
    
    # Show any failures/errors for debugging
    if results.failed:
        print("⚠️  Failed Requests:")
        for failure in results.failed[:5]:
            print(f"   Thread {failure['thread_id']}: {failure['status_code']} - {failure['response'][:200]}")
        print()
    
    if results.errors:
        print("⚠️  Errors:")
        for error in results.errors[:5]:
            print(f"   Thread {error['thread_id']}: {error['error'][:200]}")
        print()
    
    # Assertions
    print("Validating results...\n")
    
    # Assert 1: No deadlocks (all requests completed)
    total_requests = len(results.successful) + len(results.failed) + len(results.errors)
    assert total_requests == NUM_THREADS, (
        f"Not all requests completed. Expected {NUM_THREADS}, got {total_requests}"
    )
    print("✅ Assert 1: All requests completed (no deadlocks)")
    
    # Assert 2: All returned 200 OK
    assert len(results.successful) == NUM_THREADS, (
        f"Not all requests succeeded. {len(results.failed)} failed, {len(results.errors)} errors"
    )
    print("✅ Assert 2: All requests returned 200 OK")
    
    # Assert 3: Balance is mathematically correct (no race conditions)
    balance_diff = abs(final_balance - expected_balance)
    assert balance_diff < 0.01, (
        f"Balance mismatch! Expected ${expected_balance:.2f}, got ${final_balance:.2f}. "
        f"Difference: ${balance_diff:.2f}"
    )
    print("✅ Assert 3: Balance is mathematically correct")
    
    # Assert 4: No data anomalies
    assert actual_deduction == (NUM_THREADS * TRANSFER_AMOUNT), (
        f"Deduction mismatch! Expected ${NUM_THREADS * TRANSFER_AMOUNT:.2f}, "
        f"got ${actual_deduction:.2f}"
    )
    print("✅ Assert 4: No data anomalies detected")
    
    print("\n" + "="*70)
    print("✅ PHASE 4 TEST PASSED")
    print("="*70)
    print("\n🎯 Key Validations:")
    print("   ✅ Pessimistic locking working correctly")
    print("   ✅ No race conditions detected")
    print("   ✅ No deadlocks occurred")
    print("   ✅ Data integrity maintained")
    print("   ✅ System handles high concurrency")
    print(f"   ✅ Throughput: {NUM_THREADS/duration:.2f} TPS")
    
    # Show any failures for debugging
    if results.failed:
        print("\n⚠️  Failed Requests:")
        for failure in results.failed[:5]:  # Show first 5
            print(f"   Thread {failure['thread_id']}: {failure['status_code']} - {failure['response'][:200]}")
    
    if results.errors:
        print("\n⚠️  Errors:")
        for error in results.errors[:5]:  # Show first 5
            print(f"   Thread {error['thread_id']}: {error['error'][:200]}")


if __name__ == "__main__":
    """
    Run stress test directly
    """
    try:
        test_phase4_pessimistic_locking_stress_test()
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        print("\n💡 Possible Issues:")
        print("   - Race condition detected (balance mismatch)")
        print("   - Deadlock occurred (requests didn't complete)")
        print("   - Pessimistic locking not implemented")
        print("   - Database transaction isolation level incorrect")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
