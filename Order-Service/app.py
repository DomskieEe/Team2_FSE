# Order-Service/app.py
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional
import httpx
import sqlite3
import os
from datetime import datetime

app = FastAPI(
    title="Order Processing Service",
    description="Microservice with inter-service HTTP communication to Product Service for staged, transactional order fulfillment",
    version="1.0.0",
    openapi_url="/api/v1/openapi.json",
    docs_url="/docs"
)

DB_FILE = os.path.join(os.path.dirname(__file__), "orders.db")
_PRODUCT_BASE = os.getenv("PRODUCT_SERVICE_URL", "http://127.0.0.1:5001")
PRODUCT_SERVICE_BASE_URL = f"{_PRODUCT_BASE}/api/v1/products"

# Pydantic Schemas matching the Jira EARS Acceptance Criteria
class OrderCreate(BaseModel):
    product_id: int = Field(..., example=1)
    quantity: int = Field(..., gt=0, example=2)
    shipping_address: str = Field(..., example="123 Acacia Ave, Ayala Alabang, Muntinlupa")

class OrderUpdate(BaseModel):
    shipping_address: Optional[str] = Field(None, example="456 Makati Ave, Bel-Air, Makati")
    status: Optional[str] = Field(None, example="CONFIRMED")  # Allowed: CONFIRMED, SHIPPED, CANCELLED

class OrderResponse(BaseModel):
    id: int
    product_id: int
    product_title: str
    quantity: int
    total_price: float
    shipping_address: str
    status: str
    created_at: str

def get_db_connection():
    """Establishes connection to SQLite database."""
    conn = sqlite3.connect(DB_FILE, timeout=10.0)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the SQLite schema for order persistence."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                product_title TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                total_price REAL NOT NULL,
                shipping_address TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        conn.commit()

# Initialize SQLite database on startup
init_db()

@app.get("/api/v1/orders", response_model=List[OrderResponse])
def get_all_orders():
    """Retrieve all staged and fulfilled customer orders."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, product_id, product_title, quantity, total_price, shipping_address, status, created_at FROM orders")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

@app.get("/api/v1/orders/{order_id}", response_model=OrderResponse)
def get_order_by_id(order_id: int):
    """Retrieve specific order details by ID."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, product_id, product_title, quantity, total_price, shipping_address, status, created_at FROM orders WHERE id = ?", 
            (order_id,)
        )
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"Order with ID {order_id} not found.")
        return dict(row)

@app.post("/api/v1/orders", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def place_order(payload: OrderCreate):
    """
    Event-Driven & Unwanted Behavior Acceptance Criteria:
    Communicates with Product Catalog Service via asynchronous HTTP client (httpx.AsyncClient).
    Requests stock reservations, persists order record with initial status PENDING, and returns HTTP 201 Created.
    If product ID is invalid or stock is insufficient, aborts transaction and returns HTTP 400 Bad Request.
    """
    async with httpx.AsyncClient(timeout=5.0) as client:
        # Step 1: Verify product existence
        try:
            prod_res = await client.get(f"{PRODUCT_SERVICE_BASE_URL}/{payload.product_id}")
        except httpx.RequestError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Product Catalog Service is currently unavailable."
            )
        
        if prod_res.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid order: Product with ID {payload.product_id} does not exist."
            )
        elif prod_res.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to query Product Catalog Service."
            )
        
        product_info = prod_res.json()

        # Step 2: Request atomic stock reservation
        try:
            reserve_res = await client.post(
                f"{PRODUCT_SERVICE_BASE_URL}/{payload.product_id}/reserve",
                json={"quantity": payload.quantity}
            )
        except httpx.RequestError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Failed to communicate with Product Reservation endpoint."
            )
        
        # Unwanted Behavior: abort transaction if inventory cannot be reserved
        if reserve_res.status_code == 400:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order placement aborted: Insufficient inventory."
            )
        elif reserve_res.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Stock reservation failed. Transaction aborted."
            )
        
        # Calculate total price
        total_amount = product_info["price"] * payload.quantity
        created_timestamp = datetime.utcnow().isoformat()

        # Step 3: Persist order record in SQLite with status PENDING
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO orders (product_id, product_title, quantity, total_price, shipping_address, status, created_at)
                VALUES (?, ?, ?, ?, ?, 'PENDING', ?)
            """, (payload.product_id, product_info["title"], payload.quantity, total_amount, payload.shipping_address, created_timestamp))
            conn.commit()
            new_order_id = cursor.lastrowid

            cursor.execute(
                "SELECT id, product_id, product_title, quantity, total_price, shipping_address, status, created_at FROM orders WHERE id = ?", 
                (new_order_id,)
            )
            return dict(cursor.fetchone())

@app.put("/api/v1/orders/{order_id}", response_model=OrderResponse)
def update_order(order_id: int, payload: OrderUpdate):
    """
    State-Driven Acceptance Criteria:
    WHILE an order is in PENDING or CONFIRMED status, PUT /api/v1/orders/{id}
    SHALL allow modifying the shipping destination address or transitioning status to CONFIRMED, SHIPPED, or CANCELLED.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
        order = cursor.fetchone()
        
        if not order:
            raise HTTPException(status_code=404, detail=f"Order with ID {order_id} not found.")
        
        current_status = order["status"]
        
        # Enforce State-Driven Rule: Must be PENDING or CONFIRMED to allow updates
        if current_status not in ["PENDING", "CONFIRMED"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Order cannot be modified. Current status is '{current_status}'. Modifications only permitted in PENDING or CONFIRMED states."
            )
        
        new_address = payload.shipping_address if payload.shipping_address is not None else order["shipping_address"]
        new_status = current_status
        
        if payload.status is not None:
            normalized_status = payload.status.upper()
            allowed_transitions = ["CONFIRMED", "SHIPPED", "CANCELLED"]
            if normalized_status not in allowed_transitions:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid target status '{payload.status}'. Permitted transitions: {allowed_transitions}"
                )
            new_status = normalized_status

        cursor.execute("""
            UPDATE orders 
            SET shipping_address = ?, status = ? 
            WHERE id = ?
        """, (new_address, new_status, order_id))
        conn.commit()

        cursor.execute("SELECT id, product_id, product_title, quantity, total_price, shipping_address, status, created_at FROM orders WHERE id = ?", (order_id,))
        return dict(cursor.fetchone())

# Task 3: Test Data Management (Reset Endpoint for Testing)
@app.post("/api/v1/test/reset")
def reset_test_data():
    """Clears all staged orders to restore clean test state."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM orders")
        conn.commit()
    return {"message": "Order test data reset successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=5002, reload=True)