def test_add_to_cart_and_view(client, auth_headers, admin_headers):
    # 1. Admin creates product
    p_res = client.post("/api/products/", headers=admin_headers, json={
        "name": "Organic Strawberries",
        "price": 5.99,
        "stock": 15,
        "category": "Fruits"
    })
    product_id = p_res.get_json()["product"]["id"]

    # 2. Customer adds to cart
    add_res = client.post("/api/cart/add", headers=auth_headers, json={
        "product_id": product_id,
        "quantity": 3
    })
    assert add_res.status_code == 200

    # 3. View cart
    cart_res = client.get("/api/cart/", headers=auth_headers)
    assert cart_res.status_code == 200
    cart_data = cart_res.get_json()
    assert len(cart_data["items"]) >= 1
    assert cart_data["total_quantity"] >= 3
    assert cart_data["total_amount"] > 0

def test_add_to_cart_exceeds_stock(client, auth_headers, admin_headers):
    p_res = client.post("/api/products/", headers=admin_headers, json={
        "name": "Rare Truffle",
        "price": 99.99,
        "stock": 2,
        "category": "Gourmet"
    })
    product_id = p_res.get_json()["product"]["id"]

    add_res = client.post("/api/cart/add", headers=auth_headers, json={
        "product_id": product_id,
        "quantity": 5
    })
    assert add_res.status_code == 400
    assert "stock" in add_res.get_json()["msg"]

def test_remove_from_cart(client, auth_headers, admin_headers):
    p_res = client.post("/api/products/", headers=admin_headers, json={
        "name": "Chocolate Bar",
        "price": 2.50,
        "stock": 50
    })
    product_id = p_res.get_json()["product"]["id"]

    # Add to cart
    client.post("/api/cart/add", headers=auth_headers, json={
        "product_id": product_id,
        "quantity": 1
    })

    cart = client.get("/api/cart/", headers=auth_headers).get_json()
    cart_item = next(item for item in cart["items"] if item["product_id"] == product_id)

    # Remove
    del_res = client.delete(f"/api/cart/remove/{cart_item['cart_item_id']}", headers=auth_headers)
    assert del_res.status_code == 200

def test_create_order_happy_path(client, auth_headers, admin_headers):
    # Clear cart first
    client.delete("/api/cart/clear", headers=auth_headers)

    p_res = client.post("/api/products/", headers=admin_headers, json={
        "name": "Fresh Orange Juice",
        "price": 4.00,
        "stock": 10,
        "category": "Beverages"
    })
    product_id = p_res.get_json()["product"]["id"]

    # Add 2 items
    client.post("/api/cart/add", headers=auth_headers, json={
        "product_id": product_id,
        "quantity": 2
    })

    # Place order
    order_res = client.post("/api/orders/", headers=auth_headers)
    assert order_res.status_code == 201
    order_data = order_res.get_json()
    assert order_data["order"]["total_amount"] == 8.00
    assert order_data["order"]["status"] == "pending"
    assert "checkout_url" in order_data
    order_id = order_data["order"]["order_id"]

    # Verify cart is empty now
    cart_res = client.get("/api/cart/", headers=auth_headers)
    assert len(cart_res.get_json()["items"]) == 0

    # Verify stock deducted
    p_check = client.get(f"/api/products/{product_id}")
    assert p_check.get_json()["product"]["stock"] == 8

    # Get order details
    detail_res = client.get(f"/api/orders/{order_id}", headers=auth_headers)
    assert detail_res.status_code == 200
    assert detail_res.get_json()["order"]["order_id"] == order_id

def test_create_order_empty_cart(client, auth_headers):
    client.delete("/api/cart/clear", headers=auth_headers)
    res = client.post("/api/orders/", headers=auth_headers)
    assert res.status_code == 400
    assert "empty" in res.get_json()["msg"]
