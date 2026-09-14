def test_apply_coupon_flow(client, auth_headers, admin_headers):
    # 1. Admin creates coupon
    admin_res = client.post("/api/admin/coupons", headers=admin_headers, json={
        "code": "SUMMER15",
        "discount_percent": 15.0
    })
    assert admin_res.status_code == 201

    # 2. User checks coupon validity
    check_res = client.post("/api/cart/apply-coupon", headers=auth_headers, json={
        "code": "SUMMER15"
    })
    assert check_res.status_code == 200
    assert check_res.get_json()["coupon"]["discount_percent"] == 15.0

    # 3. Create order with coupon
    p_res = client.post("/api/products/", headers=admin_headers, json={
        "name": "Watermelon",
        "price": 20.00,
        "stock": 5
    })
    product_id = p_res.get_json()["product"]["id"]

    client.delete("/api/cart/clear", headers=auth_headers)
    client.post("/api/cart/add", headers=auth_headers, json={"product_id": product_id, "quantity": 1})

    order_res = client.post("/api/orders/", headers=auth_headers, json={"coupon_code": "SUMMER15"})
    assert order_res.status_code == 201
    order_data = order_res.get_json()["order"]
    assert order_data["discount_amount"] == 3.00  # 15% of 20
    assert order_data["total_amount"] == 17.00    # 20 - 3

def test_product_recommendations_endpoint(client, admin_headers):
    p1 = client.post("/api/products/", headers=admin_headers, json={"name": "Pasta", "price": 2.0, "stock": 50, "category": "Pantry"}).get_json()["product"]["id"]
    p2 = client.post("/api/products/", headers=admin_headers, json={"name": "Tomato Sauce", "price": 3.0, "stock": 50, "category": "Pantry"}).get_json()["product"]["id"]

    res = client.get(f"/api/products/{p1}/recommendations")
    assert res.status_code == 200
    data = res.get_json()
    assert "recommendations" in data
