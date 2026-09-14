import os
import pytest
import requests

PRODUCT_SERVICE_URL = os.getenv('PRODUCT_SERVICE_URL', 'http://127.0.0.1:5001')

PRODUCT_CONTRACT = {
    'required_fields': ['id', 'sku', 'title', 'description', 'price', 'stock_quantity'],
    'field_types': {
        'id': int,
        'sku': str,
        'title': str,
        'description': str,
        'price': float,
        'stock_quantity': int
    },
    'constraints': {
        'price': lambda v: v > 0,
        'stock_quantity': lambda v: v >= 0
    }
}

ERROR_CONTRACT = {
    'required_fields': ['detail'],
    'field_types': {'detail': str}
}

def validate_contract(body: dict, contract: dict):
    for field in contract['required_fields']:
        assert field in body, f'Contract violation: missing field {field}'
    for field, expected_type in contract['field_types'].items():
        assert isinstance(body[field], expected_type), f'Contract violation: {field} wrong type'
    for field, constraint in contract.get('constraints', {}).items():
        assert constraint(body[field]), f'Contract violation: {field} failed constraint'

@pytest.fixture(autouse=True)
def reset_product_service():
    response = requests.post(f'{PRODUCT_SERVICE_URL}/api/v1/test/reset')
    assert response.status_code == 200
    yield

def test_contract1_get_existing_product_by_id():
    response = requests.get(f'{PRODUCT_SERVICE_URL}/api/v1/products/1')
    assert response.status_code == 200
    body = response.json()
    validate_contract(body, PRODUCT_CONTRACT)
    assert body['id'] == 1
    print(f'\n[Contract 1 PASSED] Product: {body["title"]}')

def test_contract2_get_nonexistent_product_returns_404():
    response = requests.get(f'{PRODUCT_SERVICE_URL}/api/v1/products/999')
    assert response.status_code == 404
    body = response.json()
    validate_contract(body, ERROR_CONTRACT)
    print(f'\n[Contract 2 PASSED] 404 detail: {body["detail"]}')

def test_contract3_product_has_sufficient_stock():
    response = requests.get(f'{PRODUCT_SERVICE_URL}/api/v1/products/2')
    assert response.status_code == 200
    body = response.json()
    validate_contract(body, PRODUCT_CONTRACT)
    assert body['stock_quantity'] >= 1
    print(f'\n[Contract 3 PASSED] Stock available: {body["stock_quantity"]}')

def test_contract4_get_all_products_returns_list():
    response = requests.get(f'{PRODUCT_SERVICE_URL}/api/v1/products')
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert len(body) >= 1
    for item in body:
        validate_contract(item, PRODUCT_CONTRACT)
    print(f'\n[Contract 4 PASSED] Total products: {len(body)}')

def test_contract5_product_price_is_positive():
    response = requests.get(f'{PRODUCT_SERVICE_URL}/api/v1/products/3')
    assert response.status_code == 200
    body = response.json()
    validate_contract(body, PRODUCT_CONTRACT)
    assert body['price'] > 0
    print(f'\n[Contract 5 PASSED] Price: {body["price"]}')
