from flask import Blueprint, render_template, redirect, url_for, request
from flask_jwt_extended import unset_jwt_cookies, verify_jwt_in_request, get_jwt, get_jwt_identity
from ..models import Product, CartItem, Order, User

main_bp = Blueprint("main", __name__)

def _get_current_user_optional():
    try:
        verify_jwt_in_request(optional=True)
        user_id = get_jwt_identity()
        if user_id:
            return User.query.get(int(user_id))
    except Exception:
        pass
    return None

@main_bp.route("/")
def home():
    user = _get_current_user_optional()
    featured_products = Product.query.order_by(Product.id.desc()).limit(4).all()
    return render_template("home.html", user=user, featured_products=featured_products)

@main_bp.route("/login")
def login_page():
    user = _get_current_user_optional()
    if user:
        return redirect(url_for("main.products_page"))
    return render_template("login.html")

@main_bp.route("/register")
def register_page():
    user = _get_current_user_optional()
    if user:
        return redirect(url_for("main.products_page"))
    return render_template("register.html")

@main_bp.route("/products")
def products_page():
    user = _get_current_user_optional()
    q = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    
    query = Product.query
    if q:
        query = query.filter(Product.name.ilike(f"%{q}%") | Product.description.ilike(f"%{q}%"))
    if category and category.lower() != "all":
        query = query.filter(Product.category.ilike(category))

    products = query.order_by(Product.id.desc()).all()
    from ..extensions import db
    categories = [cat[0] for cat in db.session.query(Product.category).distinct().filter(Product.category.isnot(None)).all() if cat[0]]
    
    return render_template("products.html", user=user, products=products, categories=sorted(categories), selected_category=category, search_query=q)

@main_bp.route("/cart")
def cart_page():
    user = _get_current_user_optional()
    if not user:
        return redirect(url_for("main.login_page"))
    
    cart_items = CartItem.query.filter_by(user_id=user.id).all()
    item_list = [item.to_dict() for item in cart_items]
    total_amount = sum(item["subtotal"] for item in item_list)

    return render_template("cart.html", user=user, cart_items=item_list, total_amount=round(total_amount, 2))

@main_bp.route("/orders")
def orders_page():
    user = _get_current_user_optional()
    if not user:
        return redirect(url_for("main.login_page"))
        
    orders = Order.query.filter_by(user_id=user.id).order_by(Order.id.desc()).all()
    return render_template("orders.html", user=user, orders=orders)

@main_bp.route("/orders/<int:order_id>")
def order_detail_page(order_id):
    user = _get_current_user_optional()
    if not user:
        return redirect(url_for("main.login_page"))
        
    order = Order.query.get_or_404(order_id)
    if order.user_id != user.id and user.role != "admin":
        return redirect(url_for("main.orders_page"))
        
    return render_template("order_detail.html", user=user, order=order)

@main_bp.route("/success")
def payment_success():
    user = _get_current_user_optional()
    order_id = request.args.get("order_id")
    session_id = request.args.get("session_id")
    order = Order.query.get(order_id) if order_id else None
    return render_template("success.html", user=user, order=order, session_id=session_id)

@main_bp.route("/cancel")
def payment_cancel():
    user = _get_current_user_optional()
    order_id = request.args.get("order_id")
    order = Order.query.get(order_id) if order_id else None
    return render_template("cancel.html", user=user, order=order)

@main_bp.route("/logout")
def logout():
    resp = redirect(url_for("main.login_page"))
    unset_jwt_cookies(resp)
    return resp
