import os
from dotenv import load_dotenv
from flask import Flask, request, redirect, url_for, jsonify, render_template
from flask_login import LoginManager, UserMixin, login_required, current_user, login_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import CheckConstraint
from sqlalchemy.exc import IntegrityError
from flask_migrate import Migrate

from validators import parse_inventory_payload

load_dotenv()
app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Models
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)  
    username = db.Column(db.String(20), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(
            password,
            method="pbkdf2:sha256",
            salt_length=16
)
    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

class Inventory(db.Model):
    __table_args__ = (
        CheckConstraint('length(trim("itemName")) > 0', name="ck_inventory_itemname_not_empty"),
    )  
    id = db.Column(db.Integer, primary_key=True)
    userID = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    itemName = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    restockmin = db.Column(db.Integer)
    restockmax = db.Column(db.Integer)
    description = db.Column(db.Text)
    category = db.Column(db.String(50))

class SharedInventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ownersID = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    sharedID = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    permissionLevel = db.Column(db.String(20), nullable=False)



@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

#Routes
@app.route("/register", methods=["GET", "POST"])
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
                return redirect(url_for("login"))

    return render_template("register.html", error=error), 400 if error else 200

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("inventory_page"))
        
        error = "Incorrect Password or Username. Try Again."


    return render_template("login.html", error = error)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route("/")
def home():
    return redirect(url_for("login"))

    

@app.route("/api/me")
@login_required
def whoami():
    return jsonify({"username": current_user.username}), 200

@app.route("/add_row", methods=["POST"])
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


@app.route("/getUserInventory", methods=["GET"])
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

@app.route("/inventory")
@login_required
def inventory_page():
    return render_template("index.html", username=current_user.username)

@app.route("/edit_row", methods=["PUT"])
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


@app.route("/sharedinv")
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

@app.route("/share_inv", methods=["POST"])
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


@app.route("/edit_shared_row", methods=["PUT"])
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


if __name__ == "__main__":
    app.run(debug=True)