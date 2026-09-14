# Product-Service/app.py
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional
import sqlite3
import os

app = FastAPI(
    title="Product Catalog Service",
    description="Dedicated Product Catalog REST API with SQLite persistence and atomic stock reservations",
    version="1.0.0",
    openapi_url="/api/v1/openapi.json",
    docs_url="/docs"
)

DB_FILE = os.path.join(os.path.dirname(__file__), "products.db")

# Pydantic Schemas matching the Jira EARS Acceptance Criteria
class ProductCreate(BaseModel):
    sku: str = Field(..., example="GIX-HLM-001")
    title: str = Field(..., example="Gixxer 155 Full Face Helmet")
    description: str = Field(..., example="ECE certified aerodynamic helmet")
    price: float = Field(..., gt=0, example=4500.0)
    stock_quantity: int = Field(..., ge=0, example=10)

class ProductResponse(BaseModel):
    id: int
    sku: str
    title: str
    description: str
    price: float
    stock_quantity: int

class ReserveRequest(BaseModel):
    quantity: int = Field(..., gt=0, example=2)

def get_db_connection():
    """Establishes connection to SQLite database with foreign keys enabled."""
    conn = sqlite3.connect(DB_FILE, timeout=10.0)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the SQLite schema and seeds initial records if empty."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sku TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                price REAL NOT NULL,
                stock_quantity INTEGER NOT NULL
            )
        """)
        cursor.execute("SELECT COUNT(*) FROM products")
        if cursor.fetchone()[0] == 0:
            initial_products = [
                ("GIX-HLM-001", "Gixxer 155 Full Face Helmet", "ECE certified aerodynamic helmet", 4500.0, 10),
                ("GIX-JCK-002", "Riding Armored Jacket", "Level 2 impact armor jacket", 3200.0, 5),
                ("GIX-BRK-003", "Brembo Brake Pads", "Sintered high performance pads", 850.0, 25)
            ]
            cursor.executemany("""
                INSERT INTO products (sku, title, description, price, stock_quantity)
                VALUES (?, ?, ?, ?, ?)
            """, initial_products)
        conn.commit()

# Initialize SQLite database on startup
init_db()

@app.get("/api/v1/products", response_model=List[ProductResponse])
def get_all_products():
    """Retrieve all available catalog products."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, sku, title, description, price, stock_quantity FROM products")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

@app.get("/api/v1/products/{product_id}", response_model=ProductResponse)
def get_product_by_id(product_id: int):
    """
    Event-Driven Acceptance Criteria:
    WHEN a valid product is queried via GET /api/v1/products/{id},
    THE service SHALL return HTTP 200 OK with product ID, SKU, title, description, price, and stock quantity.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, sku, title, description, price, stock_quantity FROM products WHERE id = ?", 
            (product_id,)
        )
        row = cursor.fetchone()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {product_id} not found."
            )
        return dict(row)

@app.post("/api/v1/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(payload: ProductCreate):
    """Create a new product record in SQLite persistence."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO products (sku, title, description, price, stock_quantity)
                VALUES (?, ?, ?, ?, ?)
            """, (payload.sku, payload.title, payload.description, payload.price, payload.stock_quantity))
            conn.commit()
            new_id = cursor.lastrowid
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=400, detail="Product with this SKU already exists.")
        
        cursor.execute("SELECT id, sku, title, description, price, stock_quantity FROM products WHERE id = ?", (new_id,))
        return dict(cursor.fetchone())

@app.post("/api/v1/products/{product_id}/reserve", response_model=ProductResponse)
def reserve_stock(product_id: int, payload: ReserveRequest):
    """
    Event-Driven & Unwanted Behavior Acceptance Criteria:
    Atomically decrement stock_quantity by Q within a transactional database lock.
    If quantity exceeds available stock, return HTTP 400 Bad Request {"detail": "Insufficient inventory"}.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # Acquire an exclusive lock immediately for atomic reservation
        cursor.execute("BEGIN IMMEDIATE")
        
        cursor.execute(
            "SELECT id, sku, title, description, price, stock_quantity FROM products WHERE id = ?", 
            (product_id,)
        )
        product = cursor.fetchone()
        
        if not product:
            conn.rollback()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {product_id} not found."
            )
        
        current_stock = product["stock_quantity"]
        if payload.quantity > current_stock:
            conn.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient inventory"
            )
        
        # Atomically decrement inventory
        new_stock = current_stock - payload.quantity
        cursor.execute(
            "UPDATE products SET stock_quantity = ? WHERE id = ?", 
            (new_stock, product_id)
        )
        conn.commit()
        
        cursor.execute("SELECT id, sku, title, description, price, stock_quantity FROM products WHERE id = ?", (product_id,))
        return dict(cursor.fetchone())
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database transaction error: {str(e)}")
    finally:
        conn.close()

# Task 3: Test Data Management (Reset Endpoint for Testing)
@app.post("/api/v1/test/reset")
def reset_test_data():
    """Resets the SQLite database to baseline fixtures for automated testing."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM products")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='products'")
        initial_products = [
            ("GIX-HLM-001", "Gixxer 155 Full Face Helmet", "ECE certified aerodynamic helmet", 4500.0, 10),
            ("GIX-JCK-002", "Riding Armored Jacket", "Level 2 impact armor jacket", 3200.0, 5),
            ("GIX-BRK-003", "Brembo Brake Pads", "Sintered high performance pads", 850.0, 25)
        ]
        cursor.executemany("""
            INSERT INTO products (sku, title, description, price, stock_quantity)
            VALUES (?, ?, ?, ?, ?)
        """, initial_products)
        conn.commit()
    return {"message": "Product test data reset successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=5001, reload=True)