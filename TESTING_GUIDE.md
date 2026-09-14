# 🧪 Testing Guide: Integration & Contract Testing Explained

## Table of Contents
1. [Overview](#overview)
2. [Integration Testing](#integration-testing)
3. [Pact Contract Testing](#pact-contract-testing)
4. [Key Differences](#key-differences)
5. [Running the Tests](#running-the-tests)
6. [Best Practices](#best-practices)

---

## Overview

This project uses **two complementary testing strategies** to ensure microservices work correctly together:

| Testing Type | Purpose | Scope | When to Run |
|-------------|---------|-------|-------------|
| **Integration Testing** | Verify services work together end-to-end | Full system | After deployment, CI/CD |
| **Contract Testing (Pact)** | Verify API contracts between services | Service boundaries | Before integration, during development |

---

## Integration Testing

### 🎯 What Is Integration Testing?

Integration testing verifies that **multiple services work together correctly** as a complete system. It tests the **actual behavior** of services communicating over real HTTP connections.

### 📍 Location
```
Integration-Tests/
├── test_integration.py    # All integration tests
├── requirements.txt       # pytest, requests
└── Dockerfile            # Test runner container
```

### 🔍 How It Works

#### 1. **Test Setup - Reset All Services**
```python
@pytest.fixture(autouse=True)
def reset_all_services():
    # Reset Product Service to baseline data
    r1 = requests.post(f'{PRODUCT_SERVICE_URL}/api/v1/test/reset')
    
    # Reset Order Service to baseline data
    r2 = requests.post(f'{ORDER_SERVICE_URL}/api/v1/test/reset')
    
    assert r1.status_code == 200
    assert r2.status_code == 200
    yield
```

**Why?** Each test starts with a **clean slate** - consistent, predictable data.

#### 2. **Test Real Service Interactions**

**Example: Creating a Product**
```python
def test_integration_1_create_new_product():
    # Send POST request to Product Service
    payload = {
        'sku': 'TEST-001',
        'title': 'Motorcycle Cover',
        'description': 'Premium cover',
        'price': 1200.0,
        'stock_quantity': 15
    }
    
    response = requests.post(
        f'{PRODUCT_SERVICE_URL}/api/v1/products',
        json=payload
    )
    
    # Verify response
    assert response.status_code == 201
    body = response.json()
    assert body['title'] == payload['title']
    assert 'id' in body
```

**Example: Cross-Service Order Flow**
```python
def test_integration_8_full_order_flow():
    # Step 1: Create a product in Product Service
    product = requests.post(
        f'{PRODUCT_SERVICE_URL}/api/v1/products',
        json={
            'sku': 'TEST-G',
            'title': 'Gloves',
            'description': 'Test',
            'price': 600.0,
            'stock_quantity': 20
        }
    )
    assert product.status_code == 201
    product_id = product.json()['id']
    
    # Step 2: Create an order in Order Service
    # (Order Service will call Product Service to validate stock)
    order = requests.post(
        f'{ORDER_SERVICE_URL}/api/v1/orders',
        json={
            'product_id': product_id,
            'quantity': 3,
            'shipping_address': 'Test Address'
        }
    )
    assert order.status_code == 201
    order_id = order.json()['id']
    
    # Step 3: Update the order status
    update = requests.put(
        f'{ORDER_SERVICE_URL}/api/v1/orders/{order_id}',
        json={'status': 'CONFIRMED'}
    )
    assert update.status_code == 200
```

### 📊 Our Integration Tests

| Test | Description | What It Verifies |
|------|-------------|------------------|
| `test_integration_1_create_new_product` | Create a new product | Product Service can create products |
| `test_integration_2_created_product_in_catalog` | Verify product appears in catalog | Created product is retrievable |
| `test_integration_3_place_new_order` | Place an order | Order Service creates orders |
| `test_integration_4_place_order_insufficient_stock` | Try to order more than available | Stock validation works |
| `test_integration_5_place_order_nonexistent_product` | Order non-existent product | Product validation works |
| `test_integration_6_update_existing_order` | Update order status | Order updates work |
| `test_integration_7_update_nonexistent_order` | Update non-existent order | Error handling works |
| `test_integration_8_full_order_flow` | Complete product → order → update flow | End-to-end workflow succeeds |

### ✅ What Integration Tests Catch

- ❌ **Network issues** - Can services reach each other?
- ❌ **Data flow issues** - Does data pass correctly between services?
- ❌ **Business logic errors** - Do multi-service workflows work?
- ❌ **Environment problems** - Are ports, URLs, configs correct?

### ❌ What Integration Tests DON'T Catch

- Breaking API contract changes **before deployment**
- Service version incompatibilities during development
- Changes to response structure that haven't been deployed yet

---

## Pact Contract Testing

### 🎯 What Is Contract Testing?

Contract testing verifies that services **agree on the API structure** (the "contract"). It ensures:
- **Consumer** (Order Service) expects certain fields
- **Provider** (Product Service) delivers those fields

This catches breaking changes **before they reach integration testing**.

### 📍 Location
```
Pact-Tests/
├── consumer/
│   └── test_pact_consumer.py    # Consumer expectations
├── provider/
│   └── test_pact_provider.py    # Provider verification
├── PACT_EXPLAINED.md
├── README.md
└── requirements.txt
```

### 🔍 How It Works

#### The Contract Definition

```python
PRODUCT_CONTRACT = {
    # Required fields that MUST exist in response
    'required_fields': [
        'id',
        'sku',
        'title',
        'description',
        'price',
        'stock_quantity'
    ],
    
    # Expected data types
    'field_types': {
        'id': int,
        'sku': str,
        'title': str,
        'description': str,
        'price': float,
        'stock_quantity': int
    },
    
    # Business rules/constraints
    'constraints': {
        'price': lambda v: v > 0,           # Price must be positive
        'stock_quantity': lambda v: v >= 0  # Stock can't be negative
    }
}
```

#### Consumer Side (Order Service Expectations)

**Test: Consumer expects product structure**
```python
def test_contract1_get_existing_product_by_id():
    # Order Service calls Product Service
    response = requests.get(f'{PRODUCT_SERVICE_URL}/api/v1/products/1')
    
    assert response.status_code == 200
    body = response.json()
    
    # Validate the contract
    validate_contract(body, PRODUCT_CONTRACT)
    
    # Verify expected behavior
    assert body['id'] == 1
```

**The Contract Validator**
```python
def validate_contract(body: dict, contract: dict):
    # Check all required fields exist
    for field in contract['required_fields']:
        assert field in body, f'Missing field: {field}'
    
    # Check field types match
    for field, expected_type in contract['field_types'].items():
        assert isinstance(body[field], expected_type), \
            f'{field} has wrong type'
    
    # Check constraints are satisfied
    for field, constraint in contract.get('constraints', {}).items():
        assert constraint(body[field]), \
            f'{field} failed constraint'
```

#### Provider Side (Product Service Fulfillment)

**Test: Provider satisfies consumer expectations**
```python
def test_provider_contract1_get_product_by_id():
    # Product Service must return correct structure
    r = requests.get(f'{PROVIDER_BASE_URL}/api/v1/products/1')
    
    assert r.status_code == 200
    body = r.json()
    
    # Verify all expected fields exist with correct types
    assert isinstance(body.get('id'), int)
    assert isinstance(body.get('title'), str)
    assert isinstance(body.get('price'), float)
    assert isinstance(body.get('stock_quantity'), int)
```

### 📊 Our Pact Contracts

| Contract | Consumer Expectation | Provider Verification |
|----------|---------------------|----------------------|
| **Contract 1** | GET /products/{id} returns full product | Provider returns all required fields |
| **Contract 2** | GET /products/999 returns 404 | Provider returns 404 for non-existent |
| **Contract 3** | Product has stock_quantity >= 1 | Provider returns valid stock data |
| **Contract 4** | GET /products returns a list | Provider returns array of products |
| **Contract 5** | Product price > 0 | Provider enforces positive prices |

### 🔥 Real-World Example: Catching Breaking Changes

#### Scenario: Developer Changes Product API

**Before: Product Service returns**
```json
{
  "id": 1,
  "sku": "SED-TOY-001",
  "title": "Toyota Vios",
  "description": "Reliable sedan",
  "price": 18000.0,
  "stock_quantity": 12
}
```

**After: Developer renames field**
```json
{
  "id": 1,
  "sku": "SED-TOY-001",
  "title": "Toyota Vios",
  "description": "Reliable sedan",
  "unit_price": 18000.0,    // ❌ Changed from "price"
  "stock_quantity": 12
}
```

#### What Happens?

**Without Contract Testing:**
1. ✅ Product Service tests pass (field exists)
2. ✅ Product Service deploys successfully
3. ❌ Order Service crashes in production (can't find "price")
4. 🔥 **System is down!**

**With Contract Testing:**
1. Developer changes `price` → `unit_price`
2. ❌ Consumer contract test **FAILS immediately**
   ```
   Contract violation: missing field 'price'
   ```
3. ❌ Provider contract test **FAILS**
   ```
   AssertionError: 'price' not in response
   ```
4. 🛑 **Breaking change detected BEFORE deployment**
5. ✅ Developer fixes the issue or updates both services together

### ✅ What Contract Tests Catch

- ❌ **Breaking API changes** - Field renames, removals
- ❌ **Type mismatches** - Changing int to string
- ❌ **Missing required fields** - Removing expected data
- ❌ **Constraint violations** - Negative prices, invalid data
- ❌ **Status code changes** - 200 → 404 unexpectedly

---

## Key Differences

| Aspect | Integration Testing | Contract Testing |
|--------|-------------------|------------------|
| **Scope** | Full system, all services | Service boundaries only |
| **Goal** | Verify services work together | Verify API agreements |
| **Execution** | After deployment | During development |
| **Speed** | Slower (full stack) | Faster (isolated) |
| **Catches** | Runtime issues | API breaking changes |
| **Test Data** | Real data, real databases | Mock data acceptable |
| **Environment** | Requires all services running | Can test one service at a time |
| **When it Fails** | Something is broken in deployed system | API contract was violated |

### 🎯 When to Use Each

**Use Integration Testing When:**
- ✅ Testing complete user workflows
- ✅ Verifying deployed system works
- ✅ Testing cross-service transactions
- ✅ Validating environment configuration

**Use Contract Testing When:**
- ✅ Developing new API endpoints
- ✅ Changing existing API responses
- ✅ Before merging code changes
- ✅ Preventing breaking changes

**Best Practice: Use BOTH!**
1. **Contract tests** run in CI/CD **before** merge
2. **Integration tests** run **after** deployment to staging

---


## Running the Tests

### 🐳 Using Docker Compose (Recommended)

#### Run Integration Tests
```powershell
# Start all services
docker-compose up --build

# In another terminal, run integration tests
docker-compose run test-runner

# Expected output:
# test_integration_1_create_new_product PASSED
# test_integration_2_created_product_in_catalog PASSED
# test_integration_3_place_new_order PASSED
# ... (8 tests total)
```

#### Run Pact Tests
```powershell
# Consumer tests (what Order Service expects)
cd Pact-Tests
pytest consumer/test_pact_consumer.py -v

# Provider tests (what Product Service delivers)
pytest provider/test_pact_provider.py -v
```

### 💻 Running Locally (Without Docker)

#### Prerequisites
```powershell
# Ensure both services are running
cd Product-Service
python app.py  # Port 5001

# In another terminal
cd Order-Service
python app.py  # Port 5002
```

#### Run Integration Tests
```powershell
cd Integration-Tests
pip install -r requirements.txt
pytest test_integration.py -v
```

#### Run Pact Tests
```powershell
cd Pact-Tests
pip install -r requirements.txt

# Consumer side
pytest consumer/test_pact_consumer.py -v

# Provider side
pytest provider/test_pact_provider.py -v
```

### 📊 Expected Test Results

#### Integration Tests Output
```
test_integration_1_create_new_product PASSED
  [Test 1 PASSED] Created: id=16 Motorcycle Cover

test_integration_2_created_product_in_catalog PASSED
  [Test 2 PASSED] Product id=17 in catalog

test_integration_3_place_new_order PASSED
  [Test 3 PASSED] Order placed

test_integration_4_place_order_insufficient_stock PASSED
  [Test 4 PASSED] Insufficient stock rejected

test_integration_5_place_order_nonexistent_product PASSED
  [Test 5 PASSED] Non-existent product rejected

test_integration_6_update_existing_order PASSED
  [Test 6 PASSED] Order updated

test_integration_7_update_nonexistent_order PASSED
  [Test 7 PASSED] Non-existent order rejected

test_integration_8_full_order_flow PASSED
  [Test 8 PASSED] Full flow complete

========================= 8 passed in 2.34s =========================
```

#### Pact Tests Output
```
Consumer Tests:
test_contract1_get_existing_product_by_id PASSED
  [Contract 1 PASSED] Product: Toyota Vios

test_contract2_get_nonexistent_product_returns_404 PASSED
  [Contract 2 PASSED] 404 detail: Product not found

test_contract3_product_has_sufficient_stock PASSED
  [Contract 3 PASSED] Stock available: 4

test_contract4_get_all_products_returns_list PASSED
  [Contract 4 PASSED] Total products: 15

test_contract5_product_price_is_positive PASSED
  [Contract 5 PASSED] Price: 24000.0

========================= 5 passed in 1.12s =========================

Provider Tests:
test_provider_contract1_get_product_by_id PASSED
  [Contract 1 VERIFIED]

test_provider_contract2_nonexistent_product_404 PASSED
  [Contract 2 VERIFIED]

test_provider_contract3_product_has_stock PASSED
  [Contract 3 VERIFIED]

test_provider_contract4_returns_product_list PASSED
  [Contract 4 VERIFIED]

test_provider_contract5_price_is_positive PASSED
  [Contract 5 VERIFIED]

test_provider_fulfills_all_contracts PASSED
  [All contracts PASSED]

========================= 6 passed in 0.89s =========================
```

---

## Best Practices

### 🎯 Testing Strategy

#### Development Workflow
```
1. Write Contract Tests FIRST
   ├─ Define consumer expectations
   ├─ Implement provider to satisfy contract
   └─ Both pass? → Continue

2. Implement Feature
   └─ Business logic, database operations

3. Write Integration Tests
   └─ Test end-to-end workflows

4. Deploy to Staging
   └─ Run integration tests against staging

5. Deploy to Production
   └─ Monitor with health checks
```

#### CI/CD Pipeline Integration
```yaml
# Example GitHub Actions / Azure DevOps

stages:
  - name: "Contract Tests"
    run: |
      pytest Pact-Tests/consumer/ -v
      pytest Pact-Tests/provider/ -v
    # ❌ If fails → Block merge
    
  - name: "Build & Deploy to Staging"
    depends_on: ["Contract Tests"]
    run: |
      docker-compose build
      docker-compose up -d
    
  - name: "Integration Tests"
    depends_on: ["Build & Deploy to Staging"]
    run: |
      docker-compose run test-runner
    # ❌ If fails → Block production deploy
    
  - name: "Deploy to Production"
    depends_on: ["Integration Tests"]
    run: |
      # Deploy to prod
```

### 📝 Writing Good Tests

#### DO ✅

- **Keep tests independent** - Each test should run in isolation
- **Use descriptive names** - `test_order_fails_when_stock_insufficient`
- **Reset state between tests** - Use fixtures to ensure clean state
- **Test both happy and sad paths** - Success AND failure scenarios
- **Make assertions meaningful** - Check specific values, not just "status 200"

#### DON'T ❌

- **Don't test implementation details** - Test behavior, not internal code
- **Don't make tests dependent** - Test 2 shouldn't rely on Test 1
- **Don't skip error cases** - 404, 400, 500 responses matter!
- **Don't hardcode test data** - Use fixtures or factories
- **Don't ignore flaky tests** - Fix them or remove them

### 🔧 Test Data Management (TDM)

Our project uses **TDM seeder** to populate baseline test data:

```python
# TDM seeds initial products
tdm-seeder:
  depends_on:
    - product-service
    - order-service
  environment:
    - PRODUCT_SERVICE_URL=http://product-service:5001
    - ORDER_SERVICE_URL=http://order-service:5002
```

**Benefits:**
- ✅ Consistent baseline data across all tests
- ✅ Reproducible test results
- ✅ Fast test setup (pre-seeded data)
- ✅ Realistic test scenarios

### 🚀 Troubleshooting

#### Integration Tests Failing?

**Problem:** Connection refused
```
requests.exceptions.ConnectionError: Failed to establish connection
```
**Solution:** Ensure services are running
```powershell
docker-compose ps  # Check service status
docker-compose logs product-service  # Check logs
```

**Problem:** Test data inconsistency
```
AssertionError: expected product id=1, got id=16
```
**Solution:** Ensure reset endpoint is called
```python
@pytest.fixture(autouse=True)
def reset_all_services():
    requests.post(f'{PRODUCT_SERVICE_URL}/api/v1/test/reset')
```

#### Contract Tests Failing?

**Problem:** Contract violation
```
AssertionError: Contract violation: missing field 'price'
```
**Solution:** Check if provider changed API
```python
# Provider must return all fields in contract
PRODUCT_CONTRACT = {
    'required_fields': ['id', 'sku', 'title', 'description', 'price', 'stock_quantity']
}
```

**Problem:** Type mismatch
```
AssertionError: price has wrong type (expected float, got str)
```
**Solution:** Ensure correct JSON serialization
```python
# FastAPI/Pydantic models should specify types
class ProductResponse(BaseModel):
    price: float  # Not str!
```

---

## Summary

### 🎯 Key Takeaways

1. **Integration Testing**
   - Tests the **entire system working together**
   - Catches runtime and deployment issues
   - Run **after** deployment or in staging
   - Slower but comprehensive

2. **Contract Testing (Pact)**
   - Tests **API agreements between services**
   - Catches breaking changes before deployment
   - Run **during development** and before merge
   - Fast and focused

3. **Use Both**
   - Contract tests = **Pre-deployment safety net**
   - Integration tests = **Post-deployment verification**
   - Together they provide comprehensive coverage

4. **Testing Pyramid**
   ```
        /\
       /  \  ← Integration Tests (few, slow, comprehensive)
      /----\
     / Pact \  ← Contract Tests (medium, fast, focused)
    /--------\
   /   Unit   \ ← Unit Tests (many, very fast, isolated)
  /------------\
   ```

### 📚 Further Reading

- [Pact Documentation](https://docs.pact.io/)
- [Martin Fowler - Contract Testing](https://martinfowler.com/bliki/ContractTest.html)
- [Testing Microservices](https://martinfowler.com/articles/microservice-testing/)
- [Integration Testing Best Practices](https://testautomationpatterns.org/)

---

## Quick Reference

### Commands Cheat Sheet

```powershell
# Start all services
docker-compose up --build

# Run integration tests
docker-compose run test-runner

# Run contract tests (consumer)
cd Pact-Tests && pytest consumer/test_pact_consumer.py -v

# Run contract tests (provider)
cd Pact-Tests && pytest provider/test_pact_provider.py -v

# Run all pact tests
cd Pact-Tests && pytest -v

# Stop all services
docker-compose down

# View logs
docker-compose logs -f product-service
docker-compose logs -f order-service
```

### File Structure Reference

```
Team2_FSE/
├── Integration-Tests/          # End-to-end system tests
│   ├── test_integration.py     # 8 integration tests
│   ├── requirements.txt
│   └── Dockerfile
│
├── Pact-Tests/                 # Contract tests
│   ├── consumer/               # Order Service expectations
│   │   └── test_pact_consumer.py
│   ├── provider/               # Product Service verification
│   │   └── test_pact_provider.py
│   ├── PACT_EXPLAINED.md
│   ├── README.md
│   └── requirements.txt
│
├── Product-Service/            # Provider service
│   ├── app.py                  # FastAPI app with /api/v1/test/reset
│   └── products.db
│
├── Order-Service/              # Consumer service
│   ├── app.py                  # FastAPI app with /api/v1/test/reset
│   └── orders.db
│
├── TDM/                        # Test Data Management
│   ├── seed.py                 # Seeds initial test data
│   └── fixtures/
│       └── products.json
│
├── docker-compose.yml          # Orchestrates all services
└── TESTING_GUIDE.md           # This file!
```

---

**Happy Testing! 🧪✅**

*Remember: Good tests catch bugs before users do!*
