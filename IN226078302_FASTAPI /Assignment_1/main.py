from unicodedata import category

from fastapi import FastAPI, Query
app = FastAPI()     # app is a variable or object of fastapi class

products = [
    {"id": 1, "name": "Wireless Mouse", "price": 499, "category": "Electronics", "in_stock": True},
    {"id": 2, "name": "Notebook",        "price": 99, "category": "Stationery", "in_stock": True},
    {"id": 3, "name": "USB Hub",        "price": 799, "category": "Electronics", "in_stock": False},
    {"id": 4, "name": "Pen Set",         "price": 49, "category": "Stationery", "in_stock": True},

    #Q1: ADD 3 PRODUCTS IN THE PRODUCTS LIST
    {"id":5, "name": "Laptop Stand", "price": 1299, "category": "Electronics", "in_stock": True},
    {"id":6, "name": "Mechanical Keyboard", "price": 2499, "category": "Electronics", "in_stock": True},
    {"id":7, "name": "Webcam", "price": 1899, "category": "Electronics", "in_stock": False}
]

#----------End point 0----------------home page----------------------
@app.get("/")       #Home / route url
def home():
    return {"message": "Welcome to our app"}

#----------End point 1----------------get all products----------------------
@app.get("/products")       #products / route url
def get_products():
    return {'products': products, 'total': len(products)}

#Q2: Create an endpoint to get products by category.
#----------End point 3----------------get products by category----------------------
@app.get("/products/category/{category_name}")       #products / route url
def get_products_by_category(category_name: str):
    result = [p for p in products if p['category'].lower() == category_name.lower()]

    if not result:
        return {"message": f"No products found in category '{category_name}'"}
    
    return {"Category":category_name,
            "products": result,
            "total": len(result)}

#Q3: Create an endpoint to get products that are in stock.
#----------End point 4----------------get products in stock----------------------
@app.get("/products/instock")       #products / route url
def get_products_in_stock():
    product_instock = [p for p in products if p["in_stock"] == True]

    if not product_instock:
        return {"message": "No Products in stock"}
    
    return {"Products_in_stock": product_instock, 
            "count": len(product_instock)}


#Q4: Create a get to Build a store info endpoint.
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

#Q5: Create a get to Search products by name endpoint.
#----------End point 6----------------search products by name----------------------
@app.get("/products/search/{keyword}")
def search_products_by_name(keyword: str):
    result = [p for p in products if keyword.lower() in p["name"].lower()]

    if not result:
        return {"message": f"No products matching '{keyword}' found"}
    
    return {"search_keyword": keyword,
            "matching_products": result,
            "total": len(result)}

#6Q Bonus: Create a get to filter products by price range endpoint.
#----------End point 7----------------filter products by price range----------------------
@app.get("/products/deals")
def get_deals():
    cheapest = min(products, key=lambda p: p["price"])
    expensive = max(products, key=lambda p: p["price"])

    return {"Best deal": cheapest, 
            "premium_pick": expensive}

#----------End point----------------get product by id----------------------
@app.get("/products/{product_id}")       #products / route url
def get_product_by_id(product_id: int):
    for product in products:
        if product['id'] == product_id:
            return {"product": product}
    return {"error": "Product not found"}