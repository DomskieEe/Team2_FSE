# Pact-Tests/provider/test_pact_provider.py
#
# CONTRACT TESTING — PROVIDER VERIFICATION SIDE
# Provider = Product Service (must fulfill the contracts)
# Consumer = Order Service (defined the contracts)
#
# These tests verify that Product Service actually fulfills
# every contract that Order Service depends on.
#
# HOW TO RUN:
#   1. Start Product Service: cd ../../Product-Service && python app.py
#   2. Run: pytest provider/test_pact_provider.py -v

import pytest
import requests

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────

PROVIDER_BASE_URL = "http://127.0.0.1:5001"


# ─────────────────────────────────────────────
# PROVIDER STATE SETUP
# ─────────────────────────────────────────────

@pytest.fixture(autouse=True)
def reset_provider_state():
    """Resets Product Service to known seed state before each verification."""
    response = requests.post(f"{PROVIDER_BASE_URL}/test/reset")
    assert response.status_code == 200, "Failed to reset provider state"
    print("\n[Provider State] Reset to seed data")
    yield


# ─────────────────────────────────────────────
# PROVIDER VERIFICATION: Contract 1
# Provider must return full product shape for GET /products/{id}
# ─────────────────────────────────────────────

def test_provider_fulfills_contract1_get_product_by_id():
    """
    Verifies Contract 1:
    Provider returns 200 + {id, name, price, stock} for GET /products/1
    """
    response = requests.get(f"{PROVIDER_BASE_URL}/products/1")

    assert response.status_code == 200
    body = response.json()

    # Verify all required fields exist with correct types
    assert isinstance(body.get("id"),    int),   "Field 'id' must be int"
    assert isinstance(body.get("name"),  str),   "Field 'name' must be str"
    assert isinstance(body.get("price"), float), "Field 'price' must be float"
    assert isinstance(body.get("stock"), int),   "Field 'stock' must be int"

    # Verify correct product was returned
    assert body["id"] == 1
    assert body["name"] == "Gixxer 155 Full Face Helmet"
    assert body["price"] == 4500.0
    assert body["stock"] == 10

    print(f"[Contract 1 VERIFIED] {body['name']} — price: {body['price']}, stock: {body['stock']}")


# ─────────────────────────────────────────────
# PROVIDER VERIFICATION: Contract 2
# Provider must return 404 + detail for non-existent product
# ─────────────────────────────────────────────

def test_provider_fulfills_contract2_nonexistent_product_404():
    """
    Verifies Contract 2:
    Provider returns 404 + {detail} for GET /products/999
    """
    response = requests.get(f"{PROVIDER_BASE_URL}/products/999")

    assert response.status_code == 404
    body = response.json()

    assert "detail" in body, "Field 'detail' must exist in 404 response"
    assert isinstance(body["detail"], str), "Field 'detail' must be a string"

    print(f"[Contract 2 VERIFIED] 404 response detail: '{body['detail']}'")


# ─────────────────────────────────────────────
# PROVIDER VERIFICATION: Contract 3
# Provider must return stock >= 1 for product 2
# ─────────────────────────────────────────────

def test_provider_fulfills_contract3_product_has_stock():
    """
    Verifies Contract 3:
    Provider returns stock >= 1 for GET /products/2
    """
    response = requests.get(f"{PROVIDER_BASE_URL}/products/2")

    assert response.status_code == 200
    body = response.json()

    assert body["id"] == 2
    assert body["stock"] >= 1, f"Contract 3 violated: stock is {body['stock']}"

    print(f"[Contract 3 VERIFIED] Product 2 stock: {body['stock']}")


# ─────────────────────────────────────────────
# PROVIDER VERIFICATION: Contract 4
# Provider must return a non-empty list for GET /products
# ─────────────────────────────────────────────

def test_provider_fulfills_contract4_returns_product_list():
    """
    Verifies Contract 4:
    Provider returns a non-empty list for GET /products
    """
    response = requests.get(f"{PROVIDER_BASE_URL}/products")

    assert response.status_code == 200
    body = response.json()

    assert isinstance(body, list), f"Expected list, got {type(body).__name__}"
    assert len(body) >= 1, "Product list must not be empty"

    # Each item must have the required fields
    for item in body:
        assert "id"    in item
        assert "name"  in item
        assert "price" in item
        assert "stock" in item

    print(f"[Contract 4 VERIFIED] Catalog has {len(body)} products")


# ─────────────────────────────────────────────
# PROVIDER VERIFICATION: Contract 5
# Provider must return price > 0 for product 3
# ─────────────────────────────────────────────

def test_provider_fulfills_contract5_price_is_positive():
    """
    Verifies Contract 5:
    Provider returns price > 0 for GET /products/3
    """
    response = requests.get(f"{PROVIDER_BASE_URL}/products/3")

    assert response.status_code == 200
    body = response.json()

    assert body["price"] > 0, f"Contract 5 violated: price is {body['price']}"

    print(f"[Contract 5 VERIFIED] Product 3 price: {body['price']}")


# ─────────────────────────────────────────────
# FULL CONTRACT SUMMARY VERIFICATION
# Runs all 5 contract checks in one test for a quick pass/fail summary
# ─────────────────────────────────────────────

def test_provider_fulfills_all_contracts():
    """
    Summary test: verifies ALL 5 contracts in one pass.
    If this passes, Product Service fully honors the Order Service contract.
    """
    results = {}

    # Contract 1
    r = requests.get(f"{PROVIDER_BASE_URL}/products/1")
    results["contract1"] = r.status_code == 200 and all(
        f in r.json() for f in ["id", "name", "price", "stock"]
    )

    # Contract 2
    r = requests.get(f"{PROVIDER_BASE_URL}/products/999")
    results["contract2"] = r.status_code == 404 and "detail" in r.json()

    # Contract 3
    r = requests.get(f"{PROVIDER_BASE_URL}/products/2")
    results["contract3"] = r.status_code == 200 and r.json().get("stock", 0) >= 1

    # Contract 4
    r = requests.get(f"{PROVIDER_BASE_URL}/products")
    results["contract4"] = r.status_code == 200 and isinstance(r.json(), list)

    # Contract 5
    r = requests.get(f"{PROVIDER_BASE_URL}/products/3")
    results["contract5"] = r.status_code == 200 and r.json().get("price", 0) > 0

    print("\n── Contract Verification Summary ──")
    for contract, passed in results.items():
        status = "PASSED" if passed else "FAILED"
        print(f"  {contract}: {status}")

    assert all(results.values()), (
        f"Some contracts FAILED: "
        f"{[k for k, v in results.items() if not v]}"
    )

    print("── All contracts PASSED ──")
