# FreshMart Grocery Store 🛒

[![CI](https://github.com/Katakam-Krupavathi/Grocery_Store/actions/workflows/ci.yml/badge.svg)](https://github.com/Katakam-Krupavathi/Grocery_Store/actions/workflows/ci.yml)
[![Python Version](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/framework-Flask%203.x-green.svg)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-31%20passed-brightgreen.svg)](tests/)

FreshMart is a full-stack, production-ready e-commerce grocery web application built with **Flask**, **SQLAlchemy**, **PostgreSQL / SQLite**, **Flask-JWT-Extended**, **Stripe Checkout**, and **ReportLab**.

---

## 📑 Table of Contents

- [Key Features](#-key-features)
- [System Architecture](#-system-architecture)
- [Project Layout](#-project-layout)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Environment Variables](#environment-variables)
  - [Database Initialization](#database-initialization)
  - [Running the Application](#running-the-application)
- [API Reference](#-api-reference)
- [Automated Testing](#-automated-testing)
- [Docker Deployment](#-docker-deployment)
- [License](#-license)

---

## 🌟 Key Features

### 🛍️ Customer Storefront & Catalog
- **Interactive Catalog**: Real-time product search, category filtering, and stock availability indicators (`In Stock`, `Low Stock`, `Out of Stock`).
- **Smart Recommendations**: "Customers Also Bought" suggestions powered by SQL co-occurrence queries over historical order data.
- **Cart & Discounts**: Dynamic cart with real-time quantity adjustments, subtotal calculation, and promo code support (e.g., `SUMMER15`).

### 🔐 Unified Dual-Mode Authentication
- **Seamless Navigation**: Supports `httpOnly` JWT cookies for server-rendered web pages and standard `Authorization: Bearer <token>` headers for REST API clients.
- **Rate-Limited Security**: Protected with **Flask-Limiter** against brute-force attacks on login (10/min) and registration (5/min).

### 💳 Stripe Checkout & Invoicing
- **Hosted Checkout**: Frictionless Stripe Checkout integration with automated webhook handling (`checkout.session.completed`).
- **PDF Invoice Generation**: Auto-generates branded PDF invoices via **ReportLab** and delivers them attached to order confirmation emails.
- **Visual Order Tracker**: 4-stage tracking timeline (`Order Placed` &rarr; `Payment Confirmed` &rarr; `Shipped` &rarr; `Delivered`).

### 📊 Admin Operations & Analytics
- **Operations Portal (`/admin`)**: Role-protected dashboard for managing orders, updating delivery statuses, and monitoring inventory levels.
- **Live Analytics (`/admin/analytics`)**: Interactive **Chart.js** visualizations for revenue trends, order status distribution, and top-selling products.

---

## 🏛️ System Architecture

For comprehensive architecture diagrams, purchase flow sequences, and data models, please see **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)**.

```
+-------------------------------------------------------------------------+
|                              CLIENT LAYER                               |
|       Web Browser (SSR / AJAX)      |     REST API / Mobile Clients     |
+-------------------------------------+-----------------------------------+
                                      |
+-------------------------------------v-----------------------------------+
|                        FLASK APPLICATION LAYER                          |
|                                                                         |
|  [main_bp]      Pages: /, /products, /cart, /orders, /login, /register  |
|  [auth_bp]      Auth: /api/auth (Login, Register, JWT, Me)              |
|  [products_bp]  Catalog: /api/products (CRUD, Search, Recommendations)  |
|  [cart_bp]      Cart: /api/cart (Add, Update, Remove, Apply Coupon)     |
|  [orders_bp]    Orders: /api/orders (Checkout, History, Details)        |
|  [admin_bp]     Admin: /admin, /api/admin (Stats, Status, Coupons)      |
|  [stripe_bp]    Payments: /api/payments (Checkout Sessions, Webhook)    |
+-------------------------------------+-----------------------------------+
                                      |
+-------------------------------------v-----------------------------------+
|                           SERVICES & DATA                               |
|   PostgreSQL / SQLite (SQLAlchemy)  |   Stripe API & SMTP Mail Server   |
+-------------------------------------------------------------------------+
```

---

## 📂 Project Layout

```text
Grocery_Store/
├── app/
│   ├── admin/             # Admin portal and analytics routes
│   ├── auth/              # Authentication & JWT endpoints
│   ├── cart/              # Shopping cart & coupon handlers
│   ├── main/              # Customer-facing web page routes
│   ├── orders/            # Order processing & checkout logic
│   ├── payments/          # Stripe checkout & webhook listener
│   ├── products/          # Catalog management & recommendations
│   ├── services/          # Email dispatch & ReportLab PDF generator
│   ├── templates/         # Jinja2 HTML templates & Admin UI
│   ├── config.py          # Unified application configuration
│   ├── extensions.py      # SQLAlchemy, JWT, Mail, Limiter instances
│   ├── models.py          # Database models (User, Product, Order, etc.)
│   └── __init__.py        # App factory & blueprint registration
├── docs/
│   └── ARCHITECTURE.md    # Architecture & workflow documentation
├── migrations/            # Alembic database migration scripts
├── tests/                 # Full automated test suite (31 tests)
├── .env.example           # Template for environment variables
├── .github/workflows/     # GitHub Actions Continuous Integration
├── Dockerfile             # Container definition
├── docker-compose.yml     # Multi-container setup with PostgreSQL
├── requirements.txt       # Project dependencies
├── run.py                 # Application entry point
└── LICENSE                # MIT License
```

---

## 🚀 Getting Started

### Prerequisites
- **Python**: `3.11` or `3.12`
- **Git**

### Installation
```bash
# 1. Clone the repository
git clone https://github.com/Katakam-Krupavathi/Grocery_Store.git
cd Grocery_Store

# 2. Create and activate a virtual environment
python -m venv .venv
# On macOS/Linux:
source .venv/bin/activate
# On Windows (PowerShell):
.venv\Scripts\Activate.ps1

# 3. Install required dependencies
pip install -r requirements.txt
```

### Environment Variables
Copy `.env.example` to `.env` and adjust settings as needed:
```bash
cp .env.example .env
```

| Variable | Default (Local) | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///dev.db` | Database connection URI (SQLite or PostgreSQL) |
| `SECRET_KEY` | `change-me-secret` | Flask session secret key |
| `JWT_SECRET_KEY` | `change-me-jwt` | Secret key used for signing JWT tokens |
| `STRIPE_SECRET_KEY` | `sk_test_...` | Stripe secret API key |
| `STRIPE_WEBHOOK_SECRET` | `whsec_...` | Stripe webhook signing secret |
| `MAIL_SERVER` | `smtp.sendgrid.net` | SMTP host for delivering PDF invoices |
| `MAIL_PORT` | `587` | SMTP port |
| `MAIL_USERNAME` | `apikey` | SMTP username |
| `MAIL_PASSWORD` | `your_api_key` | SMTP password / API token |

### Database Initialization
```bash
# Apply database schema migrations
flask db upgrade

# Seed default administrator account (admin@example.com / admin123)
python create_admin.py
```

### Running the Application
```bash
python run.py
```
Open [http://localhost:8000](http://localhost:8000) in your web browser.

---

## 📡 API Reference

### Authentication (`/api/auth`)
| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `POST` | `/api/auth/register` | Register new user account | Public (Rate-limited) |
| `POST` | `/api/auth/login` | Authenticate and obtain JWT | Public (Rate-limited) |
| `POST` | `/api/auth/logout` | Clear auth cookies and logout | Public |
| `GET` | `/api/auth/me` | Fetch authenticated user profile | Required |

### Products Catalog (`/api/products`)
| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `GET` | `/api/products/` | List products (with `q`, `category`, `page`) | Public |
| `GET` | `/api/products/<id>` | Get product details | Public |
| `GET` | `/api/products/<id>/recommendations` | Get "Customers Also Bought" items | Public |
| `POST` | `/api/products/` | Create new product | Admin |
| `PUT` | `/api/products/<id>` | Update product details or stock | Admin |
| `DELETE` | `/api/products/<id>` | Remove product from catalog | Admin |

### Shopping Cart (`/api/cart`)
| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `GET` | `/api/cart/` | View current user's cart items & total | Required |
| `POST` | `/api/cart/add` | Add product to cart | Required |
| `POST` | `/api/cart/apply-coupon` | Validate promo code & calculate discount | Required |
| `PUT` | `/api/cart/update/<id>` | Update item quantity | Required |
| `DELETE` | `/api/cart/remove/<id>` | Remove single item from cart | Required |
| `DELETE` | `/api/cart/clear` | Empty cart | Required |

### Orders & Checkout (`/api/orders`)
| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `POST` | `/api/orders/` | Place order & generate Stripe checkout URL | Required |
| `GET` | `/api/orders/` | List order history | Required |
| `GET` | `/api/orders/<id>` | Fetch specific order details & items | Required |

### Administration (`/api/admin`)
| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `GET` | `/api/admin/stats` | KPI counters & sales breakdown | Admin |
| `PUT` | `/api/admin/orders/<id>/status` | Update order status (`paid`, `shipped`, etc.) | Admin |
| `POST` | `/api/admin/coupons` | Create a new promotional discount code | Admin |

---

## 🧪 Automated Testing

The project includes **31 automated tests** running on an in-memory SQLite database (`sqlite:///:memory:`) by default.

```bash
# Run all test suites
pytest -v
```

### GitHub Actions CI
On every push and pull request, `.github/workflows/ci.yml` runs tests in parallel across:
- **Python 3.11** with in-memory SQLite & PostgreSQL 15
- **Python 3.12** with in-memory SQLite & PostgreSQL 15

---

## 🐳 Docker Deployment

Run the complete platform and PostgreSQL database with Docker Compose:

```bash
docker-compose up --build
```

---

## 📜 License

This project is licensed under the [MIT License](LICENSE) - see the LICENSE file for details.

Developed with ❤️ by **Katakam-Krupavathi**.
