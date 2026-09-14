from flask import Blueprint, request, jsonify
from ..extensions import db
from ..models import User
from flask_jwt_extended import create_access_token
from flask import render_template
import json

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")
    name = data.get("name")
    if not email or not password:
        return jsonify({"msg":"email and password required"}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"msg":"user exists"}), 400
    user = User(email=email, name=name)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    
    # FIX: serialize identity as JSON string
    access = create_access_token(identity=json.dumps({"id": user.id, "role": user.role}))
    
    return jsonify({"access_token": access, "user": {"id": user.id, "email": user.email}}), 201

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"msg":"invalid credentials"}), 401
    
    # FIX: serialize identity as JSON string
    access = create_access_token(identity=json.dumps({"id": user.id, "role": user.role}))
    
    return jsonify({"access_token": access, "user": {"id": user.id, "email": user.email}}), 200


# Render login page
@auth_bp.route("/login_page")
def login_page():
    return render_template("login.html")

# Render register page
@auth_bp.route("/register_page")
def register_page():
    return render_template("register.html")
