# FreshMart Grocery Store Platform 🛒

A full-stack, production-ready e-commerce grocery store web application built with **Flask**, **SQLAlchemy**, **PostgreSQL / SQLite**, **Flask-JWT-Extended**, and **Stripe Checkout**.

---

## 🌟 Key Features

- **Modern Web Storefront**: Responsive catalog with real-time search, category filtering, product inventory badges, and AJAX shopping cart.
- **Unified Dual Authentication**: Seamless JWT authentication supporting both browser cookies (`httpOnly`) and API client `Authorization: Bearer <token>` headers.
- **Shopping Cart & Checkout**: Interactive cart with quantity controls, subtotal calculation, inventory stock validation, and promotional coupon codes.
- **Stripe Payment Gateway**: Secure hosted Stripe Checkout sessions with asynchronous webhook fulfillment on `checkout.session.completed`.
- **Automated Invoicing & Emails**: Itemized HTML order confirmation emails with auto-generated PDF invoices delivered via asynchronous background workers.
- **Admin Operations Dashboard**: Role-protected management portal (`/admin`) for tracking order statuses (`pending` &rarr; `paid` &rarr; `shipped` &rarr; `delivered`), inventory levels, low-stock warnings, and revenue analytics.
- **Smart Recommendations**: "Customers also bought" co-occurrence queries highlighting related products during checkout.
- **Zero-Config Local Dev**: Defaults to SQLite with zero setup required, while fully production-ready with PostgreSQL via Docker or environment variables.
- **Comprehensive Automated Tests**: Full pytest test suite with in-memory SQLite defaults covering authentication, products, cart operations, and orders.

---

## 🏛️ System Architecture

For in-depth architectural diagrams, purchase sequence flows, and data model entity-relationship diagrams, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

```
                      +-------------------+
                      |   Client Layer    |
                      | (Browser / REST)  |
                      +---------+---------+
                                |
               +----------------v----------------+
               |      Flask Application          |
               |                                 |
               |  +---------------------------+  |
               |  |  main_bp: UI Pages        |  |
               |  |  auth_bp: JWT Auth        |  |
               |  |  products_bp: Catalog     |  |
               |  |  cart_bp: Cart Ops        |  |
               |  |  orders_bp: Checkout      |  |
               |  |  admin_bp: Analytics      |  |
               |  |  stripe_bp: Webhooks      |  |
               |  +---------------------------+  |
               +--------+--------------+---------+
                        |              |
              +---------v---+    +-----v---------+
              | PostgreSQL  |    |  Stripe API   |
              | / SQLite DB |    | & SMTP Server |
              +-------------+    +---------------+
```

---

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.11 or 3.12
- Git

### 2. Clone and Setup
```bash
# Clone the repository
git clone https://github.com/Katakam-Krupavathi/Grocery_Store.git
cd Grocery_Store

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration
Create a `.env` file based on `.env.example`:
```bash
cp .env.example .env
```

| Variable | Default (Local) | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///dev.db` | Connection URI (PostgreSQL or SQLite) |
| `SECRET_KEY` | `change-me` | Flask session secret key |
| `JWT_SECRET_KEY` | `change-me-jwt` | Secret key used for signing JWTs |
| `STRIPE_SECRET_KEY` | - | Stripe API Secret Key (`sk_test_...`) |
| `STRIPE_WEBHOOK_SECRET` | - | Stripe Webhook Secret (`whsec_...`) |
| `MAIL_SERVER` | `smtp.sendgrid.net` | SMTP host for sending invoice emails |

### 4. Database Setup & Initial Admin
```bash
# Run migrations
flask db upgrade

# Create the default administrator account
python create_admin.py
```

### 5. Run Development Server
```bash
python run.py
```
Open [http://localhost:8000](http://localhost:8000) in your browser.

---

## 🧪 Running Automated Tests

Run the full pytest suite:
```bash
pytest -v
```

---

## 🐳 Running with Docker

```bash
docker-compose up --build
```

---

## 📜 License

This project is licensed under the [MIT License](LICENSE) - see the LICENSE file for details.
