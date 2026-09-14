import os
import pytest
import requests

PRODUCT_SERVICE_URL = os.getenv('PRODUCT_SERVICE_URL', 'http://127.0.0.1:5001')
ORDER_SERVICE_URL = os.getenv('ORDER_SERVICE_URL', 'http://127.0.0.1:5002')

@pytest.fixture(autouse=True)
def reset_all_services():
    r1 = requests.post(f'{PRODUCT_SERVICE_URL}/api/v1/test/reset')
    r2 = requests.post(f'{ORDER_SERVICE_URL}/api/v1/test/reset')
    assert r1.status_code == 200
    assert r2.status_code == 200
    yield

def test_integration_1_create_new_product():
    payload = {'sku': 'TEST-001', 'title': 'Motorcycle Cover', 'description': 'Premium cover', 'price': 1200.0, 'stock_quantity': 15}
    r = requests.post(f'{PRODUCT_SERVICE_URL}/api/v1/products', json=payload)
    assert r.status_code == 201
    body = r.json()
    assert body['title'] == payload['title']
    assert 'id' in body
    print(f'\n[Test 1 PASSED] Created: id={body["id"]} {body["title"]}')

def test_integration_2_created_product_in_catalog():
    payload = {'sku': 'TEST-002', 'title': 'Oil Filter', 'description': 'Premium', 'price': 450.0, 'stock_quantity': 30}
    r = requests.post(f'{PRODUCT_SERVICE_URL}/api/v1/products', json=payload)
    assert r.status_code == 201
    new_id = r.json()['id']
    catalog = requests.get(f'{PRODUCT_SERVICE_URL}/api/v1/products')
    assert catalog.status_code == 200
    ids = [p['id'] for p in catalog.json()]
    assert new_id in ids
    print(f'\n[Test 2 PASSED] Product id={new_id} in catalog')

def test_integration_3_place_new_order():
    payload = {'product_id': 1, 'quantity': 2, 'shipping_address': '123 Test St'}
    r = requests.post(f'{ORDER_SERVICE_URL}/api/v1/orders', json=payload)
    assert r.status_code == 201
    body = r.json()
    assert body['product_id'] == 1
    assert body['status'] == 'PENDING'
    print(f'\n[Test 3 PASSED] Order placed')

def test_integration_4_place_order_insufficient_stock():
    payload = {'product_id': 2, 'quantity': 999, 'shipping_address': 'Test'}
    r = requests.post(f'{ORDER_SERVICE_URL}/api/v1/orders', json=payload)
    assert r.status_code == 400
    print(f'\n[Test 4 PASSED] Insufficient stock rejected')

def test_integration_5_place_order_nonexistent_product():
    payload = {'product_id': 9999, 'quantity': 1, 'shipping_address': 'Test'}
    r = requests.post(f'{ORDER_SERVICE_URL}/api/v1/orders', json=payload)
    assert r.status_code == 400
    print(f'\n[Test 5 PASSED] Non-existent product rejected')

def test_integration_6_update_existing_order():
    payload = {'product_id': 1, 'quantity': 1, 'shipping_address': 'Test'}
    create_r = requests.post(f'{ORDER_SERVICE_URL}/api/v1/orders', json=payload)
    order_id = create_r.json()['id']
    r = requests.put(f'{ORDER_SERVICE_URL}/api/v1/orders/{order_id}', json={'status': 'SHIPPED'})
    assert r.status_code == 200
    print(f'\n[Test 6 PASSED] Order updated')

def test_integration_7_update_nonexistent_order():
    r = requests.put(f'{ORDER_SERVICE_URL}/api/v1/orders/9999', json={'status': 'CANCELLED'})
    assert r.status_code == 404
    print(f'\n[Test 7 PASSED] Non-existent order rejected')

def test_integration_8_full_order_flow():
    product = requests.post(f'{PRODUCT_SERVICE_URL}/api/v1/products',
        json={'sku': 'TEST-G', 'title': 'Gloves', 'description': 'Test', 'price': 600.0, 'stock_quantity': 20})
    assert product.status_code == 201
    product_id = product.json()['id']
    order = requests.post(f'{ORDER_SERVICE_URL}/api/v1/orders',
        json={'product_id': product_id, 'quantity': 3, 'shipping_address': 'Test'})
    assert order.status_code == 201
    order_id = order.json()['id']
    update = requests.put(f'{ORDER_SERVICE_URL}/api/v1/orders/{order_id}',
        json={'status': 'CONFIRMED'})
    assert update.status_code == 200
    print(f'\n[Test 8 PASSED] Full flow complete')
