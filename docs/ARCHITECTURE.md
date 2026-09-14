# Architecture & Workflow Documentation

This document describes the architectural layers, system components, data models, purchase flow, and authentication strategy for the **FreshMart Grocery Store** platform.

---

## 1. System Component & Layer Diagram

```mermaid
graph TD
    subgraph Client ["Client Layer"]
        Browser["Web Browser (UI)"]
        APIClient["REST / API Client (Mobile/Postman)"]
    end

    subgraph App ["Flask Application Layer"]
        subgraph Blueprints ["Blueprints & Routing"]
            main_bp["main_bp<br/>(Web Pages & Navigation)"]
            auth_bp["auth_bp<br/>(/api/auth - Login, Register, JWT)"]
            products_bp["products_bp<br/>(/api/products - Catalog CRUD)"]
            cart_bp["cart_bp<br/>(/api/cart - Cart Management)"]
            orders_bp["orders_bp<br/>(/api/orders - Checkout & Inventory)"]
            stripe_bp["stripe_bp<br/>(/api/payments - Stripe & Webhooks)"]
            admin_bp["admin_bp<br/>(/admin & /api/admin - Operations & Analytics)"]
        end

        subgraph Extensions ["Flask Extensions & Services"]
            jwt_mgr["Flask-JWT-Extended<br/>(Cookie & Bearer Auth)"]
            limiter["Flask-Limiter<br/>(Rate Limiting)"]
            db_ext["Flask-SQLAlchemy<br/>(ORM & Data Access)"]
            email_svc["services/email.py<br/>(Async Receipts & PDF Invoices)"]
        end
    end

    subgraph Data ["Persistence Layer"]
        Postgres[("PostgreSQL / SQLite Database")]
    end

    subgraph External ["External Services"]
        StripeAPI["Stripe API & Checkout"]
        MailServer["SMTP / SendGrid Email Server"]
    end

    %% Client Connections
    Browser -->|HTTP GET/POST + Cookies| main_bp
    Browser -->|AJAX JSON + Bearer/Cookies| auth_bp
    Browser -->|AJAX JSON + Bearer/Cookies| products_bp
    Browser -->|AJAX JSON + Bearer/Cookies| cart_bp
    Browser -->|AJAX JSON + Bearer/Cookies| orders_bp
    Browser -->|AJAX JSON + Bearer/Cookies| admin_bp
    APIClient -->|JSON REST + Bearer Token| auth_bp
    APIClient -->|JSON REST + Bearer Token| products_bp
    APIClient -->|JSON REST + Bearer Token| cart_bp
    APIClient -->|JSON REST + Bearer Token| orders_bp

    %% Blueprint Internal Connections
    auth_bp --> jwt_mgr
    auth_bp --> limiter
    auth_bp --> db_ext
    products_bp --> db_ext
    cart_bp --> db_ext
    orders_bp --> db_ext
    admin_bp --> db_ext
    stripe_bp --> StripeAPI
    stripe_bp --> db_ext
    stripe_bp --> email_svc
    email_svc --> MailServer

    %% Data Connections
    db_ext --> Postgres

    %% External Webhooks
    StripeAPI -->|Webhook Event: checkout.session.completed| stripe_bp
```

---

## 2. Purchase Flow Sequence Diagram

The end-to-end purchasing workflow from product selection to Stripe checkout and automated invoice fulfillment:

