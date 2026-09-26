import jwt
from bson import ObjectId
from flask import Blueprint, g, jsonify, request
from pymongo.errors import DuplicateKeyError
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import mongo
from app.services.rate_limiter import rate_limit
from app.utils.security import create_token, decode_token, generate_api_key, login_required, utcnow
from app.utils.serializers import user_json
from app.utils.validators import password_problem, valid_email

bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def _tokens(user):
    return {
        "access_token": create_token(user["_id"], "access"),
        "refresh_token": create_token(user["_id"], "refresh"),
        "user": user_json(user),
    }


@bp.post("/signup")
@rate_limit("RATE_LIMIT_AUTH", scope="auth")
def signup():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if len(name) < 2:
        return jsonify(error="Please enter your name"), 400
    if not valid_email(email):
        return jsonify(error="Please enter a valid email"), 400
    problem = password_problem(password)
    if problem:
        return jsonify(error=problem), 400

    user = {
        "name": name[:60],
        "email": email,
        "password_hash": generate_password_hash(password),
        "created_at": utcnow(),
    }
    try:
        user["_id"] = mongo.users.insert_one(user).inserted_id
    except DuplicateKeyError:
        return jsonify(error="An account with this email already exists"), 409
    return jsonify(_tokens(user)), 201


@bp.post("/login")
@rate_limit("RATE_LIMIT_AUTH", scope="auth")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    user = mongo.users.find_one({"email": email})
    if not user or not check_password_hash(user["password_hash"], data.get("password") or ""):
        return jsonify(error="Incorrect email or password"), 401
    mongo.users.update_one({"_id": user["_id"]}, {"$set": {"last_login_at": utcnow()}})
    return jsonify(_tokens(user))


@bp.post("/refresh")
def refresh():
    token = (request.get_json(silent=True) or {}).get("refresh_token")
    if not token:
        return jsonify(error="refresh_token is required"), 400
    try:
        payload = decode_token(token, expected="refresh")
    except jwt.InvalidTokenError:
        return jsonify(error="Please log in again"), 401
    user = mongo.users.find_one({"_id": ObjectId(payload["sub"])})
    if not user:
        return jsonify(error="Please log in again"), 401
    return jsonify(access_token=create_token(user["_id"], "access"))


@bp.get("/me")
@login_required
def me():
    return jsonify(user=user_json(g.user))


@bp.patch("/me")
@login_required
def update_me():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if len(name) < 2:
        return jsonify(error="Name is too short"), 400
    mongo.users.update_one({"_id": g.user["_id"]}, {"$set": {"name": name[:60]}})
    return jsonify(user=user_json(mongo.users.find_one({"_id": g.user["_id"]})))


@bp.post("/change-password")
@login_required
def change_password():
    data = request.get_json(silent=True) or {}
    if not check_password_hash(g.user["password_hash"], data.get("current_password") or ""):
        return jsonify(error="Current password is wrong"), 400
    problem = password_problem(data.get("new_password"))
    if problem:
        return jsonify(error=problem), 400
    mongo.users.update_one(
        {"_id": g.user["_id"]}, {"$set": {"password_hash": generate_password_hash(data["new_password"])}}
    )
    return jsonify(message="Password updated")


@bp.post("/api-key")
@login_required
def rotate_api_key():
    key = generate_api_key()
    mongo.users.update_one({"_id": g.user["_id"]}, {"$set": {"api_key": key}})
    # shown once, like GitHub tokens
    return jsonify(api_key=key)


@bp.delete("/api-key")
@login_required
def revoke_api_key():
    mongo.users.update_one({"_id": g.user["_id"]}, {"$unset": {"api_key": ""}})
    return jsonify(message="API key revoked")


@bp.delete("/me")
@login_required
def delete_account():
    uid = g.user["_id"]
    mongo.clicks.delete_many({"owner_id": uid})
    mongo.links.delete_many({"owner_id": uid})
    mongo.users.delete_one({"_id": uid})
    return jsonify(message="Account deleted")
