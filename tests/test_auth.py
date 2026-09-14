import json

def test_register_success(client):
    res = client.post("/api/auth/register", json={
        "name": "Alice Smith",
        "email": "alice@example.com",
        "password": "securepassword123"
    })
    assert res.status_code == 201
    data = res.get_json()
    assert "access_token" in data
    assert data["user"]["email"] == "alice@example.com"
    assert data["user"]["name"] == "Alice Smith"

def test_register_duplicate_email(client):
    # First registration
    client.post("/api/auth/register", json={
        "name": "Bob",
        "email": "bob@example.com",
        "password": "password123"
    })
    # Second registration with same email
    res = client.post("/api/auth/register", json={
        "name": "Bob Duplicate",
        "email": "bob@example.com",
        "password": "password456"
    })
    assert res.status_code == 400
    data = res.get_json()
    assert "already exists" in data["msg"]

def test_register_missing_fields(client):
    res = client.post("/api/auth/register", json={
        "email": "incomplete@example.com"
    })
    assert res.status_code == 400

def test_login_success(client):
    # Register first
    client.post("/api/auth/register", json={
        "name": "Charlie",
        "email": "charlie@example.com",
        "password": "charliepass123"
    })
    
    # Login
    res = client.post("/api/auth/login", json={
        "email": "charlie@example.com",
        "password": "charliepass123"
    })
    assert res.status_code == 200
    data = res.get_json()
    assert "access_token" in data
    assert data["user"]["email"] == "charlie@example.com"

def test_login_invalid_credentials(client):
    res = client.post("/api/auth/login", json={
        "email": "nonexistent@example.com",
        "password": "wrongpassword"
    })
    assert res.status_code == 401

def test_get_me_authenticated(client, auth_headers):
    res = client.get("/api/auth/me", headers=auth_headers)
    assert res.status_code == 200
    data = res.get_json()
    assert data["user"]["email"] == "customer@example.com"

def test_get_me_unauthorized(client):
    res = client.get("/api/auth/me")
    assert res.status_code == 401

def test_logout(client):
    res = client.post("/api/auth/logout")
    assert res.status_code == 200
