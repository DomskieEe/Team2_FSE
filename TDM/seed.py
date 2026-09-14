# TDM/seed.py
# TDM Seeding Engine
#
# This script seeds both Product Service and Order Service
# with fixture data defined in fixtures/products.json.
# It runs as a Docker container (tdm-seeder) after services are healthy.
#
# It also exposes reset functions used by integration tests
# to restore clean state between test runs.

import json
import os
import time
import requests

PRODUCT_SERVICE_URL = os.getenv("PRODUCT_SERVICE_URL", "http://127.0.0.1:5001")
ORDER_SERVICE_URL   = os.getenv("ORDER_SERVICE_URL",   "http://127.0.0.1:5002")

FIXTURES_PATH = os.path.join(os.path.dirname(__file__), "fixtures", "products.json")


def wait_for_service(url: str, name: str, retries: int = 10, delay: int = 2):
    """Wait until a service is reachable."""
    for attempt in range(retries):
        try:
            r = requests.get(url, timeout=3)
            if r.status_code < 500:
                print(f"[TDM] {name} is ready.")
                return True
        except requests.exceptions.RequestException:
            pass
        print(f"[TDM] Waiting for {name}... attempt {attempt + 1}/{retries}")
        time.sleep(delay)
    raise RuntimeError(f"[TDM] {name} did not become ready after {retries} attempts.")


def reset_services():
    """Reset both services to clean state."""
    print("[TDM] Resetting services...")
    r1 = requests.post(f"{PRODUCT_SERVICE_URL}/test/reset")
    r2 = requests.post(f"{ORDER_SERVICE_URL}/test/reset")
    assert r1.status_code == 200, "Failed to reset Product Service"
    assert r2.status_code == 200, "Failed to reset Order Service"
    print("[TDM] Both services reset to seed state.")


def seed_products():
    """Seed Product Service with fixture data from products.json."""
    with open(FIXTURES_PATH, "r") as f:
        products = json.load(f)

    print(f"[TDM] Seeding {len(products)} products into Product Service...")

    # Reset first for clean slate
    requests.post(f"{PRODUCT_SERVICE_URL}/test/reset")

    seeded = []
    for product in products:
        response = requests.post(
            f"{PRODUCT_SERVICE_URL}/products",
            json=product,
            timeout=5
        )
        if response.status_code == 201:
            seeded.append(response.json())
            print(f"  [OK] Seeded: {product['name']} (price: {product['price']}, stock: {product['stock']})")
        else:
            print(f"  [WARN] Failed to seed: {product['name']} — {response.status_code}")

    print(f"[TDM] Seeding complete. {len(seeded)} products seeded.")
    return seeded


def verify_seed():
    """Verify that seeded data is accessible."""
    response = requests.get(f"{PRODUCT_SERVICE_URL}/products")
    assert response.status_code == 200, "Cannot verify seed — Product Service not responding"
    products = response.json()
    print(f"[TDM] Verification: {len(products)} products in catalog.")
    for p in products:
        print(f"  id:{p['id']} | {p['name']} | price:{p['price']} | stock:{p['stock']}")


if __name__ == "__main__":
    print("[TDM] Starting TDM Seeding Engine...")

    wait_for_service(f"{PRODUCT_SERVICE_URL}/products", "Product Service")
    wait_for_service(f"{ORDER_SERVICE_URL}/orders",     "Order Service")

    seed_products()
    verify_seed()

    print("[TDM] Seeding Engine completed successfully.")
