# Pact Contract Testing Explained

## The Problem

Order Service calls Product Service.
If Product Service changes response fields, Order Service crashes.

## The Solution

Define a contract - an agreement on the response shape.

## Our 5 Contracts

1. GET /products/1 returns full product
2. GET /products/999 returns 404
3. GET /products/2 has stock >= 1
4. GET /products returns a list
5. GET /products/3 price > 0

## Implementation

Consumer defines expected shape:
```python
CONTRACT = {
    'required_fields': ['id', 'title', 'price', 'stock_quantity']
}
```

Provider verifies it fulfills that shape:
```python
assert 'price' in response
assert isinstance(response['price'], float)
```

## Why It Matters

If Product Service changes `price` to `unit_price`,
Pact tests fail immediately before deployment.

## Why No pact-python Library

The official library needs Python 3.11 or lower.
We have Python 3.14, so we implemented the same concept manually.
