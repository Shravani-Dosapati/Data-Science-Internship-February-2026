from fastapi import FastAPI,Response, status, Query, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional

app = FastAPI()

products = [
    {'id': 1, 'name': 'Wireless Mouse', 'price': 499, 'category': 'Electronics', 'in_stock': True},
    {'id': 2, 'name': 'Notebook',       'price':  99, 'category': 'Stationery',  'in_stock': True},
    {'id': 3, 'name': 'USB Hub',        'price': 799, 'category': 'Electronics', 'in_stock': False},
    {'id': 4, 'name': 'Pen Set',        'price':  49, 'category': 'Stationery',  'in_stock': True},
]

feedback = []
orders = []
order_counter = 1
cart = []

class NewProduct(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    price: int = Field(..., gt=0)
    category: str = Field(..., min_length=2, max_length=50)
    in_stock: bool = Field(...)

class CustomerFeedback(BaseModel):
    customer_name: str = Field(..., min_length=2, max_length=100)
    product_id: int = Field(..., gt=0)
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=500)

class OrderItem(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0, le=50)

class BulkOrder(BaseModel):
    customer_name: str = Field(..., min_length=2)
    contact_email: str = Field(None, min_length=5)
    items: List[OrderItem] = Field(..., min_items=1)

class CheckoutRequest(BaseModel):
    customer_name: str = Field(..., min_length=2)
    delivery_address: str = Field(..., min_length=5)

#----------End point 0----------------home page----------------------
@app.get("/")       #Home / route url
def home():
    return {"message": "Welcome to our app"}

#----------End point----------------get products in stock----------------------
@app.get("/products/instock")       #products / route url
def get_products_in_stock():
    product_instock = [p for p in products if p["in_stock"] == True]

    if not product_instock:
        return {"message": "No Products in stock"}
    
    return {"Products_in_stock": product_instock, 
            "count": len(product_instock)}

#----------End point----------------store info----------------------
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

#----------End point----------------search products by name----------------------
@app.get("/products/search/{keyword}")
def search_products_by_name(keyword: str):
    result = [p for p in products if keyword.lower() in p["name"].lower()]

    if not result:
        return {"message": f"No products matching '{keyword}' found"}
    
    return {"search_keyword": keyword,
            "matching_products": result,
            "total": len(result)}

#----------End point----------------filter products by price range----------------------
@app.get("/products/deals")
def get_deals():
    cheapest = min(products, key=lambda p: p["price"])
    expensive = max(products, key=lambda p: p["price"])

    return {"Best deal": cheapest, 
            "premium_pick": expensive}

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
        "customer_name": order.customer_name,
        "products_ordered": pending,
        "failed": failed,
        "grand_total": grand_total,
        "status": "pending"
    }
    orders.append(new_order)
    return {"new_order": new_order, "total_orders": len(orders) }

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

# --- DAY 5 - Cart system

def find_product(product_id: int):
    for product in products:
        if product["id"] == product_id:
            return product
    return None

def calculate_total(product, quantity):
    return product["price"] * quantity 

@app.post('/cart/add')
def add_to_cart(
    product_id: int = Query(..., description='Product ID to add'),
    quantity: int = Query(1, description='How many (default 1)'),
):  
    # Q3: Handle 404 for missing products
    product = find_product(product_id)
    if not product:
        raise HTTPException(status_code=404, 
                            detail=f"Product with ID {product_id} not found" )
    
    # Q3: Handle 400 for out-of-stock products
    if not product['in_stock']:
        raise HTTPException(status_code=400, 
                            detail=f"{product['name']} is out of stock" )
        
    if quantity < 1:
        raise HTTPException( status_code=400, 
                            detail='Quantity must be at least 1' )
    
    # Q4: Already in cart — update quantity
    for item in cart:
        if item['product_id'] == product_id:
            item['quantity'] += quantity
            item['subtotal'] = calculate_total(product, item['quantity'])
            return {'message': 'Cart updated', 'cart_item': item}
            
    # New item
    cart_item = {
        'product_id': product_id,
        'product_name': product['name'],
        'quantity': quantity,
        'unit_price': product['price'],
        'subtotal': calculate_total(product, quantity)
    }
    cart.append(cart_item)
    return {'message': 'Added to cart', 'cart_item': cart_item}

#-------------------------End Point----------------------View cart----------------------
@app.get('/cart')
def view_cart():

    # Q5: Return cart is empty
    if not cart:
        return {'message': 'Cart is empty'}
    
    # Q2: Calculate grand total and item count
    total_amount = sum(item['subtotal'] for item in cart)
    return {'items': cart, 
            'item_count': len(cart),
            'grand_total': total_amount}

#-------------------------End Point----------------------Remove from cart----------------------
@app.delete('/cart/{product_id}')
def remove_from_cart(product_id: int):
    for index, item in enumerate(cart):
        if item['product_id'] == product_id:
            removed_item = cart.pop(index)
            return {'message': f"Removed {removed_item['product_name']} from cart"}
    
    raise HTTPException(status_code=404, 
                        detail='Product not found in cart')

