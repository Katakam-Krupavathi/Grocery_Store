def test_home_page(client):
    res = client.get("/")
    assert res.status_code == 200
    assert b"FreshMart" in res.data

def test_login_page(client):
    res = client.get("/login")
    assert res.status_code == 200
    assert b"Sign In" in res.data

def test_register_page(client):
    res = client.get("/register")
    assert res.status_code == 200
    assert b"Create Account" in res.data

def test_products_page(client):
    res = client.get("/products")
    assert res.status_code == 200
    assert b"Products" in res.data

def test_api_products_smoke(client):
    res = client.get("/api/products/")
    assert res.status_code == 200
    data = res.get_json()
    assert "products" in data
