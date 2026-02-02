from flask import Flask
from flask_login import LoginManager, UserMixin, login_required, current_user, login_user, logout_user
from flask import render_template
from flask import request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
app = Flask(__name__)

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
    id = db.Column(db.Integer, primary_key=True)
    userID = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    itemName = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    restockmin = db.Column(db.Integer)
    restockmax = db.Column(db.Integer)

    description = db.Column(db.Text)

 


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

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("whoami"))

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
           

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)