from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity,
    get_jwt,
    set_access_cookies,
    unset_jwt_cookies
)
from ..extensions import db, limiter
from ..models import User

auth_bp = Blueprint("auth", __name__)

def _get_request_data():
    if request.is_json:
        return request.get_json(silent=True) or {}
    return request.form.to_dict() or {}

@auth_bp.route("/register", methods=["POST"])
@limiter.limit("5 per minute")
def register():
    data = _get_request_data()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password")
    name = (data.get("name") or "").strip()

    if not email or not password:
        return jsonify({"msg": "Email and password are required"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"msg": "User with this email already exists"}), 400

    user = User(email=email, name=name or email.split("@")[0])
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={"role": user.role, "email": user.email, "name": user.name}
    )

    resp = jsonify({
        "msg": "Registered successfully",
        "access_token": access_token,
        "user": user.to_dict()
    })
    set_access_cookies(resp, access_token)
    return resp, 201

@auth_bp.route("/login", methods=["POST"])
@limiter.limit("10 per minute")
def login():
    data = _get_request_data()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password")

    if not email or not password:
        return jsonify({"msg": "Email and password are required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"msg": "Invalid email or password"}), 401

    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={"role": user.role, "email": user.email, "name": user.name}
    )

    resp = jsonify({
        "msg": "Login successful",
        "access_token": access_token,
        "user": user.to_dict()
    })
    set_access_cookies(resp, access_token)
    return resp, 200

@auth_bp.route("/logout", methods=["POST", "GET"])
def logout():
    resp = jsonify({"msg": "Logged out successfully"})
    unset_jwt_cookies(resp)
    return resp, 200

@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def get_me():
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"msg": "User not found"}), 404
    return jsonify({"user": user.to_dict()}), 200