#-------------------------End Point----------------------Checkout----------------------
@app.post('/cart/checkout')
def checkout(checkout_request: CheckoutRequest, Response: Response):

    global order_counter
    # BONUS: Empty cart validation using HTTPException
    if not cart:
        raise HTTPException(status_code=400, 
                            detail='Cart is empty')
    
    order_summary = []
    grand_total = 0

    for item in cart:
        order = {
            'order_id': order_counter,
            'customer_name': checkout_request.customer_name,  
            'product_id': item['product_id'],
            'quantity': item['quantity'],
            'total_price': item['subtotal'],
            'delivery_address': checkout_request.delivery_address,
            'total_amount': item['subtotal'],
            'status': 'Confirmed'
        }
        orders.append(order)
        order_summary.append(order)
        grand_total += item['subtotal']
        order_counter += 1

    cart.clear()  
    Response.status_code = status.HTTP_201_CREATED

    return {
        'message': 'Order placed successfully',
        'order_summary': order_summary,
        'grand_total': grand_total
    }

#-------------------------End Point----------------------Get orders list--------------------
@app.get('/orders')
def get_orders():
    return {'orders': orders, 
            'total_orders': len(orders)}


#-------------------------End Point----------------------Search Products----------------------
@app.get('/products/search')
def search_products(keyword: str):
    matching_products = [p for p in products if keyword.lower() in p['name'].lower()]

    if not matching_products:
        return {'message': f"No products found matching '{keyword}'"}
    
    return {'search_keyword': keyword,
            'matching_products': [p['name'] for p in matching_products], 
            'total_matches': len(matching_products)}

#-------------------------End Point----------------------Sort Products----------------------
@app.get('/products/sort')
def sort_products(sort_by: str = Query("price"),
                  order: str = Query("asc")):
    
    if sort_by not in ["price", "name"]:
        raise HTTPException(status_code=400, detail="sort_by must be 'price' or 'name'")

    elif order not in ["asc", "desc"]:
        raise HTTPException(status_code=400, detail="order must be 'asc' or 'desc'")
    
    reverse = (order == "desc")
    sort_products = sorted(products, key=lambda p: p[sort_by], reverse=reverse)

    return {'sort_by': sort_by,
            'order': order,
            'products': sort_products}

#-------------------------End Point----------------------Pagination----------------------
@app.get('/products/page')
def paginate_products(page: int = Query(1, ge=1, description="Page number"), 
                      limit: int = Query(2, ge=1, le=100, description="items per page")):
    
    start = (page - 1) * limit                  
    end = start + limit
    paginated = products[start:end] 

    if not paginated:
        return {'message': 'No products found for this page'}
    
    return {
        'page': page,
        'limit': limit,
        'total': len(products),
        'total_products': len(products),
        'products': paginated
    }   

#-------------------------End Point----------------------Searching Order list----------------------
@app.get('/orders/search')
def search_orders(customer_name: str = Query(..., description="Search by customer name")):
    matching_orders = [order for order in orders if customer_name.lower() in order['customer_name'].lower()]

    if not matching_orders:
        return {'message': f"No orders found for customer '{customer_name}'"}
    
    return {'customer_name': customer_name,
            'total_orders': len(matching_orders),
            'Orders': matching_orders,}

#-------------------------End Point----------------------Sort by Category then price----------------------
@app.get('/products/sort-by-category')
def sort_by_Category():
    sorted_products = sorted(products, key=lambda p: (p['category'], p['price']))
    return {'products': sorted_products}

#-------------------------End Point----------------------paginate orders----------------------
@app.get('/orders/paginate')
def paginate_orders(page: int = Query(1, ge=1, description="Page number"),
                    limit: int = Query(3, ge=1, le=100, description="Orders per page")):
    
    start = (page - 1) * limit                  
    end = start + limit
    paginated_orders = orders[start:end] 

    if not paginated_orders:
        return {'message': 'No orders found for this page'}
    
    return {
        'page': page,
        'limit': limit,
        'total_orders': len(orders),
        'orders': paginated_orders
    }

#-------------------------End Point----------------------Products Browse----------------------
@app.get('/products/browse')
def browse_products(
    keyword: str = Query(None),
    sort_by: str = Query('price'),
    order: str = Query('asc'),
    page: int = Query(1, ge=1),
    limit: int = Query(4, ge=1, le=20)
):
    # 1) Start with all products
    results = products

    # 2) Filter by keyword (if provided)
    if keyword:
        results = [p for p in results if keyword.lower() in p['name'].lower()]

    # 3) Validate sort_by and order
    if sort_by not in ["price", "name"]:
        raise HTTPException(status_code=400, detail="Invalid sort_by parameter")
    if order not in ["asc", "desc"]:
        raise HTTPException(status_code=400, detail="Invalid order parameter")

    # 4) Sort (use results, not result)
    results = sorted(results, key=lambda p: p[sort_by], reverse=(order == 'desc'))

    # 5) Paginate
    total = len(results)
    start = (page - 1) * limit
    end = start + limit
    paged = results[start:end]

    return {
        'keyword': keyword,
        'sort_by': sort_by,
        'order': order,
        'page': page,
        'limit': limit,
        'total_found': total,
        'total_pages': (total + limit - 1) // limit,
        'products': paged}




@app.get("/orders/{order_id}")
def get_order_status(order_id: int):
    for order in orders:
        if order["order_id"] == order_id:
            return {"order": order}
    return {"error": "Order not found"}

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
#-------------------------End Point----------------------Get single product----------------------
@app.get("/products/{product_id}")
def get_product(product_id: int, response: Response):
    index = find_product_index(product_id)
    if index is None:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"error": "Product not found"}
    return products[index]
