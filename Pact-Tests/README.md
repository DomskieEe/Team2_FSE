# Pact Contract Tests — Team2 FSE

Contract tests for the e-commerce microservices.
- Consumer = Order Service
- Provider = Product Service

---

## Setup

```bash
cd Pact-Tests
py -m pip install -r requirements.txt
```

---

## How to Run

### Step 1 — Start Product Service (separate terminal)

```bash
cd Product-Service
py app.py
```

### Step 2 — Run Consumer Tests

```bash
cd Pact-Tests
py -m pytest consumer/test_pact_consumer.py -v
```

### Step 3 — Run Provider Verification

```bash
cd Pact-Tests
py -m pytest provider/test_pact_provider.py -v
```

### Run Everything

```bash
cd Pact-Tests
py -m pytest -v
```

---

## Contracts

| # | Request | Expected | Description |
|---|---|---|---|
| 1 | GET /products/1 | 200 + {id,name,price,stock} | Get existing product |
| 2 | GET /products/999 | 404 + {detail} | Non-existent product |
| 3 | GET /products/2 | 200 + stock >= 1 | Sufficient stock check |
| 4 | GET /products | 200 + list | Get all products |
| 5 | GET /products/3 | 200 + price > 0 | Valid price for order total |

---

## Test Data Management

Both services have a `/test/reset` endpoint.
The `autouse=True` fixture in each test file calls reset before every test,
ensuring a clean, predictable state every time.

Seed data (Product Service):
- id:1 Gixxer 155 Full Face Helmet — price: 4500.0, stock: 10
- id:2 Riding Armored Jacket — price: 3200.0, stock: 5
- id:3 Brembo Brake Pads — price: 850.0, stock: 25
