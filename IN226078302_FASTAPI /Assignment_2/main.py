from unicodedata import category
from typing  import Optional
from pydantic import BaseModel, Field
from typing import List
from fastapi import FastAPI, Query
app = FastAPI()     # app is a variable or object of fastapi class

products = [
    {"id": 1, "name": "Wireless Mouse", "price": 499, "category": "Electronics", "in_stock": True},
    {"id": 2, "name": "Notebook",        "price": 99, "category": "Stationery", "in_stock": True},
    {"id": 3, "name": "USB Hub",        "price": 799, "category": "Electronics", "in_stock": False},
    {"id": 4, "name": "Pen Set",         "price": 49, "category": "Stationery", "in_stock": True},
    {"id":5, "name": "Laptop Stand", "price": 1299, "category": "Electronics", "in_stock": True},
    {"id":6, "name": "Mechanical Keyboard", "price": 2499, "category": "Electronics", "in_stock": True},
    {"id":7, "name": "Webcam", "price": 1899, "category": "Electronics", "in_stock": False}
]

feedback = []
orders = []

class CustomerFeedback(BaseModel):
    customer_name: str = Field(..., min_length=2, max_length=100)
    product_id: int = Field(..., gt=0)
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=500)

class OrderItem(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0, le=50)

class BulkOrder(BaseModel):
    company_name: str = Field(..., min_length=2)
    contact_email: str = Field(None, min_length=5)
    items: List[OrderItem] = Field(..., min_items=1)

#----------End point 0----------------home page----------------------
@app.get("/")       #Home / route url
def home():
    return {"message": "Welcome to our app"}

#----------End point 1----------------get all products----------------------
@app.get("/products")       #products / route url
def get_products():
    return {'products': products, 'total': len(products)}

#----------End point 3----------------get products by category----------------------
@app.get("/products/filter")       #products / route url
def get_products_by_category(category_name: str = Query(None), 
                             min_price: int = Query(None, description='Minimum price'),
                             max_price:int = Query(None, description='Maximum price')):
    if category_name:
        result = [p for p in products if p['category'].lower() == category_name.lower()]
    else:
        result = products
    if min_price is not None:
        result = [p for p in result if p['price'] >= min_price]
    if max_price is not None:
        result = [p for p in result if p['price'] <= max_price]
    if not result:
        return {"message": f"No products found in category '{category_name}'"}
    
    return {"filters": {"Category": category_name, 
                        "min_price": min_price, 
                        "max_price": max_price},

            "products": result,
            "total": len(result)}

#----------End point 4----------------get products in stock----------------------
@app.get("/products/instock")       #products / route url
def get_products_in_stock():
    product_instock = [p for p in products if p["in_stock"] == True]

    if not product_instock:
        return {"message": "No Products in stock"}
    
    return {"Products_in_stock": product_instock, 
            "count": len(product_instock)}

#----------End point 5----------------store info----------------------
@app.get("/store/summary")
def get_store_summary():
    total_products = len(products)
    in_stock_count = sum(1 for p in products if p["in_stock"])
    out_of_stock_count = total_products - in_stock_count
    categories = set(p["category"] for p in products)

    return {
        "store_name": "My E-commerce Store",
        "total_products": total_products,
        "in_stock": in_stock_count,
        "out_of_stock": out_of_stock_count,
        "categories": list(categories)
    }

#----------End point 6----------------search products by name----------------------
@app.get("/products/search/{keyword}")
def search_products_by_name(keyword: str):
    result = [p for p in products if keyword.lower() in p["name"].lower()]

    if not result:
        return {"message": f"No products matching '{keyword}' found"}
    
    return {"search_keyword": keyword,
            "matching_products": result,
            "total": len(result)}

#----------End point 7----------------filter products by price range----------------------
@app.get("/products/deals")
def get_deals():
    cheapest = min(products, key=lambda p: p["price"])
    expensive = max(products, key=lambda p: p["price"])

    return {"Best deal": cheapest, 
            "premium_pick": expensive}

#------------------End point 8----------------get only price of products----------------------
@app.get("/products/{product_id}/price")
def get_product_price(product_id: int):
    for product in products:
        if product['id'] == product_id:
            return {"product_id": product['name'],
                    "price": product['price']}
    return {"error": "Product not found"}

#-----------------End point 9----------------Accept Customer Feedback----------------------
@app.post("/feedback")
def submit_feedback(data: CustomerFeedback):
    feedback.append(data.model_dump())

    return {"message": "Thank you for your feedback!",
            "feedback": data.model_dump(),
            "total_feedback": len(feedback)}

#-----------------End point 10----------------get product summary----------------------
@app.get("/products/summary")
def get_product_summary():
    total_products = len(products)
    in_stock_count = sum(1 for p in products if p["in_stock"])
    out_of_stock_count = total_products - in_stock_count
    most_expensive = max(products, key=lambda p: p["price"])
    cheapest = min(products, key=lambda p: p["price"])
    categories = set(p["category"] for p in products)
    
    return {
        "total_products": total_products,
        "in_stock": in_stock_count,
        "out_of_stock": out_of_stock_count,
        "most_expensive": {"name": most_expensive["name"], "price": most_expensive["price"]},
        "cheapest": {"name": cheapest["name"], "price": cheapest["price"]},
        "categories": list(categories)
    }

#-----------------End point 11----------------Validate and place bulk orders----------------------
@app.post("/orders")
def place_bulk_order(order: BulkOrder):
    pending, failed, grand_total = [],[], 0
    for item in order.items:
        product = next((p for p in products if p["id"] == item.product_id), None)
        
        if not product:
            failed.append({
                "product_id": item.product_id,
                "reason": "Product not found"
            })
            continue
        if not product["in_stock"]:
            failed.append({
                "product_id": item.product_id,
                "reason": "Product not in stock"
            })
            continue
        
        sub_total = product["price"] * item.quantity
        grand_total += sub_total

        pending.append({
            "product_id": item.product_id,
            "quantity": item.quantity,
            "sub_total": sub_total
        })
    order_id = len(orders) + 1
    new_order = {
        "order_id": order_id,
        "company": order.company_name,
        "products_ordered": pending,
        "failed": failed,
        "grand_total": grand_total,
        "status": "pending"
    }
    orders.append(new_order)
    return {"new_order": new_order, "total_orders": len(orders) }

@app.get("/orders/{order_id}")
def get_order_status(order_id: int):
    for order in orders:
        if order["order_id"] == order_id:
            return {"order": order}
    return {"error": "Order not found"}

@app.patch("/orders/{order_id}/confirm")
def confirm_order(order_id: int):
    for order in orders:
        if order["order_id"] == order_id:
            order["status"] = "Confirmed"
            return {"message": "Order confirmed", 
                    "order": order}
    return {"error": "Order not found"}

#----------End point----------------get product by id----------------------
@app.get("/products/{product_id}")       #products / route url
def get_product_by_id(product_id: int):
    for product in products:
        if product['id'] == product_id:
            return {"product": product}
    return {"error": "Product not found"}