from fastapi import FastAPI,Response, status, Query, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

app = FastAPI()

products = [
    {'id': 1, 'name': 'Wireless Mouse', 'price': 499, 'category': 'Electronics', 'in_stock': True},
    {'id': 2, 'name': 'Notebook',       'price':  99, 'category': 'Stationery',  'in_stock': True},
    {'id': 3, 'name': 'USB Hub',        'price': 799, 'category': 'Electronics', 'in_stock': False},
    {'id': 4, 'name': 'Pen Set',        'price':  49, 'category': 'Stationery',  'in_stock': True},
]

class NewProduct(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    price: int = Field(..., gt=0)
    category: str = Field(..., min_length=2, max_length=50)
    in_stock: bool
    
#----------End point 0----------------home page----------------------
@app.get("/")       #Home / route url
def home():
    return {"message": "Welcome to our app"}

@app.get("/products")
def get_all_products():
    return {'products': products, 'total': len(products)}

@app.get("/products/filter")
def filter_products(category: str = Query(None, description="Filter by category"), 
                    min_price: int = Query(None, description="Minimum price"), 
                    max_price: int = Query(None, description="Maximum price"),
                    in_stock: bool = Query(None, description="Filter by stock status")):
    
    filtered = products
    if category:
        filtered = [p for p in filtered if p['category'].lower() == category.lower()]
    if min_price is not None:
        filtered = [p for p in filtered if p['price'] >= min_price]
    if max_price is not None:
        filtered = [p for p in filtered if p['price'] <= max_price]
    if not filtered:
        raise HTTPException(status_code=404, detail="No products found matching the criteria")
    return {'products': filtered, 'total': len(filtered)}


#-------------------------End Point----------------------Product audit----------------------
@app.get("/products/audit")
def product_audit():

    in_stock_list = [p for p in products if p['in_stock']]
    out_of_stock_list = [p for p in products if not p['in_stock']]

    stock_summary = sum(p['price'] * 10 for p in in_stock_list)

    expensive = max(products, key=lambda p: p['price'])

    return {
        "total_products": len(products),
        "in_stock_count": len(in_stock_list),
        "out_of_stock_names": [p['name'] for p in out_of_stock_list],
        "total_stock_value": stock_summary,
        "most_expensive": {
            "name": expensive['name'],
            "price": expensive['price']
        }
    }    

#-------------------------End Point----------------------Apply discount----------------------
@app.put("/products/discount_percent")
def apply_discount(
    category: str = Query(...),
    discount: int = Query(..., ge=1, le=99)):

    updated_products = []

    for product in products:
        if product["category"].lower() == category.lower():

            product["price"] = int(product["price"] * (1 - discount / 100))

            updated_products.append({
                "name": product["name"],
                "price": product["price"]})

    if not updated_products:
        return {"message": f"No products found in category '{category}'"}

    return {
        "message": f"{discount}% discount applied to {category}",
        "updated_count": len(updated_products),
        "updated_products": updated_products}

#-------------------------Q1 End Point----------------------Add new product----------------------
@app.post("/products")
def add_product(data: NewProduct, response: Response):
    # Check for duplicate name
    for p in products:
        if p['name'].lower() == data.name.lower():
            raise HTTPException(status_code=400, detail="Product with this name already exists")
    
    new_id = max(p['id'] for p in products) + 1 if products else 1
    new_product = {
        'id': new_id,
        'name': data.name,
        'price': data.price,
        'category': data.category,
        'in_stock': data.in_stock
    }
    products.append(new_product)
    response.status_code = status.HTTP_201_CREATED
    return {"message": "Product added",
            "product": new_product}

def find_product_index(product_id: int):
    for index, product in enumerate(products):
        if product['id'] == product_id:
            return index
    return None

#-------------------------End Point----------------------Update product----------------------
@app.put("/products/{product_id}")
def update_product(product_id: int, 
                   price: int = Query(None), 
                   in_stock: bool = Query(None),
                   response: Response = None):
    index = find_product_index(product_id)
    if index is None:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"error": "Product not found"}
    
    if price is not None:
        products[index]['price'] = price

    if in_stock is not None:
        products[index]['in_stock'] = in_stock

    if response:
        response.status_code = status.HTTP_200_OK
    return products[index]

#-------------------------End Point----------------------Delete product----------------------
@app.delete("/products/{product_id}")
def delete_product(product_id: int, 
                   response: Response):
    
    index = find_product_index(product_id)

    if index is None:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"error": "Product not found"}
    
    deleted_product = products.pop(index)
    return {"message": f"Product {deleted_product['name']} deleted"}

#-------------------------End Point----------------------Get single product----------------------
@app.get("/products/{product_id}")
def get_product(product_id: int, response: Response):
    index = find_product_index(product_id)
    if index is None:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"error": "Product not found"}
    return products[index]