```mermaid
sequenceDiagram
    autonumber
    actor User as Customer (Browser)
    participant Auth as Auth API
    participant Products as Products API
    participant Cart as Cart API
    participant Orders as Orders API
    participant Stripe as Stripe Gateway
    participant Webhook as Stripe Webhook
    participant Email as Email Service
    participant DB as Database

    User->>Auth: POST /api/auth/login or /register (credentials)
    Auth->>DB: Verify credentials / Create User
    Auth-->>User: 200 OK + JWT (Set HttpOnly Cookie & LocalStorage)

    User->>Products: GET /api/products (filter/search)
    Products->>DB: Query available products with stock > 0
    Products-->>User: 200 OK (Product List JSON)

    User->>Cart: POST /api/cart/add {product_id, quantity}
    Cart->>DB: Check stock & insert/update CartItem
    Cart-->>User: 200 OK {"msg": "Item added to cart"}

    User->>Orders: POST /api/orders/ (Trigger Checkout)
    activate Orders
    Orders->>DB: Fetch cart items, verify stock, decrement inventory
    Orders->>DB: Create Order (status="pending") + OrderItems
    Orders->>DB: Clear CartItems for user
    Orders->>Stripe: Create Stripe Checkout Session
    Stripe-->>Orders: Returns checkout session URL
    Orders-->>User: 201 Created {order_id, checkout_url}
    deactivate Orders

    User->>Stripe: Redirected to Stripe Hosted Checkout
    User->>Stripe: Enters test card & submits payment
    Stripe-->>User: Redirect to /success?session_id=...&order_id=...

    par Asynchronous Webhook
        Stripe->>Webhook: POST /api/payments/webhook (checkout.session.completed)
        activate Webhook
        Webhook->>DB: Verify signature & update Order status = "paid"
        Webhook->>Email: send_order_confirmation_email(order, user)
        activate Email
        Email->>Email: Generate PDF Invoice
        Email->>User: Deliver HTML Email + Attached PDF Invoice
        deactivate Email
        Webhook-->>Stripe: 200 OK {"received": true}
        deactivate Webhook
    end
```

---

## 3. Data Model (Entity-Relationship Diagram)

```mermaid
erDiagram
    USER ||--o{ CART_ITEM : "has many"
    USER ||--o{ ORDERS : "places many"
    PRODUCT ||--o{ CART_ITEM : "referenced in"
    PRODUCT ||--o{ ORDER_ITEM : "referenced in"
    ORDERS ||--|{ ORDER_ITEM : "contains"
    COUPON ||--o{ ORDERS : "applied to"

    USER {
        int id PK
        string email UK "nullable=False"
        string password_hash "nullable=False"
        string name "nullable=True"
        string role "default='customer'"
        datetime created_at
    }

    PRODUCT {
        int id PK
        string name "nullable=False"
        text description "nullable=True"
        numeric price "10,2 - nullable=False"
        string uom "unit, kg, bunch, etc."
        int stock "nullable=False, default=0"
        string category "nullable=True"
        string image_url "nullable=True"
        datetime created_at
    }

    CART_ITEM {
        int id PK
        int user_id FK "nullable=False"
        int product_id FK "nullable=False"
        int quantity "default=1"
        datetime added_at
    }

    ORDERS {
        int id PK
        int user_id FK "nullable=False"
        numeric total_amount "10,2"
        numeric discount_amount "10,2, default=0"
        int coupon_id FK "nullable=True"
        string status "pending, paid, shipped, delivered, cancelled"
        string shipping_address "nullable=True"
        string tracking_number "nullable=True"
        datetime created_at
    }

    ORDER_ITEM {
        int id PK
        int order_id FK "nullable=False"
        int product_id FK "nullable=False"
        numeric price "10,2 snapshot price"
        int quantity "default=1"
    }

    COUPON {
        int id PK
        string code UK "nullable=False"
        numeric discount_percent "5,2 - e.g. 10.00"
        boolean active "default=True"
        datetime expiry_date
        datetime created_at
    }
```

---

## 4. Authentication Strategy (Dual Header + Cookie JWT)

The platform implements a unified authentication architecture using `Flask-JWT-Extended` with dual location verification:

1. **Browser Navigation & Server-Side Rendering**:
   - On `/api/auth/login` and `/api/auth/register`, the response includes an `httpOnly` cookie (`access_token_cookie`) configured with `SameSite=Lax`.
   - When a browser visits protected UI pages (like `/cart`, `/orders`, or `/admin`), Flask inspects the cookie automatically.
   - If the cookie is missing or expired on a web page request, the application gracefully redirects the user to `/login`.

2. **Single-Page App & API Clients**:
   - In addition to cookies, responses return `{ "access_token": "<jwt>" }`.
   - Client-side JavaScript stores the token and includes `Authorization: Bearer <token>` on asynchronous `fetch()` requests.
   - External API consumers (cURL, mobile apps, Postman) authenticate purely via the `Authorization` header.
   - Unauthorized API requests receive a standardized `401 Unauthorized` JSON payload (`{ "msg": "Missing authorization token" }`).

3. **Role-Based Access Control (RBAC)**:
   - User claims include `role: "customer"` or `role: "admin"`.
   - Administrative endpoints (`/admin`, `/api/products` POST/PUT/DELETE, `/api/admin/...`) verify `role == "admin"`, returning `403 Forbidden` if unauthorized.
