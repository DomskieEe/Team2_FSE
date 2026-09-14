# Order-Service/app.py
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
import requests

app = FastAPI(
    title="Order Service API",
    description="Microservice for handling order placement and lifecycle updates",
    version="1.0.0"
)

# Configuration: URL ng Product Service
PRODUCT_SERVICE_URL = "http://127.0.0.1:5001/products"

# Pydantic Schemas (Contracts para sa Broker!)
class OrderCreate(BaseModel):
    product_id: int
    quantity: int

class OrderUpdate(BaseModel):
    status: str  # e.g., 'CONFIRMED', 'SHIPPED', 'CANCELLED'

class Order(BaseModel):
    order_id: int
    product_id: int
    product_name: str
    quantity: int
    total_price: float
    status: str

# In-Memory Database para sa Orders
orders_db: List[dict] = [
    {
        "order_id": 101,
        "product_id": 1,
        "product_name": "Gixxer 155 Full Face Helmet",
        "quantity": 1,
        "total_price": 4500.0,
        "status": "CONFIRMED"
    }
]

@app.get("/orders", response_model=List[Order])
def get_all_orders():
    """Retrieve all placed orders"""
    return orders_db

@app.get("/orders/{order_id}", response_model=Order)
def get_order(order_id: int):
    """Retrieve specific order details by ID"""
    order = next((o for o in orders_db if o["order_id"] == order_id), None)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@app.post("/orders", response_model=Order, status_code=status.HTTP_201_CREATED)
def place_order(order_req: OrderCreate):
    """Scenario 2: Place a new order (With Inter-Service Communication!)"""
    if order_req.quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be greater than zero")

    # 🔗 INTER-SERVICE COMMUNICATION: Tawagin si Product Service sa Port 5001
    try:
        response = requests.get(f"{PRODUCT_SERVICE_URL}/{order_req.product_id}", timeout=5)
    except requests.exceptions.RequestException:
        raise HTTPException(
            status_code=503, 
            detail="Product Service is currently unreachable"
        )

    if response.status_code == 404:
        raise HTTPException(status_code=404, detail="Product does not exist")
    elif response.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to fetch product details")

    product_data = response.json()

    # Tsek kung sapat ang stock
    if product_data["stock"] < order_req.quantity:
        raise HTTPException(
            status_code=400, 
            detail=f"Insufficient stock. Only {product_data['stock']} items available"
        )

    # I-calculate ang total price gamit ang verified price mula sa Product Service
    total = product_data["price"] * order_req.quantity
    new_order_id = 100 + len(orders_db) + 1

    new_order = {
        "order_id": new_order_id,
        "product_id": product_data["id"],
        "product_name": product_data["name"],
        "quantity": order_req.quantity,
        "total_price": total,
        "status": "PENDING"
    }

    orders_db.append(new_order)
    return new_order

@app.put("/orders/{order_id}", response_model=Order)
def update_order_status(order_id: int, update_req: OrderUpdate):
    """Scenario 3: Update an existing order"""
    order = next((o for o in orders_db if o["order_id"] == order_id), None)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order["status"] = update_req.status.upper()
    return order

# Task 3: Test Data Management (Reset Endpoint)
@app.post("/test/reset")
def reset_orders():
    global orders_db
    orders_db = [
        {
            "order_id": 101,
            "product_id": 1,
            "product_name": "Gixxer 155 Full Face Helmet",
            "quantity": 1,
            "total_price": 4500.0,
            "status": "CONFIRMED"
        }
    ]
    return {"message": "Order test data reset successfully"}

if __name__ == "__main__":
    import uvicorn
    print("🚀 [Order Service] Starting on http://127.0.0.1:5002")
    uvicorn.run("app:app", host="0.0.0.0", port=5002, reload=True)