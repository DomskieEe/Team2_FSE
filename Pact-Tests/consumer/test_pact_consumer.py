# Pact-Tests/consumer/test_pact_consumer.py
#
# CONTRACT TESTING — CONSUMER SIDE
# Consumer = Order Service
# Provider = Product Service
#
# These tests define and validate the CONTRACT between Order Service
# and Product Service. Instead of a Pact mock server, we define the
# expected response shapes as contracts and validate them directly.
#
# HOW TO RUN:
#   1. Start Product Service: cd ../../Product-Service && python app.py
#   2. Run: pytest consumer/test_pact_consumer.py -v

import pytest
import requests

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────

PRODUCT_SERVICE_URL = "http://127.0.0.1:5001"


# ─────────────────────────────────────────────
# CONTRACT DEFINITIONS
# These define what Order Service EXPECTS from Product Service.
# Think of these as the "pact" — the agreed-upon shapes.
# ─────────────────────────────────────────────

PRODUCT_CONTRACT = {
    "required_fields": ["id", "name", "price", "stock"],
    "field_types": {
        "id":    int,
        "name":  str,
        "price": float,
        "stock": int
    },
    "constraints": {
        "price": lambda v: v > 0,
        "stock": lambda v: v >= 0
    }
}

PRODUCT_LIST_CONTRACT = {
    "type": list,
    "min_length": 1,
    "item_contract": PRODUCT_CONTRACT
}

ERROR_CONTRACT = {
    "required_fields": ["detail"],
    "field_types": {"detail": str}
}


def validate_contract(body: dict, contract: dict):
    """Helper: validates a response body against a contract definition."""
    for field in contract["required_fields"]:
        assert field in body, f"Contract violation: missing field '{field}'"

    for field, expected_type in contract["field_types"].items():
        assert isinstance(body[field], expected_type), (
            f"Contract violation: '{field}' expected {expected_type.__name__}, "
            f"got {type(body[field]).__name__}"
        )

    for field, constraint in contract.get("constraints", {}).items():
        assert constraint(body[field]), (
            f"Contract violation: '{field}' value {body[field]} failed constraint"
        )


# ─────────────────────────────────────────────
# FIXTURE: Reset Product Service before each test
# ─────────────────────────────────────────────

@pytest.fixture(autouse=True)
def reset_product_service():
    """Resets Product Service to known seed data before each test."""
    response = requests.post(f"{PRODUCT_SERVICE_URL}/test/reset")
    assert response.status_code == 200, "Could not reset Product Service"
    yield


# ─────────────────────────────────────────────
# CONTRACT 1: GET /products/{id} — existing product
# Order Service expects full product shape when product exists.
# ─────────────────────────────────────────────

def test_contract1_get_existing_product_by_id():
    """
    Contract 1:
    GIVEN product ID 1 exists,
    WHEN  Order Service calls GET /products/1,
    THEN  response is 200 with fields: id, name, price, stock
    """
    response = requests.get(f"{PRODUCT_SERVICE_URL}/products/1")

    # Status contract
    assert response.status_code == 200, (
        f"Contract 1 violated: expected 200, got {response.status_code}"
    )

    # Shape contract
    body = response.json()
    validate_contract(body, PRODUCT_CONTRACT)

    # Value contract
    assert body["id"] == 1
    print(f"\n[Contract 1 PASSED] Product: {body['name']} | Price: {body['price']}")


# ─────────────────────────────────────────────
# CONTRACT 2: GET /products/{id} — non-existent product
# Order Service expects 404 with a detail message.
# ─────────────────────────────────────────────

def test_contract2_get_nonexistent_product_returns_404():
    """
    Contract 2:
    GIVEN product ID 999 does NOT exist,
    WHEN  Order Service calls GET /products/999,
    THEN  response is 404 with field: detail
    """
    response = requests.get(f"{PRODUCT_SERVICE_URL}/products/999")

    # Status contract
    assert response.status_code == 404, (
        f"Contract 2 violated: expected 404, got {response.status_code}"
    )

    # Shape contract
    body = response.json()
    validate_contract(body, ERROR_CONTRACT)

    print(f"\n[Contract 2 PASSED] 404 detail: {body['detail']}")


# ─────────────────────────────────────────────
# CONTRACT 3: GET /products/{id} — stock is sufficient
# Order Service checks stock >= requested quantity before placing order.
# ─────────────────────────────────────────────

def test_contract3_product_has_sufficient_stock():
    """
    Contract 3:
    GIVEN product ID 2 exists with stock >= 1,
    WHEN  Order Service calls GET /products/2,
    THEN  response stock field is >= 1
    """
    response = requests.get(f"{PRODUCT_SERVICE_URL}/products/2")

    assert response.status_code == 200
    body = response.json()
    validate_contract(body, PRODUCT_CONTRACT)

    assert body["stock"] >= 1, (
        f"Contract 3 violated: stock {body['stock']} is insufficient"
    )

    print(f"\n[Contract 3 PASSED] Stock available: {body['stock']}")


# ─────────────────────────────────────────────
# CONTRACT 4: GET /products — returns a list
# Order Service expects a non-empty list from the catalog.
# ─────────────────────────────────────────────

def test_contract4_get_all_products_returns_list():
    """
    Contract 4:
    GIVEN products exist in the catalog,
    WHEN  Order Service calls GET /products,
    THEN  response is a non-empty list where each item matches product shape
    """
    response = requests.get(f"{PRODUCT_SERVICE_URL}/products")

    assert response.status_code == 200
    body = response.json()

    assert isinstance(body, list), (
        f"Contract 4 violated: expected list, got {type(body).__name__}"
    )
    assert len(body) >= 1, "Contract 4 violated: product list is empty"

    # Validate shape of each item in the list
    for item in body:
        validate_contract(item, PRODUCT_CONTRACT)

    print(f"\n[Contract 4 PASSED] Total products in catalog: {len(body)}")


# ─────────────────────────────────────────────
# CONTRACT 5: GET /products/{id} — price is positive
# Order Service uses price to compute total_price of an order.
# A zero or negative price would corrupt order calculations.
# ─────────────────────────────────────────────

def test_contract5_product_price_is_positive():
    """
    Contract 5:
    GIVEN product ID 3 exists,
    WHEN  Order Service calls GET /products/3,
    THEN  price field is a positive number (> 0)
    """
    response = requests.get(f"{PRODUCT_SERVICE_URL}/products/3")

    assert response.status_code == 200
    body = response.json()
    validate_contract(body, PRODUCT_CONTRACT)

    assert body["price"] > 0, (
        f"Contract 5 violated: price {body['price']} is not positive"
    )

    print(f"\n[Contract 5 PASSED] Price: {body['price']}")
