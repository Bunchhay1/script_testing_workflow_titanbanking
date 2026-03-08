# Phase 1: Idempotency & Ledger Testing

## Overview
Professional pytest script for validating idempotency enforcement in Core Banking System transfer operations.

## Test Coverage
- ✅ Test Case A: Valid transfer with unique idempotency key (200 OK)
- ✅ Test Case B: Duplicate request with same idempotency key (409 Conflict)
- ✅ Test Case C: Multiple transfers with different keys (Bonus)

## Requirements
```bash
pip install pytest requests
```

## Usage

### Run with pytest (Recommended)
```bash
# Run all tests
pytest test_idempotency_ledger.py -v

# Run specific test
pytest test_idempotency_ledger.py::test_case_a_valid_transfer_with_unique_idempotency_key -v

# Run with detailed output
pytest test_idempotency_ledger.py -v -s

# Generate HTML report
pytest test_idempotency_ledger.py --html=report.html --self-contained-html
```

### Run directly with Python
```bash
python test_idempotency_ledger.py
```

## Configuration

Update the following variables in the script:

```python
BASE_URL = "http://localhost:8080"  # Your API base URL

# Update auth credentials in auth_token fixture
payload = {
    "username": "test_user",
    "password": "test_password"
}

# Update account numbers in transfer_payload fixture
"fromAccount": "001202640700",
"toAccount": "001202624829",
```

## Expected Results

### Test Case A: Valid Transfer
```
Status Code: 200 OK
Response: {"transactionId": "...", "status": "SUCCESS"}
```

### Test Case B: Duplicate Detection
```
Status Code: 409 Conflict
Response: {"error": "Duplicate transaction detected", "idempotencyKey": "..."}
```

### Test Case C: Multiple Transfers
```
Request 1: 200 OK
Request 2: 200 OK
Request 3: 200 OK
```

## Test Execution Flow

```
1. Generate UUID for Idempotency-Key
2. Send POST request to /api/v1/core/transfer
3. Validate response status and structure
4. For duplicate test: Resend with SAME key
5. Assert 409 Conflict response
```

## Key Features

- **Dynamic UUID Generation**: Each test generates unique idempotency keys
- **Authentication Support**: Optional JWT token authentication
- **Comprehensive Assertions**: Validates status codes and response structure
- **Clean Documentation**: Professional docstrings for each test
- **Flexible Configuration**: Easy to adapt to different environments
- **Bonus Test**: Validates multiple legitimate transfers

## Troubleshooting

### Connection Refused
```bash
# Check if service is running
curl http://localhost:8080/actuator/health
```

### Authentication Failed
```bash
# Update credentials in auth_token fixture
# Or set auth_token to None if auth not required
```

### 404 Not Found
```bash
# Verify endpoint URL
# Check API documentation for correct path
```

## Integration with CI/CD

### GitHub Actions
```yaml
- name: Run Idempotency Tests
  run: |
    pip install pytest requests
    pytest test_idempotency_ledger.py -v --junitxml=results.xml
```

### Jenkins
```groovy
stage('Idempotency Tests') {
    steps {
        sh 'pytest test_idempotency_ledger.py -v'
    }
}
```

## Author
Senior QA Automation Engineer
Core Banking System - Phase 1 Testing
