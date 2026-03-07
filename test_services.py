#!/usr/bin/env python3
import requests
import json
import sys
from typing import Dict, Optional

# Service Configuration
SERVICES = {
    "gateway": "http://localhost:8000",
    "core-banking": "http://localhost:8080",
    "ai-service": "http://localhost:50051",
    "notifications": "http://localhost:8081",
    "promotions": "http://localhost:8082",
    "event-consumer": "http://localhost:8083"
}

# Test State
state = {"token": None, "passed": 0, "failed": 0}

def test(name: str, method: str, url: str, **kwargs) -> Optional[requests.Response]:
    """Execute test and track results"""
    try:
        headers = kwargs.get("headers", {})
        if state["token"] and "Authorization" not in headers:
            headers["Authorization"] = f"Bearer {state['token']}"
            kwargs["headers"] = headers
        
        resp = requests.request(method, url, timeout=10, **kwargs)
        
        if resp.status_code < 400:
            print(f"✅ {name}")
            state["passed"] += 1
            return resp
        else:
            print(f"❌ {name} - Status: {resp.status_code}")
            state["failed"] += 1
            return resp
    except Exception as e:
        print(f"❌ {name} - Error: {e}")
        state["failed"] += 1
        return None

def run_tests():
    """Run all service tests"""
    print("\n🚀 TITAN SERVICES TEST\n")
    
    # 1. Health Checks
    print("📊 Health Checks:")
    test("Gateway Health", "GET", f"{SERVICES['gateway']}/health")
    test("Core Banking Health", "GET", f"{SERVICES['core-banking']}/actuator/health")
    
    # 2. Authentication
    print("\n🔐 Authentication:")
    register_resp = test("Register User", "POST", f"{SERVICES['core-banking']}/api/v1/auth/register",
        json={"username": "test_user", "password": "Pass123!", "email": "test@titan.com", 
              "firstName": "Test", "lastName": "User", "pin": "123456"})
    
    login_resp = test("Login User", "POST", f"{SERVICES['core-banking']}/api/v1/auth/login",
        json={"username": "test_user", "password": "Pass123!"})
    
    if login_resp and login_resp.status_code == 200:
        state["token"] = login_resp.json().get("token")
    
    # 3. Account Operations
    print("\n🏦 Account Operations:")
    acc_resp = test("Create Account", "POST", f"{SERVICES['core-banking']}/api/v1/accounts",
        json={"currency": "USD", "accountType": "SAVINGS", "initialDeposit": 1000.00})
    
    test("Get Accounts", "GET", f"{SERVICES['core-banking']}/api/v1/accounts")
    
    # 4. Transactions
    if acc_resp and acc_resp.status_code in [200, 201]:
        acc_num = acc_resp.json().get("accountNumber")
        print("\n💸 Transactions:")
        test("Deposit", "POST", f"{SERVICES['core-banking']}/api/v1/transactions/deposit",
            json={"toAccountNumber": acc_num, "amount": 500.00, "transactionType": "DEPOSIT", "pin": "123456"})
        
        test("Get Transactions", "GET", f"{SERVICES['core-banking']}/api/v1/transactions")
    
    # Results
    total = state["passed"] + state["failed"]
    rate = (state["passed"] / total * 100) if total > 0 else 0
    print(f"\n📈 Results: {state['passed']}/{total} passed ({rate:.0f}%)")
    
    return 0 if state["failed"] == 0 else 1

if __name__ == "__main__":
    sys.exit(run_tests())
