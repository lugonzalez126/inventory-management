from flask import request, redirect, url_for, jsonify, render_template, Blueprint
from flask_login import login_required, current_user, login_user, logout_user
from sqlalchemy.exc import IntegrityError
from app import db, limiter
from app.models import User, Inventory, SharedInventory

from app.validators import parse_inventory_payload

main = Blueprint("main", __name__)

#Routes
@main.route("/register", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def register():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            error = "Username and password are required."
        elif len(password) < 6:
            error = "Password must be at least 6 characters."
        else:
            existing = User.query.filter_by(username=username).first()
            if existing:
                error = "Username already exists. Try another."
            else:
                u = User(username=username)
                u.set_password(password)
                db.session.add(u)
                db.session.commit()
                return redirect(url_for("main.login"))

    return render_template("register.html", error=error), 400 if error else 200

@main.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("main.inventory_page"))
        
        error = "Incorrect Password or Username. Try Again."


    return render_template("login.html", error = error)

@main.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.login"))

@main.route("/")
def home():
    return redirect(url_for("main.login"))

    

@main.route("/api/me")
@login_required
def whoami():
    return jsonify({"username": current_user.username}), 200

@main.route("/add_row", methods=["POST"])
@login_required
def add_row():
    payload = request.get_json() or {}

    try:
        data = parse_inventory_payload(payload)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    item = Inventory(
        userID=current_user.id,
        itemName=data["itemName"],
        quantity=data["quantity"],
        restockmin=data["restockmin"],
        description=data["description"]
    )

    db.session.add(item)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Invalid data"}), 400

    return jsonify({"status": "ok", "id": item.id}), 201


@main.route("/getUserInventory", methods=["GET"])
@login_required
def get_user_inventory():
    items = Inventory.query.filter_by(userID=current_user.id).all()

    inventory_list = []
    for item in items:
        inventory_list.append({
            "id": item.id,
            "itemName": item.itemName,
            "quantity": item.quantity,
            "restockmin": item.restockmin,
            "description": item.description
        })

    return jsonify({"user_inventory": inventory_list}), 200

@main.route("/inventory")
@login_required
def inventory_page():
    return render_template("index.html", username=current_user.username)

@main.route("/edit_row", methods=["PUT"])
@login_required
def edit_row():
    payload = request.get_json() or {}

    try:
        data = parse_inventory_payload(payload)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    item_id_raw = payload.get("itemid")
    try:
        item_id = int(item_id_raw)
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid item id"}), 400

    item = Inventory.query.get(item_id)

    if item is None:
        return jsonify({"error": "Item not found"}), 404

    if item.userID != current_user.id:
        return jsonify({"error": "Forbidden"}), 403

    item.itemName = data["itemName"]
    item.quantity = data["quantity"]
    item.restockmin = data["restockmin"]
    item.description = data["description"]

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Invalid data"}), 400

    return jsonify({"status": "ok"}), 200


@main.route("/sharedinv")
@login_required
def shared_inventory_page():
    currentuserid = current_user.id
    shares = SharedInventory.query.filter_by(sharedID=currentuserid).all()

    shared_inventories_data = {}

    for share in shares:
        owner = User.query.get(share.ownersID)
        if not owner:
            continue

        items = Inventory.query.filter_by(userID=share.ownersID).all()
        shared_inventories_data[owner.username] = items

    return render_template("shared_inventory.html", shared_inventories=shared_inventories_data, username=current_user.username)

@main.route("/share_inv", methods=["POST"])
@login_required
def share_inv():
    payload = request.get_json() or {}
    username_to_share = payload.get("username", "").strip()

    if not username_to_share:
        return jsonify({"error": "Username required"}), 400

    user_to_share = User.query.filter_by(username=username_to_share).first()
    if not user_to_share:
        return jsonify({"error": "User not found"}), 404

    if user_to_share.id == current_user.id:
        return jsonify({"error": "Cannot share with yourself"}), 400

    existing = SharedInventory.query.filter_by(
        ownersID=current_user.id,
        sharedID=user_to_share.id
    ).first()
    if existing:
        return jsonify({"error": "Already shared"}), 400

    newshare = SharedInventory(
        ownersID=current_user.id,
        sharedID=user_to_share.id,
        permissionLevel="Edit"
    )
    db.session.add(newshare)
    db.session.commit()

    return jsonify({"status": "ok"}), 201


@main.route("/edit_shared_row", methods=["PUT"])
@login_required
def edit_shared_row():
    payload = request.get_json() or {}
    try:
        data = parse_inventory_payload(payload)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    
    item_id_raw = (payload.get("itemid"))
    try:
        item_id = int(item_id_raw)
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid item id"}), 400
        

    item = Inventory.query.get(item_id)
    if not item:
        return jsonify({"error": "Item not found"}), 404

    
    if item.userID == current_user.id:
        pass
    else:
        share = SharedInventory.query.filter_by(
            ownersID=item.userID,
            sharedID=current_user.id
        ).first()

        if not share or share.permissionLevel != "Edit":
            return jsonify({"error": "Forbidden"}), 403

        item.itemName = data["itemName"]
        item.quantity = data["quantity"]
        item.restockmin = data["restockmin"]
        item.description = data["description"]

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Invalid data"}), 400
    
    return jsonify({"status": "ok"}), 200
