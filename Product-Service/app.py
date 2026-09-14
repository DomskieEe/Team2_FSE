from fastapi import FastAPI, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, EmailStr
from typing import Optional, List

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

class Product(BaseModel):
    id: int
    sku: str
    name: str
    category: str
    price: float
    stock: int
    description: str
    image: str

class OrderItem(BaseModel):
    id: str
    name: str
    price: float
    quantity: int

class OrderRequest(BaseModel):
    email: str
    address: str
    items: List[OrderItem]
    total: float

products = [
    {
        "id": 1,
        "sku": "SED-TOY-001",
        "name": "Toyota Vios",
        "category": "Sedan",
        "price": 18000.0,
        "stock": 12,
        "description": "Reliable sedan for everyday driving.",
        "image": "https://images.unsplash.com/photo-1550355291-bbee04a92027?auto=format&fit=crop&w=800&q=80"
    },
    {
        "id": 2,
        "sku": "SPO-YAM-002",
        "name": "Yamaha R15",
        "category": "Sports Bike",
        "price": 3500.0,
        "stock": 4, # Low stock example
        "description": "Lightweight sports motorcycle.",
        "image": "https://images.unsplash.com/photo-1558981806-ec527fa84c39?auto=format&fit=crop&w=800&q=80"
    },
    {
        "id": 3,
        "sku": "SED-HON-003",
        "name": "Honda Civic",
        "category": "Sedan",
        "price": 24000.0,
        "stock": 8, # Low stock example
        "description": "Sleek and powerful compact car.",
        "image": "https://images.unsplash.com/photo-1606664515524-ed2f786a0bd6?auto=format&fit=crop&w=800&q=80"
    },
    {
        "id": 4,
        "sku": "SPO-KAW-004",
        "name": "Kawasaki Ninja 400",
        "category": "Sports Bike",
        "price": 5200.0,
        "stock": 0, # Out of stock example
        "description": "High-performance sport bike built for speed.",
        "image": "https://images.unsplash.com/photo-1558981806-ec527fa84c39?auto=format&fit=crop&w=800&q=80"
    },
    {
        "id": 5,
        "sku": "4X4-JEE-005",
        "name": "Jeep Wrangler Rubicon",
        "category": "4x4",
        "price": 45000.0,
        "stock": 6, # Low stock example
        "description": "Legendary 4x4 capability with removable top and doors.",
        "image": "https://images.unsplash.com/photo-1533473359331-0135ef1b58bf?auto=format&fit=crop&w=800&q=80"
    },
    {
        "id": 6,
        "sku": "4X4-TOY-006",
        "name": "Toyota Land Cruiser",
        "category": "4x4",
        "price": 85000.0,
        "stock": 15,
        "description": "Ultimate full-size luxury 4x4 SUV for extreme terrains.",
        "image": "https://images.unsplash.com/photo-1519641471654-76ce0107ad1b?auto=format&fit=crop&w=800&q=80"
    },
    {
        "id": 7,
        "sku": "NAK-DUC-007",
        "name": "Ducati Monster",
        "category": "Naked Bike",
        "price": 9500.0,
        "stock": 7, # Low stock example
        "description": "Naked bike with aggressive style and power.",
        "image": "https://images.unsplash.com/photo-1558980664-3a031cf67ea8?auto=format&fit=crop&w=800&q=80"
    },
    {
        "id": 8,
        "sku": "ELE-TES-008",
        "name": "Tesla Model 3",
        "category": "Electric",
        "price": 39999.0,
        "stock": 20,
        "description": "All-electric modern sedan with autopilot features.",
        "image": "https://images.unsplash.com/photo-1560958089-b8a1929cea89?auto=format&fit=crop&w=800&q=80"
    },
    {
        "id": 9,
        "sku": "SPO-BMW-009",
        "name": "BMW S1000RR",
        "category": "Sports Bike",
        "price": 17500.0,
        "stock": 3, # Low stock example
        "description": "Track-ready superbike with advanced electronics.",
        "image": "https://images.unsplash.com/photo-1568772585407-9361f9bf3a87?auto=format&fit=crop&w=800&q=80"
    },
    {
        "id": 10,
        "sku": "4X4-FOR-010",
        "name": "Ford Explorer 4x4",
        "category": "4x4",
        "price": 36000.0,
        "stock": 11,
        "description": "Spacious family SUV equipped with intelligent four-wheel drive.",
        "image": "https://images.unsplash.com/photo-1533473359331-0135ef1b58bf?auto=format&fit=crop&w=800&q=80"
    },
    {
        "id": 11,
        "sku": "CRU-HAR-011",
        "name": "Harley-Davidson Iron 883",
        "category": "Cruiser",
        "price": 11200.0,
        "stock": 9, # Low stock example
        "description": "Classic American cruiser with a raw profile.",
        "image": "https://images.unsplash.com/photo-1558981403-c5f9899a28bc?auto=format&fit=crop&w=800&q=80"
    },
    {
        "id": 12,
        "sku": "SPO-SUZ-012",
        "name": "Suzuki Hayabusa",
        "category": "Sports Bike",
        "price": 18500.0,
        "stock": 0, # Out of stock example
        "description": "Legendary hypersport motorcycle built for velocity.",
        "image": "https://images.unsplash.com/photo-1558981359-219d6364c9c8?auto=format&fit=crop&w=800&q=80"
    },
    {
        "id": 13,
        "sku": "SPO-CHE-013",
        "name": "Chevrolet Camaro",
        "category": "Sports Car",
        "price": 35000.0,
        "stock": 14,
        "description": "Iconic muscle car with thrilling track performance.",
        "image": "https://images.unsplash.com/photo-1552519507-da3b142c6e3d?auto=format&fit=crop&w=800&q=80"
    },
    {
        "id": 14,
        "sku": "SCO-VES-014",
        "name": "Vespa Primavera 150",
        "category": "Scooter",
        "price": 4300.0,
        "stock": 25,
        "description": "Stylish urban scooter for easy city commuting.",
        "image": "https://images.unsplash.com/photo-1558981403-c5f9899a28bc?auto=format&fit=crop&w=800&q=80"
    },
    {
        "id": 15,
        "sku": "SPO-POR-015",
        "name": "Porsche 911 Carrera",
        "category": "Sports Car",
        "price": 105000.0,
        "stock": 2, # Low stock example
        "description": "Timeless luxury sports car with breathtaking power.",
        "image": "https://images.unsplash.com/photo-1614162692292-7ac56d7f7f1e?auto=format&fit=crop&w=800&q=80"
    }
]

@app.get("/", response_class=HTMLResponse)
def home(request: Request, category: Optional[str] = None):
    filtered_products = products
    if category and category != "All":
        filtered_products = [
            p for p in filtered_products 
            if p["category"].lower() == category.lower()
        ]
    categories = ["All"] + sorted(list(set(p["category"] for p in products)))
    return templates.TemplateResponse(request, "index.html", {
        "products": filtered_products, 
        "categories": categories,
        "current_category": category or "All"
    })

@app.get("/products")
def get_products(search: Optional[str] = None, category: Optional[str] = None):
    filtered_products = products
    if search:
        q = search.lower()
        filtered_products = [p for p in filtered_products if q in p["name"].lower() or q in p["sku"].lower() or q in p["description"].lower()]
    if category and category != "All":
        filtered_products = [p for p in filtered_products if p["category"].lower() == category.lower()]
    return filtered_products

@app.post("/api/v1/orders", status_code=status.HTTP_201_CREATED)
def create_order(order: OrderRequest):
    return {
        "message": "Order successfully created",
        "order_id": 99281,
        "email": order.email,
        "total": order.total,
        "status": "CREATED"
    }