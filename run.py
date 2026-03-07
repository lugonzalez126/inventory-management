from flask import Flask
from flask_login import LoginManager, UserMixin, login_required, current_user, login_user, logout_user
from flask import render_template
from flask import request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
app = Flask(__name__)
from flask import request, jsonify
from sqlalchemy import CheckConstraint
from sqlalchemy.exc import IntegrityError
from validators import parse_inventory_payload


#1. conifguration boilorplate code
app.config["SECRET_KEY"] = "dev-only-change-later"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///storage.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

#2. Creating user model
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

class User(UserMixin, db.Model):
    #creates a unique Identifier columns
    id = db.Column(db.Integer, primary_key=True)  
    #creates columns username
    username = db.Column(db.String(20), unique=True, nullable=False)
    #create columns of hashed password
    password_hash = db.Column(db.String(255), nullable=False)
    #configured method salts and hashed passowrd to be stored
    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(
            password,
            method="pbkdf2:sha256",
            salt_length=16
)
    # Verify user password using salted hash stored in the database
    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)
    #authenticate user

#4. Create Inventory model
class Inventory(db.Model):
    __table_args__ = (
        CheckConstraint("length(trim(itemName)) > 0", name="ck_inventory_itemname_not_empty"),
    )  
    id = db.Column(db.Integer, primary_key=True)
    userID = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    itemName = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    restockmin = db.Column(db.Integer)
    restockmax = db.Column(db.Integer)
    description = db.Column(db.Text)
#5. a
class SharedInventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ownersID = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    sharedID = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    permissionLevel = db.Column(db.String(20), nullable=False)



@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

#3. added routes to login, logout, register
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if not username or not password:
            return "Username and Password Required", 400
        
        existing = User.query.filter_by(username=username).first()
        if existing:
            return "Username already exists", 400
        
        u = User(username=username)
        u.set_password(password)
        db.session.add(u)
        db.session.commit()
        return redirect(url_for("login"))

    return render_template("register.html")
#5. add routes for basic functionlaity
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("inventory_page"))

        return "Invalid credentials", 401

    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route("/")
def home():
    return "Inventory app running"
    

@app.route("/whoami")
@login_required
def whoami():
    return f"Logged in as: {current_user.username}"

#7. adding payloads     
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
            "restock": item.restockmin,
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

#5.inventory
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

    return render_template("shared_inventory.html", shared_inventories=shared_inventories_data)
#6 share invenotry
@app.route("/share_inv", methods=["POST"])
@login_required
def share_inv():
    data = request.get_json()
    username_to_share = (data or "").strip()

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

#6b edit shared inv
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

    # If owner → allow
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
    with app.app_context():
        db.create_all()
    app.run(debug=True)