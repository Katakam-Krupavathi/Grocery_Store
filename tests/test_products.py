def test_create_product_as_admin(client, admin_headers):
    res = client.post("/api/products/", headers=admin_headers, json={
        "name": "Fresh Organic Apples",
        "description": "Crisp and juicy Honeycrisp apples",
        "price": 3.99,
        "stock": 50,
        "uom": "kg",
        "category": "Fruits"
    })
    assert res.status_code == 201
    data = res.get_json()
    assert data["product"]["name"] == "Fresh Organic Apples"
    assert data["product"]["stock"] == 50

def test_create_product_forbidden_for_customer(client, auth_headers):
    res = client.post("/api/products/", headers=auth_headers, json={
        "name": "Hacked Product",
        "price": 0.01,
        "stock": 100
    })
    assert res.status_code == 403

def test_list_products(client, admin_headers):
    # Create test product
    client.post("/api/products/", headers=admin_headers, json={
        "name": "Bananas",
        "price": 1.29,
        "stock": 100,
        "category": "Fruits"
    })
    
    res = client.get("/api/products/")
    assert res.status_code == 200
    data = res.get_json()
    assert len(data["products"]) > 0

def test_search_and_filter_products(client, admin_headers):
    client.post("/api/products/", headers=admin_headers, json={
        "name": "Whole Milk",
        "price": 4.50,
        "stock": 20,
        "category": "Dairy"
    })

    # Search by name
    res = client.get("/api/products/?q=Milk")
    assert res.status_code == 200
    data = res.get_json()
    assert any(p["name"] == "Whole Milk" for p in data["products"])

    # Filter by category
    res = client.get("/api/products/?category=Dairy")
    assert res.status_code == 200
    data = res.get_json()
    assert all(p["category"] == "Dairy" for p in data["products"])

def test_update_product_as_admin(client, admin_headers):
    res_create = client.post("/api/products/", headers=admin_headers, json={
        "name": "Old Bread",
        "price": 2.00,
        "stock": 10,
        "category": "Bakery"
    })
    product_id = res_create.get_json()["product"]["id"]

    res_update = client.put(f"/api/products/{product_id}", headers=admin_headers, json={
        "name": "Fresh Artisanal Bread",
        "price": 3.50,
        "stock": 25
    })
    assert res_update.status_code == 200
    updated = res_update.get_json()["product"]
    assert updated["name"] == "Fresh Artisanal Bread"
    assert updated["price"] == 3.50
    assert updated["stock"] == 25

def test_delete_product_as_admin(client, admin_headers):
    res_create = client.post("/api/products/", headers=admin_headers, json={
        "name": "Temporary Product",
        "price": 5.00,
        "stock": 5
    })
    product_id = res_create.get_json()["product"]["id"]

    res_del = client.delete(f"/api/products/{product_id}", headers=admin_headers)
    assert res_del.status_code == 200

    # Verify not found
    res_get = client.get(f"/api/products/{product_id}")
    assert res_get.status_code == 404
