def test_products_smoke(client):
    res = client.get("/api/products")
    assert res.status_code in (200, 404)
