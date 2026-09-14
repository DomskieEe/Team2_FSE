from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class Order(BaseModel):
    id: int
    vehicle_name: str
    quantity: int
    status: str = "Pending"

orders = [
    {
        "id": 1,
        "vehicle_name": "Toyota Vios",
        "quantity": 1,
        "status": "Pending"
    }
]

@app.get("/orders")
def get_orders():
    return orders

@app.post("/orders")
def create_order(order: Order):
    orders.append(order.dict())
    return order

@app.put("/orders/{order_id}")
def update_order(order_id: int, status: str):
    for order in orders:
        if order["id"] == order_id:
            order["status"] = status
            return order
    raise HTTPException(status_code=404, detail="Order not found")