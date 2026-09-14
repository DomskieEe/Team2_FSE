# Product-Service/app.py
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import List

app = FastAPI(
    title="Product Service API",
    description="Microservice for managing product inventory and details",
    version="1.0.0"
)

# Pydantic Schemas (Ito ang magsisilbing Contract para sa Broker!)
class ProductCreate(BaseModel):
    name: str
    price: float
    stock: int

class Product(BaseModel):
    id: int
    name: str
    price: float
    stock: int

# In-Memory Database
products_db: List[dict] = [
    {"id": 1, "name": "Gixxer 155 Full Face Helmet", "price": 4500.0, "stock": 10},
    {"id": 2, "name": "Riding Armored Jacket", "price": 3200.0, "stock": 5},
    {"id": 3, "name": "Brembo Brake Pads", "price": 850.0, "stock": 25}
]

@app.get("/products", response_model=List[Product])
def get_all_products():
    """Retrieve all available products"""
    return products_db

@app.get("/products/{product_id}", response_model=Product)
def get_product(product_id: int):
    """Retrieve product details by ID (Used by Order Service)"""
    product = next((p for p in products_db if p["id"] == product_id), None)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@app.post("/products", response_model=Product, status_code=status.HTTP_201_CREATED)
def create_product(product: ProductCreate):
    """Scenario 1: Create a new product"""
    new_id = len(products_db) + 1
    new_item = {
        "id": new_id,
        "name": product.name,
        "price": product.price,
        "stock": product.stock
    }
    products_db.append(new_item)
    return new_item

# Task 3: Test Data Management (Reset Endpoint)
@app.post("/test/reset")
def reset_products():
    global products_db
    products_db = [
        {"id": 1, "name": "Gixxer 155 Full Face Helmet", "price": 4500.0, "stock": 10},
        {"id": 2, "name": "Riding Armored Jacket", "price": 3200.0, "stock": 5},
        {"id": 3, "name": "Brembo Brake Pads", "price": 850.0, "stock": 25}
    ]
    return {"message": "Product test data reset successfully"}

if __name__ == "__main__":
    import uvicorn
    print("🚀 [Product Service] Starting on http://127.0.0.1:5001")
    uvicorn.run("app:app", host="0.0.0.0", port=5001, reload=True)