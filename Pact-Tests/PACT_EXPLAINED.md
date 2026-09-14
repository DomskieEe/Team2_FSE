# How Pact Contract Testing Works

## The Problem

Two services talk to each other:
- Order Service calls Product Service
- Order Service expects specific fields in the response

What happens if Product Service changes a field name?
Order Service crashes. Pact prevents this.

---

## The Solution: Contracts

A contract is an agreement between two services.

**Consumer (Order Service)** says:
> When I call GET /api/v1/products/1, I expect: id, title, price, stock_quantity

**Provider (Product Service)** must fulfill that expectation.

---

## Our Implementation

We define contracts as dictionaries in Python:

```python
PRODUCT_CONTRACT = {
    required_fields: [id, sku, title, price, stock_quantity],
    field_types: {
        price: float,
        stock_quantity: int
    }
}
```

Then we validate responses against them.

---

## The 5 Contracts We Test

1. GET /products/1 returns full product shape
2. GET /products/999 returns 404 with detail
3. GET /products/2 returns stock >= 1
4. GET /products returns a list
5. GET /products/3 returns price > 0

---

## Why This Matters

If Product Service changes price to unit_price, Pact tests FAIL immediately with:
Contract violation: missing field price

We catch the breaking change before deployment.

---

## Why We Did Not Use pact-python Library

The official pact-python library:
- Uses a mock server
- Auto-generates .json contract files
- Does not work on Python 3.14

Our approach:
- Uses real services
- Validates contracts manually with pytest
- Same concept, different implementation

Both achieve the same goal: verify service compatibility.
