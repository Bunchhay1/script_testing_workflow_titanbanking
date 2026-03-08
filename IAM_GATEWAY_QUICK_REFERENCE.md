# Phase 2: IAM & API Gateway Routing - Quick Reference

## Quick Start

```bash
# Run with Python
python test_iam_gateway_routing.py

# Run with pytest
pytest test_iam_gateway_routing.py -v

# Run specific test
pytest test_iam_gateway_routing.py::test_target_1_iam_login_and_extract_token -v
```

## Test Targets

### Target 1: IAM Login
```python
POST /api/v1/auth/login
Body: {"username": "user", "password": "pass"}
Expected: 200 OK + {"token": "eyJ..."}
```

### Target 2: Gateway with Token
```python
GET /api/v1/accounts
Headers: {"Authorization": "Bearer eyJ..."}
Expected: 200 OK
```

### Target 3: Gateway without Token
```python
GET /api/v1/accounts
Headers: {} (no auth header)
Expected: 401 Unauthorized
```

## Configuration

```python
IAM_BASE_URL = "http://localhost:8080"      # IAM Service
GATEWAY_BASE_URL = "http://localhost:8000"  # API Gateway
```

## Test Flow

```
1. Register test user
2. Login to IAM → Extract JWT token
3. Call Gateway with token → Expect 200
4. Call Gateway without token → Expect 401
5. Call Gateway with invalid token → Expect 401
```

## Expected Results

| Test | Status | Response |
|------|--------|----------|
| IAM Login | ✅ Pass | 200 + Token |
| Gateway + Token | ✅ Pass | 200 OK |
| Gateway - Token | ✅ Pass | 401 Unauthorized |
| Gateway + Invalid | ✅ Pass | 401 Unauthorized |

## Troubleshooting

### IAM Service Not Running
```bash
curl http://localhost:8080/actuator/health
```

### Gateway Not Running
```bash
curl http://localhost:8000/health
```

### Token Not Extracted
Check response structure - token might be under different key:
- `token`
- `accessToken`
- `jwt`

## Integration with CI/CD

### GitHub Actions
```yaml
- name: Run IAM & Gateway Tests
  run: |
    pytest test_iam_gateway_routing.py -v --junitxml=iam-results.xml
```

### Jenkins
```groovy
stage('IAM & Gateway Tests') {
    steps {
        sh 'pytest test_iam_gateway_routing.py -v'
    }
}
```

## Success Criteria

✅ All 4 tests pass  
✅ IAM service responds with valid JWT  
✅ Gateway accepts valid tokens  
✅ Gateway rejects invalid/missing tokens  
✅ Proper HTTP status codes returned
