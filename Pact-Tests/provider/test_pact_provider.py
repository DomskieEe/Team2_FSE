import pytest
import requests

PROVIDER_BASE_URL = 'http://127.0.0.1:5001'

@pytest.fixture(autouse=True)
def reset_provider_state():
    response = requests.post(f'{PROVIDER_BASE_URL}/api/v1/test/reset')
    assert response.status_code == 200
    yield

def test_provider_contract1_get_product_by_id():
    r = requests.get(f'{PROVIDER_BASE_URL}/api/v1/products/1')
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body.get('id'), int)
    assert isinstance(body.get('title'), str)
    assert isinstance(body.get('price'), float)
    assert isinstance(body.get('stock_quantity'), int)
    print(f'[Contract 1 VERIFIED]')

def test_provider_contract2_nonexistent_product_404():
    r = requests.get(f'{PROVIDER_BASE_URL}/api/v1/products/999')
    assert r.status_code == 404
    assert 'detail' in r.json()
    print(f'[Contract 2 VERIFIED]')

def test_provider_contract3_product_has_stock():
    r = requests.get(f'{PROVIDER_BASE_URL}/api/v1/products/2')
    assert r.status_code == 200
    assert r.json()['stock_quantity'] >= 1
    print(f'[Contract 3 VERIFIED]')

def test_provider_contract4_returns_product_list():
    r = requests.get(f'{PROVIDER_BASE_URL}/api/v1/products')
    assert r.status_code == 200
    assert isinstance(r.json(), list)
    assert len(r.json()) >= 1
    print(f'[Contract 4 VERIFIED]')

def test_provider_contract5_price_is_positive():
    r = requests.get(f'{PROVIDER_BASE_URL}/api/v1/products/3')
    assert r.status_code == 200
    assert r.json()['price'] > 0
    print(f'[Contract 5 VERIFIED]')

def test_provider_fulfills_all_contracts():
    results = {}
    r = requests.get(f'{PROVIDER_BASE_URL}/api/v1/products/1')
    results['c1'] = r.status_code == 200
    r = requests.get(f'{PROVIDER_BASE_URL}/api/v1/products/999')
    results['c2'] = r.status_code == 404
    r = requests.get(f'{PROVIDER_BASE_URL}/api/v1/products/2')
    results['c3'] = r.status_code == 200
    r = requests.get(f'{PROVIDER_BASE_URL}/api/v1/products')
    results['c4'] = r.status_code == 200
    r = requests.get(f'{PROVIDER_BASE_URL}/api/v1/products/3')
    results['c5'] = r.status_code == 200
    assert all(results.values())
    print('[All contracts PASSED]')
