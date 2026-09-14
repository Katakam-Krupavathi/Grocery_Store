from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from flask_jwt_extended import jwt_required, get_jwt, verify_jwt_in_request, get_jwt_identity
from sqlalchemy import func
from ..extensions import db
from ..models import User, Product, Order, OrderItem, Coupon

admin_bp = Blueprint("admin", __name__)

def _require_admin():
    try:
        verify_jwt_in_request()
        claims = get_jwt()
        if claims.get("role") == "admin":
            user_id = int(get_jwt_identity())
            return db.session.get(User, user_id)
    except Exception:
        pass
    return None

@admin_bp.route("/admin")
def admin_dashboard():
    admin = _require_admin()
    if not admin:
        return redirect(url_for("main.login_page"))

    orders = Order.query.order_by(Order.id.desc()).all()
    products = Product.query.order_by(Product.stock.asc()).all()
    low_stock = [p for p in products if p.stock < 10]
    coupons = Coupon.query.order_by(Coupon.id.desc()).all()
    total_revenue = sum(float(o.total_amount or 0) for o in orders if o.status == "paid")
    total_customers = User.query.filter_by(role="customer").count()

    return render_template(
        "admin/dashboard.html",
        user=admin,
        orders=orders,
        products=products,
        low_stock=low_stock,
        coupons=coupons,
        total_revenue=round(total_revenue, 2),
        total_orders=len(orders),
        total_customers=total_customers
    )

@admin_bp.route("/admin/analytics")
def admin_analytics_page():
    admin = _require_admin()
    if not admin:
        return redirect(url_for("main.login_page"))

    return render_template("admin/analytics.html", user=admin)

@admin_bp.route("/api/admin/stats", methods=["GET"])
@jwt_required()
def admin_stats_api():
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"msg": "Admin access required"}), 403

    orders = Order.query.all()
    paid_orders = [o for o in orders if o.status == "paid"]
    total_revenue = sum(float(o.total_amount or 0) for o in paid_orders)
    total_orders = len(orders)
    total_users = User.query.count()
    low_stock_count = Product.query.filter(Product.stock < 10).count()

    # Top selling products
    top_products_raw = db.session.query(
        OrderItem.product_id,
        func.sum(OrderItem.quantity).label("total_sold")
    ).group_by(OrderItem.product_id).order_by(func.sum(OrderItem.quantity).desc()).limit(5).all()

    top_products = []
    for pid, sold in top_products_raw:
        prod = db.session.get(Product, pid)
        top_products.append({
            "product_id": pid,
            "name": prod.name if prod else f"Product #{pid}",
            "units_sold": int(sold)
        })

    # Order status breakdown
    status_counts = {}
    for o in orders:
        status_counts[o.status] = status_counts.get(o.status, 0) + 1

    return jsonify({
        "total_revenue": round(total_revenue, 2),
        "total_orders": total_orders,
        "total_users": total_users,
        "low_stock_count": low_stock_count,
        "top_products": top_products,
        "status_breakdown": status_counts
    }), 200

@admin_bp.route("/api/admin/orders/<int:order_id>/status", methods=["PUT", "POST"])
@jwt_required()
def update_order_status(order_id):
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"msg": "Admin access required"}), 403

    order = db.session.get(Order, order_id)
    if not order:
        return jsonify({"msg": "Order not found"}), 404

    data = request.get_json(silent=True) or request.form.to_dict() or {}
    new_status = (data.get("status") or "").strip().lower()

    valid_statuses = ["pending", "paid", "shipped", "delivered", "cancelled"]
    if new_status not in valid_statuses:
        return jsonify({"msg": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"}), 400

    order.status = new_status
    if "tracking_number" in data:
        order.tracking_number = data["tracking_number"]

    db.session.commit()
    return jsonify({"msg": f"Order #{order.id} status updated to {new_status}", "order": order.to_dict()}), 200

@admin_bp.route("/api/admin/coupons", methods=["POST"])
@jwt_required()
def create_coupon():
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"msg": "Admin access required"}), 403

    data = request.get_json(silent=True) or request.form.to_dict() or {}
    code = (data.get("code") or "").strip().upper()
    if not code:
        return jsonify({"msg": "Coupon code is required"}), 400

    try:
        discount = float(data.get("discount_percent", 10.0))
    except (ValueError, TypeError):
        return jsonify({"msg": "Invalid discount percentage"}), 400

    if Coupon.query.filter_by(code=code).first():
        return jsonify({"msg": "Coupon code already exists"}), 400

    coupon = Coupon(code=code, discount_percent=discount, active=True)
    db.session.add(coupon)
    db.session.commit()
    return jsonify({"msg": "Coupon created successfully", "coupon": coupon.to_dict()}), 201
