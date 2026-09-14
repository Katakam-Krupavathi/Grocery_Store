from flask import Blueprint, request, jsonify
from ..extensions import db
from ..models import Product
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask import render_template
import json

products_bp = Blueprint("products", __name__)

@products_bp.route("/", methods=["GET"])
def list_products():
    q = request.args.get("q", "")
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))
    query = Product.query
    if q:
        query = query.filter(Product.name.ilike(f"%{q}%"))
    pagination = query.order_by(Product.id.desc()).paginate(page=page, per_page=per_page, error_out=False)
    items = []
    for p in pagination.items:
        items.append({
            "id": p.id,
            "name": p.name,
            "price": float(p.price),
            "stock": p.stock,
            "uom": p.uom,
            "category": p.category
        })
    return jsonify({
        "products": items,
        "page": pagination.page,
        "pages": pagination.pages,
        "total": pagination.total
    })

@products_bp.route("/", methods=["POST"])
@jwt_required()
def create_product():
    identity = json.loads(get_jwt_identity())  # FIX: decode JSON string
    if identity.get("role") != "admin":
        return jsonify({"msg":"admin required"}), 403
    data = request.get_json() or {}
    p = Product(
        name=data.get("name"),
        description=data.get("description"),
        price=data.get("price", 0),
        uom=data.get("uom"),
        stock=data.get("stock", 0),
        category=data.get("category")
    )
    db.session.add(p)
    db.session.commit()
    return jsonify({"msg":"created","product": {"id": p.id}}), 201

@products_bp.route("/<int:product_id>", methods=["PUT"])
@jwt_required()
def update_product(product_id):
    identity = json.loads(get_jwt_identity())  # FIX: decode JSON string
    if identity.get("role") != "admin":
        return jsonify({"msg":"admin required"}), 403
    p = Product.query.get_or_404(product_id)
    data = request.get_json() or {}
    p.name = data.get("name", p.name)
    p.description = data.get("description", p.description)
    p.price = data.get("price", p.price)
    p.uom = data.get("uom", p.uom)
    p.stock = data.get("stock", p.stock)
    p.category = data.get("category", p.category)
    db.session.commit()
    return jsonify({"msg":"updated"}), 200

@products_bp.route("/view")
def view_products():
    products = Product.query.order_by(Product.id.desc()).all()
    return render_template("products.html", products=products)
