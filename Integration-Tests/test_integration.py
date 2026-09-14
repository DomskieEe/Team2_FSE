import os
import pytest
import requests

PRODUCT_SERVICE_URL = os.getenv("PRODUCT_SERVICE_URL", "http://127.0.0.1:5001")
ORDER_SERVICE_URL   = os.getenv("ORDER_SERVICE_URL",   "http://127.0.0.1:5002")


@pytest.fixture(autouse=True)
def reset_all_services():
    """TDM: Reset both services to seed state before each test."""
    r1 = requests.post(f"{PRODUCT_SERVICE_URL}/test/reset")
    r2 = requests.post(f"{ORDER_SERVICE_URL}/test/reset")
    assert r1.status_code == 200, "Could not reset Product Service"
    assert r2.status_code == 200, "Could not reset Order Service"
    yield


def test_integration_1_create_new_product():
    payload = {"name": "Motorcycle Cover Waterproof", "price": 1200.0, "stock": 15}
    r = requests.post(f"{PRODUCT_SERVICE_URL}/products", json=payload)
    assert r.status_code == 201
    body = r.json()
    assert body["name"] == payload["name"]
    assert body["price"] == payload["price"]
    assert body["stock"] == payload["stock"]
    assert "id" in body
    print(f"\n[Test 1 PASSED] Created: id={body['id']} {body['name']}")


def test_integration_2_created_product_in_catalog():
    payload = {"name": "Oil Filter Premium", "price": 450.0, "stock": 30}
    r = requests.post(f"{PRODUCT_SERVICE_URL}/products", json=payload)
    assert r.status_code == 201
    new_id = r.json()["id"]
    catalog = requests.get(f"{PRODUCT_SERVICE_URL}/products")
    assert catalog.status_code == 200
    ids = [p["id"] for p in catalog.json()]
    assert new_id in ids
    print(f"\n[Test 2 PASSED] Product id={new_id} found in catalog")


def test_integration_3_place_new_order():
    payload = {"product_id": 1, "quantity": 2}
    r = requests.post(f"{ORDER_SERVICE_URL}/orders", json=payload)
    assert r.status_code == 201
    body = r.json()
    assert body["product_id"] == 1
    assert body["quantity"] == 2
    assert body["status"] == "PENDING"
    assert body["total_price"] == 9000.0
    assert "order_id" in body
    print(f"\n[Test 3 PASSED] Order placed: id={body['order_id']} total={body['total_price']}")


def test_integration_4_place_order_insufficient_stock():
    payload = {"product_id": 2, "quantity": 999}
    r = requests.post(f"{ORDER_SERVICE_URL}/orders", json=payload)
    assert r.status_code == 400
    assert "detail" in r.json()
    print(f"\n[Test 4 PASSED] Insufficient stock rejected correctly")


def test_integration_5_place_order_nonexistent_product():
    payload = {"product_id": 9999, "quantity": 1}
    r = requests.post(f"{ORDER_SERVICE_URL}/orders", json=payload)
    assert r.status_code == 404
    assert "detail" in r.json()
    print(f"\n[Test 5 PASSED] Non-existent product rejected with 404")


def test_integration_6_update_existing_order():
    r = requests.put(f"{ORDER_SERVICE_URL}/orders/101", json={"status": "SHIPPED"})
    assert r.status_code == 200
    body = r.json()
    assert body["order_id"] == 101
    assert body["status"] == "SHIPPED"
    print(f"\n[Test 6 PASSED] Order 101 updated to SHIPPED")


def test_integration_7_update_nonexistent_order():
    r = requests.put(f"{ORDER_SERVICE_URL}/orders/9999", json={"status": "CANCELLED"})
    assert r.status_code == 404
    assert "detail" in r.json()
    print(f"\n[Test 7 PASSED] Non-existent order update rejected with 404")


def test_integration_8_full_order_flow():
    """End-to-end: create product, place order, update order status."""
    # Step 1 - Create product
    product = requests.post(f"{PRODUCT_SERVICE_URL}/products",
        json={"name": "Test Gloves", "price": 600.0, "stock": 20})
    assert product.status_code == 201
    product_id = product.json()["id"]

    # Step 2 - Place order using the new product
    order = requests.post(f"{ORDER_SERVICE_URL}/orders",
        json={"product_id": product_id, "quantity": 3})
    assert order.status_code == 201
    order_body = order.json()
    assert order_body["status"] == "PENDING"
    assert order_body["total_price"] == 1800.0
    order_id = order_body["order_id"]

    # Step 3 - Update order to CONFIRMED
    update = requests.put(f"{ORDER_SERVICE_URL}/orders/{order_id}",
        json={"status": "CONFIRMED"})
    assert update.status_code == 200
    assert update.json()["status"] == "CONFIRMED"

    print(f"\n[Test 8 PASSED] Full flow: product={product_id} order={order_id} status=CONFIRMED")
