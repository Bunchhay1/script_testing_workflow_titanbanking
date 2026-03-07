# Titan Core Banking - Testing Workflow

Comprehensive testing suite for a microservices-based core banking system with 9 testing phases covering infrastructure, business logic, and advanced features.

## Architecture

**Microservices:**
- Core Banking Service (port 8080)
- IAM Service (port 8081)
- Ledger Service (port 8082)
- Promotions Service (port 8083)
- Notifications Service (port 8084)
- API Gateway (port 8000)

**Infrastructure:**
- PostgreSQL (port 5432)
- Redis (port 6379)
- Kafka + Zookeeper (ports 9092, 2181)
- Prometheus (port 9090)
- Grafana (port 3000)
- Config Server (port 8888)

## Quick Start

### Prerequisites
```bash
pip install -r requirements.txt
```

### Start Infrastructure
```bash
docker-compose up -d
./create-kafka-topics.sh
```

### Run Tests
```bash
# Run all phases
./test_phase1.py  # Infrastructure
./test_phase2.py  # Promotions
./test_phase3.py  # Notifications
./test_phase4.py  # Advanced Features
./test_phase5.py  # Orchestration & AI
./test_phase6.py  # Security & Compliance
./test_phase7.py  # Performance & Scalability
./test_phase8.py  # Integration & E2E
./test_phase9.py  # Chaos & Resilience

# Or run service validation
./test_services.py
```

## Testing Phases

### Phase 1: Infrastructure (24 tests)
- DDD & Bounded Contexts
- Infrastructure-as-Code
- Event-Driven Architecture (Kafka)
- Database Setup (PostgreSQL + Flyway)
- Caching (Redis)
- API Gateway (Rate Limiting, Circuit Breaker)
- Monitoring (Prometheus, Grafana)
- Distributed Tracing (Zipkin)
- Security (JWT, OAuth2)
- CI/CD Pipeline

### Phase 2: Promotions Service (24 tests)
- Campaign Management (CRUD)
- Eligibility Engine
- Reward Calculation
- Event-Driven Notifications
- Caching Strategy
- Idempotency
- Saga Pattern
- Monitoring & Metrics
- Security & Authorization
- Performance Testing

### Phase 3: Notifications Service (24 tests)
- Multi-Channel Delivery (Email, SMS, Push)
- Template Management
- Event-Driven Processing
- Retry Mechanism
- Delivery Status Tracking
- Rate Limiting
- Batch Processing
- Monitoring
- Security
- Performance

### Phase 4: Advanced Features (24 tests)
- Real-time Analytics
- Fraud Detection
- Recommendation Engine
- Audit Logging
- Multi-tenancy
- Feature Flags
- A/B Testing
- GraphQL API
- WebSocket Support
- Advanced Caching

### Phase 5: Orchestration & AI (24 tests)
- Saga Orchestration
- CQRS Implementation
- Event Sourcing
- AI/ML Integration
- Predictive Analytics
- Natural Language Processing
- Chatbot Integration
- Anomaly Detection
- Smart Routing
- Automated Decision Making

### Phase 6: Security & Compliance (24 tests)
- Advanced Authentication (MFA, Biometric)
- Authorization (RBAC, ABAC)
- Data Encryption
- PCI-DSS Compliance
- GDPR Compliance
- Audit Trail
- Threat Detection
- Penetration Testing
- Vulnerability Scanning
- Security Monitoring

### Phase 7: Performance & Scalability (24 tests)
- Load Testing
- Stress Testing
- Horizontal Scaling
- Database Sharding
- Read Replicas
- CDN Integration
- Caching Optimization
- Query Optimization
- Connection Pooling
- Resource Management

### Phase 8: Integration & E2E (24 tests)
- End-to-End Workflows
- Third-party Integrations
- Payment Gateway Integration
- KYC/AML Integration
- Credit Bureau Integration
- SMS Gateway Integration
- Email Service Integration
- Document Management
- Reporting Integration
- Analytics Integration

### Phase 9: Chaos & Resilience (24 tests)
- Chaos Engineering
- Fault Injection
- Network Latency Simulation
- Service Failure Recovery
- Database Failure Recovery
- Message Queue Failure
- Cache Failure Handling
- Disaster Recovery
- Backup & Restore
- High Availability Testing

## CI/CD Pipeline

GitHub Actions workflow includes:
- Build with Maven
- Unit & Integration Tests
- Docker Image Build
- Automated Testing
- Deployment to Production

## Monitoring & Observability

**Prometheus Metrics:**
- Service health checks
- Request rates & latencies
- Error rates
- Custom business metrics

**Grafana Dashboards:**
- System overview
- Service-specific metrics
- Alert visualization

**Distributed Tracing:**
- Zipkin integration
- Request flow visualization
- Performance bottleneck identification

## Known Issues

### Port Conflicts
Colima port forwarding may conflict with:
- Prometheus (9090)
- Grafana (3000)
- Kafka (9092)

**Solutions:**
1. Use alternative ports in `docker-compose.yml`
2. Stop Colima port forwarding
3. Update test configurations

### Placeholder Services
IAM, Ledger, and API Gateway are placeholder containers. Actual Spring Boot implementations required for full functionality.

## Test Results

Results are saved in `result test show/` directory:
- `phase1-test-results.txt` through `phase9-test-results.txt`

## Configuration

Edit `CONFIG` dictionary in each test file to adjust:
- Service endpoints
- Database credentials
- Kafka brokers
- Redis connection
- Monitoring endpoints

## Development

**Add New Tests:**
1. Create test function in appropriate phase file
2. Use `test(name, func)` wrapper for consistent reporting
3. Update test count in phase header

**Add New Services:**
1. Add service to `docker-compose.yml`
2. Update test configurations
3. Add health check endpoints
4. Configure Prometheus scraping

## License

MIT
