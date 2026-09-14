def test_admin_stats_as_admin(client, admin_headers):
    res = client.get("/api/admin/stats", headers=admin_headers)
    assert res.status_code == 200
    data = res.get_json()
    assert "total_revenue" in data
    assert "total_orders" in data
    assert "status_breakdown" in data

def test_admin_stats_forbidden_for_customer(client, auth_headers):
    res = client.get("/api/admin/stats", headers=auth_headers)
    assert res.status_code == 403

def test_admin_update_order_status(client, admin_headers, auth_headers):
    # 1. Customer creates product & order
    p_res = client.post("/api/products/", headers=admin_headers, json={
        "name": "Organic Honey",
        "price": 10.00,
        "stock": 20
    })
    product_id = p_res.get_json()["product"]["id"]

    client.post("/api/cart/add", headers=auth_headers, json={"product_id": product_id, "quantity": 1})
    order_res = client.post("/api/orders/", headers=auth_headers)
    order_id = order_res.get_json()["order"]["order_id"]

    # 2. Admin updates status to shipped
    update_res = client.put(f"/api/admin/orders/{order_id}/status", headers=admin_headers, json={
        "status": "shipped",
        "tracking_number": "TRK-987654"
    })
    assert update_res.status_code == 200
    assert update_res.get_json()["order"]["status"] == "shipped"

def test_admin_create_coupon(client, admin_headers):
    res = client.post("/api/admin/coupons", headers=admin_headers, json={
        "code": "FLASH50",
        "discount_percent": 50.0
    })
    assert res.status_code == 201
    assert res.get_json()["coupon"]["code"] == "FLASH50"
